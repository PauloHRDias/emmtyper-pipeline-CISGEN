# Arquitetura da vigilância genômica — CIGenS/SC

Este documento descreve o fluxo de vigilância genômica de *Streptococcus
pyogenes* implementado neste repositório e a sua articulação com o pré-projeto
do TCC. O objetivo é processar isolados invasivos de *S. pyogenes* obtidos de
sítios estéreis, produzindo tipagem *emm*, perfil de virulência e relatórios
consolidados para apoio à vigilância epidemiológica no Estado de Santa Catarina.

## Visão geral do fluxo

```
Amostra clínica invasiva
        │
        ▼
Sequenciamento (MinION / Rapid Barcoding)
        │
        ▼
Montagem e anotação (a montante deste repositório)
Dorado → Flye → Medaka → QUAST/NanoPlot → Prokka
        │
        ▼
Assembly .fna  ──────────────────────────────┐
        │                                     │
        ▼                                     ▼
QC de montagem                        Tipagem emm (emmtyper)
(contigs, tamanho, N50, GC, Ns)       workflow BLAST (padrão)
        │                                     │
        └──────────────┬──────────────────────┘
                       ▼
        Perfil de virulência (blastn × VFDB)
        identidade, cobertura, e-value, classe funcional
                       │
                       ▼
        Consolidação da tabela por amostra
                       │
                       ▼
        Junção de metadados clínico-epidemiológicos
        (data, município, sítio anatômico, desfecho)
                       │
                       ▼
        Laudos individuais (Ollama) + alerta determinístico
                       │
                       ▼
        Relatório do lote
        distribuição emm, virulência, alertas, séries temporal/espacial
```

A montagem e a anotação ocorrem **a montante** deste repositório, conforme a
metodologia do TCC (Dorado, Flye, Medaka, QUAST, NanoPlot e Prokka). O pipeline
começa a partir dos assemblies `.fna` depositados em `entrada/`.

## Etapas e ferramentas

| Etapa | Ferramenta | Entrada | Saída |
|---|---|---|---|
| QC de montagem | `scripts/qc_montagem.py` | `entrada/*.fna` | `resultados_consolidados/qc_montagem.tsv` |
| Tipagem *emm* | `emmtyper` 0.2.0 (BLAST) | assembly `.fna` | `resultados_blast/*_emm.stdout.log` |
| Perfil de virulência | `blastn` × VFDB filtrado | assembly `.fna` | `resultados_consolidados/*_vfdb.tsv` |
| Consolidação | `scripts/consolidar_lote.py` | resultados emm + VFDB | `resultados_consolidados/epibuilder_metadata.tsv` |
| Metadados | `scripts/juntar_metadados.py` | tabela genômica + CSV/TSV + QC | `resultados_consolidados/epibuilder_completo.tsv` |
| Laudos | `scripts/vigilancia_bot.py` + Ollama | tabela genômica | `resultados_consolidados/laudos.txt` |
| Relatório do lote | `scripts/relatorio_lote.py` | tabela final + laudos | `resultados_consolidados/relatorio_lote.md` |

## QC de montagem

O QC calcula, para cada assembly:

- número de contigs;
- comprimento total;
- N50;
- maior e menor contig;
- conteúdo GC;
- quantidade e percentagem de `N`.

Os valores esperados para *S. pyogenes* são usados como referência:

| Métrica | Faixa/limite padrão |
|---|---|
| Comprimento total | 1.500.000–2.500.000 pb |
| Contigs | ≤ 500 |
| Ns | ≤ 1% |
| GC | 35–42% |

O QC **não bloqueia** o pipeline por defeito. Casos críticos (comprimento muito
baixo, excesso de contigs ou de `N`) são marcados como `FALHA`; desvios menores
como `ATENCAO`; o restante como `OK`. O modo `--strict` faz o script terminar
com código 1 quando existe alguma `FALHA`, podendo ser usado em validação.

## Tipagem *emm*

A tipagem usa o `emmtyper` no workflow BLAST contra o banco `emm.fna`. O
resultado bruto do BLAST é preservado em
`resultados_blast/<ID>.blast.raw.tsv` quando disponível. O PCR *in silico* é
opcional (`--pcr`) e serve como método complementar de conferência.

## Perfil de virulência

O `blastn` compara o assembly completo contra o VFDB filtrado para
*S. pyogenes* (`banco_dados/VFDB_S.pyogenes.fas`). A detecção de um gene exige:

- identidade mínima: `VFDB_MIN_PIDENT` (padrão **90%**);
- cobertura do sujeito: `length / slen` (padrão **70%**).

A cobertura é calculada em relação ao gene de referência do VFDB, pois a query
é o genoma completo. Os hits aprovados são consolidados em uma lista de `VFG`
por amostra.

## Classificação das amostras

| Situação | `Tipo_EMM` | Laudo clínico |
|---|---|---|
| *S. pyogenes* confirmado | `EMM<x>` | Sim |
| Espécie diferente de *S. pyogenes* | `NAO_S_PYOGENES` | Não |
| Amostra não processada | `NAO_PROCESSADO` | Não |

Amostras `NAO_S_PYOGENES` são registadas na tabela e no relatório do lote, mas
não recebem laudo clínico nem entram nas agregações de virulência como se fossem
*S. pyogenes*.

## Laudos e alertas

O laudo individual é redigido por um modelo local (`llama3:8b` via Ollama). O
texto é organizado por categorias funcionais do VFDB (adesão, exotoxinas,
modulação imune, enzimas, sobrevivência a stress, fatores nutricionais e
metabólicos), reduzindo o número de genes apresentados ao modelo.

A **classificação de alerta é determinística** e calculada em Python a partir
dos genes detetados; o modelo apenas redige a narrativa. As etiquetas usadas são:

- `[ALERTA VERMELHO]` — presença de fatores de virulência de maior risco;
- `[ALERTA AMARELO]` — perfil intermédio;
- `[PERFIL ENDÉMICO PADRÃO]` — sem marcadores de alerta.

> **Nota:** no painel de validação atual, todas as 12 estirpes de *S. pyogenes*
> possuem pelo menos um superantígeno e recebem `[ALERTA VERMELHO]`. Se o TCC
> definir uma escala de alerta distinta, a regra deve ser ajustada em
> `scripts/vigilancia_bot.py` de forma documentada.

## Metadados clínico-epidemiológicos

Os metadados são fornecidos em CSV ou TSV com uma coluna de identificação
(`ID_Amostra`, `ID`, `Amostra`, `Sample` ou `sample_id`). Colunas recomendadas:

| Coluna | Descrição |
|---|---|
| `ID_Amostra` | Identificador da amostra (igual ao nome do `.fna` sem extensão) |
| `Data_Coleta` | Data de coleta (`AAAA-MM-DD`, `DD/MM/AAAA`, `AAAA-MM` ou `MM/AAAA`) |
| `Municipio` | Município de origem |
| `UF` | Unidade federativa |
| `Sitio_Anatomico` | Sítio anatômico de isolamento |
| `Desfecho` | Desfecho clínico |
| `Idade` | Idade do paciente |
| `Sexo` | Sexo do paciente |

O script `scripts/juntar_metadados.py` acrescenta as colunas de metadados e de
QC à tabela genômica, preservando a tabela genômica como fonte primária. Amostras
sem metadados recebem `NA`; metadados sem assembly correspondente são apenas
reportados no terminal. Um exemplo está em `docs/metadados_exemplo.tsv`.

> **Importante:** dados clínicos reais nunca devem ser versionados no Git. O
> ficheiro real de metadados deve ficar fora do controlo de versão (ver
> `.gitignore`).

## Relatório do lote

O relatório em Markdown resume:

- total de amostras e situação de QC;
- distribuição de tipos *emm*;
- número de genes de virulência por amostra e principais categorias funcionais;
- contagem de alertas nos laudos;
- agregações por mês de coleta, município, sítio anatômico e desfecho, quando
  os metadados estão disponíveis.

## Uso

```bash
# Lote completo: QC + tipagem + VFDB + laudos + relatório
./pipeline_principal.sh

# Sem laudos (mais rápido, útil para testes)
./pipeline_principal.sh --sem-laudos

# Com metadados clínico-epidemiológicos
./pipeline_principal.sh --metadados docs/metadados_exemplo.tsv

# Sem QC ou sem relatório
./pipeline_principal.sh --sem-qc
./pipeline_principal.sh --sem-relatorio

# Apenas uma amostra
./pipeline_principal.sh --amostra entrada/GCF_XXXX.fna
```

## Estrutura de saídas

```
resultados_blast/                  # saídas do emmtyper e BLAST bruto
resultados_pcr/                    # saídas do PCR in silico (opcional)
resultados_consolidados/
  qc_montagem.tsv                  # QC por amostra
  <ID>_vfdb.tsv                    # hits brutos do VFDB
  epibuilder_metadata.tsv          # tabela genômica consolidada
  epibuilder_completo.tsv          # tabela + QC + metadados
  laudos.txt                       # laudos individuais
  relatorio_lote.md                # relatório resumido do lote
logs/                              # stderr de cada etapa
```

## Reprodutibilidade e versionamento

- Os bancos (`emm.fna`, VFDB filtrado e índice BLAST) são insumos locais.
- As saídas em `resultados_*`, `logs/` e os metadados clínicos reais são
  ignorados pelo Git.
- O painel de validação (12 estirpes, 11 tipos *emm*) está documentado em
  `docs/painel_validacao.md`.
- Cada fase do projeto é commitada e enviada para `origin/main`.
