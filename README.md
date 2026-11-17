# Vigilância Genômica de *Streptococcus pyogenes* (CIGenS/SC)

Pipeline reprodutível para **QC de montagem**, **tipagem *emm***, **perfil de virulência (VFDB)**, **laudos epidemiológicos automatizados** e **relatório de lote** de assemblies de *S. pyogenes*.

## O que a pipeline faz

```text
entrada/*.fna
   │
   ├── QC de montagem ────────► qc_montagem.tsv
   ├── emmtyper (BLAST) ──────► tipo emm
   ├── blastn contra VFDB ────► genes de virulência
   └── (opcional) PCR in silico
   │
   ▼
resultados_consolidados/epibuilder_metadata.tsv
   │
   ├── metadados clínico-epidemiológicos (opcional)
   ▼
resultados_consolidados/epibuilder_completo.tsv
   │
   ├── laudos via Ollama (llama3:8b) ──► laudos.txt
   ├── relatório do lote ──────────────► relatorio_lote.md
   └── dashboard HTML ─────────────────► dashboard.html
```

A montagem e a anotação (Dorado → Flye → Medaka → QUAST/NanoPlot → Prokka) ocorrem
**a montante** deste repositório. A visão completa do fluxo de vigilância está em
[`docs/arquitetura_vigilancia.md`](docs/arquitetura_vigilancia.md).

## Requisitos

- **micromamba** em `/resultados/Analises_Paulo/micromamba` com o ambiente `emmtyper`
  (emmtyper 0.2.0, blastn e isPcr).
- **Docker** com o contêiner `ollama` ativo e o modelo `llama3:8b` baixado.
- Assemblies em FASTA (`.fna`) na pasta `entrada/`.

O `config.sh` resolve automaticamente o ambiente e o `PATH`, mesmo em shells não-interativos.
Se necessário, copie `config.example.sh` para `config.sh` e ajuste os caminhos.

## Como rodar

```bash
cd ~/teste_emmtyper

# Lote completo: QC + tipagem + virulência + consolidação + laudos + relatório
./pipeline_principal.sh

# Apenas tipagem/virulência/consolidação (sem laudos)
./pipeline_principal.sh --sem-laudos

# Com metadados clínico-epidemiológicos (CSV ou TSV)
./pipeline_principal.sh --metadados docs/metadados_exemplo.tsv

# Pular QC de montagem, relatório do lote ou dashboard HTML
./pipeline_principal.sh --sem-qc
./pipeline_principal.sh --sem-relatorio
./pipeline_principal.sh --sem-html

# Incluir PCR in silico
./pipeline_principal.sh --pcr

# Processar uma amostra específica
./pipeline_principal.sh --amostra entrada/GCF_000006785.2_ASM678v2_genomic.fna

# Ajuda
./pipeline_principal.sh --help
```

### Teste rápido ao retomar

Se você voltar em outro dia e quiser apenas confirmar que tudo continua funcionando,
rode o lote de validação **sem laudos** (não depende do Ollama). Se estiver em outra
máquina ou clone, rode `git pull` e copie `config.example.sh` para `config.sh`
ajustando os caminhos:

```bash
cd ~/teste_emmtyper
./pipeline_principal.sh --sem-laudos --metadados docs/metadados_exemplo.tsv
```

O teste usa as 30 montagens de `entrada/` e deve terminar com **30/30 amostras
processadas, 0 falhas, QC 30/30 `OK` e 18 tipos emm distintos**. Confira com:

```bash
wc -l resultados_consolidados/epibuilder_completo.tsv
# 31 linhas (cabeçalho + 30 amostras)

tail -n +2 resultados_consolidados/epibuilder_completo.tsv | cut -f2 | sort -u | wc -l
# 18 tipos emm distintos

grep -c "OK" resultados_consolidados/qc_montagem.tsv
# 30
```

Para o teste completo, com laudos:

```bash
docker start ollama   # se o contêiner estiver parado
./pipeline_principal.sh --metadados docs/metadados_exemplo.tsv
```

Os laudos ficam em `resultados_consolidados/laudos.txt` e o resumo em
`resultados_consolidados/relatorio_lote.md`.

### Rodar sem depender da sessão SSH

Para deixar o processamento rodando mesmo se você bloquear a tela ou desconectar:

```bash
setsid nohup ./pipeline_principal.sh > logs/pipeline.log 2>&1 < /dev/null &
```

Ou use `tmux`:

```bash
tmux new -s vigilancia
./pipeline_principal.sh
# Ctrl+B, depois D para sair da sessão
```

Bloquear a tela **não** interrompe processos no servidor. O risco é apenas o encerramento
da sessão SSH; `setsid`/`nohup`/`tmux` protegem contra isso.

## Validação

O painel em `entrada/` contém **30 genomas completos de *S. pyogenes*** com
**18 tipos emm distintos**, selecionados da NCBI Datasets pelo taxon 1314,
nível *Complete Genome* e acessos RefSeq (GCF), sem duplicatas. O resultado
detalhado está em [`docs/painel_validacao.md`](docs/painel_validacao.md).

As cinco amostras de outras espécies usadas inicialmente como controles
negativos foram removidas de `entrada/`.

## Leituras recomendadas

A lista curada de artigos sobre vigilância genômica de *S. pyogenes* e sobre IA/LLMs
em biologia, com referências em ABNT, relevância para o TCC e ordem de leitura, está em
[`docs/referencias_curadas.md`](docs/referencias_curadas.md).

### Documentos do TCC

- [`docs/tcc_revisado.md`](docs/tcc_revisado.md): texto do TCC com as citações e as referências ABNT.
- [`docs/tcc_revisado.html`](docs/tcc_revisado.html): versão formatada para importar no Google Docs ou Word.
- [`docs/referencias_tcc_abnt.md`](docs/referencias_tcc_abnt.md): somente a lista de referências, para colar direto no documento.

## O que cada script faz

| Script | Função |
|---|---|
| `pipeline_principal.sh` | Orquestra o lote: QC → emmtyper → VFDB → consolidação → metadados → laudos → relatório. |
| `scripts/qc_montagem.py` | QC básico de montagem (contigs, tamanho, N50, GC, Ns). |
| `scripts/consolidar_lote.py` | Monta a tabela final com emm e virulência **reais**. |
| `scripts/juntar_metadados.py` | Junta QC e metadados clínico-epidemiológicos por `ID_Amostra`. |
| `scripts/relatorio_lote.py` | Gera o relatório Markdown resumido do lote. |
| `scripts/relatorio_html.py` | Gera o dashboard HTML autocontido (visualização offline). |
| `scripts/preparar_mapa.py` | Prepara o vetor simplificado de SC (execução única). |
| `scripts/preparar_mapa_brasil.py` | Prepara estados + municípios do Brasil para o mapa 3D (execução única). |
| `scripts/prepara_epibuilder.py` | Parsers de emm/VFDB e geração individual da tabela. |
| `scripts/vigilancia_bot.py` | Gera os laudos via Ollama para as amostras de *S. pyogenes*. |
| `scripts/rag_vigilancia.py` | Constrói o dicionário de genes do VFDB (diagnóstico). |
| `scripts/testar_ollama.py` | Testa a conexão e o modelo do Ollama. |

## Estrutura de diretórios

```text
teste_emmtyper/
├── entrada/                     # assemblies .fna
├── banco_dados/
│   ├── VFDB_S.pyogenes.fas
│   ├── vfdb_pyogenes_index.*    # índice BLAST do VFDB
│   ├── sc_municipios.json       # vetor simplificado de SC (legado)
│   └── brasil_geo.json          # estados + municípios do Brasil (mapa 3D)
├── docs/                        # painel de validação, arquitetura e metadados de exemplo
├── scripts/
├── resultados_blast/            # logs do emmtyper e BLAST bruto
├── resultados_pcr/              # saídas do PCR in silico (opcional)
├── resultados_consolidados/     # QC, tabela final, laudos e relatório
├── logs/                        # stderr e logs de execução
├── config.sh                    # configuração local (não versionada)
└── pipeline_principal.sh
```

## Saídas esperadas

- `resultados_consolidados/qc_montagem.tsv` — QC de montagem por amostra.
- `resultados_blast/<ID>_emm.stdout.log` — saída do emmtyper por amostra.
- `resultados_consolidados/<ID>_vfdb.tsv` — hits do blastn contra o VFDB.
- `resultados_consolidados/epibuilder_metadata.tsv` — tabela consolidada:
  `ID_Amostra`, `Tipo_EMM`, `Perfil_Virulencia`.
- `resultados_consolidados/epibuilder_completo.tsv` — tabela + QC + metadados
  (quando `--metadados` é usado).
- `resultados_consolidados/laudos.txt` — laudos gerados pelo Ollama.
- `resultados_consolidados/relatorio_lote.md` — relatório resumido do lote.
- `resultados_consolidados/dashboard.html` — painel interativo para visualização (abrir no navegador).
- `logs/<ID>_*.stderr.log` — erros e avisos por etapa.

## Visualização (dashboard HTML)

O arquivo `resultados_consolidados/dashboard.html` é gerado automaticamente e
contém **CSS e JavaScript embutidos**: funciona offline, sem servidor nem
dependências, e pode ser aberto no navegador ou anexado a um e-mail.

O painel mostra:

- cartões com total de amostras, tipos *emm*, alertas vermelhos e QC aprovado;
- **mapa tático 3D do Brasil** (projeção isométrica, estilo iDroid): os 27
  estados são desenhados com siglas e **pins de todas as amostras** já na visão
  geral. Clicar num estado o destaca, aplica zoom e abre a visão municipal
  daquele estado (5.523 municípios no total), com a mesma extrusão 3D e os pins
  por cidade; o botão **← VOLTAR AO BRASIL** retorna à visão geral.
  O mapa gira **360°** (arraste/slider), tem **zoom** (roda ou botões +/−),
  **RESET**, botão de **tela cheia**, e uma **legenda clicável abaixo do mapa**
  que abre os detalhes da amostra;
- gráficos de distribuição de *emm*, evolução mensal, municípios e categorias
  funcionais do VFDB;
- tabela filtrável (busca livre, *emm*, município e alerta) com exportação TSV;
- ao clicar numa amostra, o laudo completo, as categorias e os genes detectados.

Para atualizar apenas o painel sem reprocessar os genomas:

```bash
source config.sh
"$CONDA_PREFIX/bin/python" scripts/relatorio_html.py
```

O mapa usa `banco_dados/brasil_geo.json` (27 estados e 5.523 municípios
simplificados, ~1,9 MB), gerado uma única vez a partir dos GeoJSONs públicos
[tbrugz/geodata-br](https://github.com/tbrugz/geodata-br) (municípios) e
[brazil-states](https://github.com/codeforgermany/click_that_hood) (estados).
Para atualizar o vetor, coloque `estados.json` e os `mun_<codigo>.json` numa
pasta e rode:

```bash
python3 scripts/preparar_mapa_brasil.py /caminho/da/pasta
```

Escolha de design: o HTML é o formato de baixa fricção para o TCC e as primeiras
demonstrações no SUS. Se houver necessidade de filtros mais elaborados ou de
acesso por múltiplos usuários na rede do laboratório, a evolução natural é um
aplicativo Streamlit lendo as mesmas tabelas — os dados já estão preparados para
isso. A análise de epítopos com o EpiBuilder é separada (ver
[`docs/epibuilder_epitopos.md`](docs/epibuilder_epitopos.md)).

## Metadados clínico-epidemiológicos

Use `--metadados CAMINHO` com um CSV ou TSV que tenha uma coluna de identificação
(`ID_Amostra`, `ID`, `Amostra`, `Sample` ou `sample_id`). Colunas recomendadas:
`Data_Coleta`, `Municipio`, `UF`, `Sitio_Anatomico`, `Desfecho`, `Idade` e `Sexo`.
Um exemplo está em [`docs/metadados_exemplo.tsv`](docs/metadados_exemplo.tsv).

> **Procedência dos dados de exemplo (importante):** os 30 genomas são reais,
> obtidos do NCBI RefSeq, mas **todos os metadados clínicos/epidemiológicos
> (`Municipio`, `Data_Coleta`, `Sitio_Anatomico`, `Desfecho`, `Idade`, `Sexo`)
> são fictícios**, criados apenas para validar a pipeline. Nenhuma amostra real
> de Santa Catarina foi processada até agora. Os laudos e alertas do dashboard
> de demonstração derivam desses metadados sintéticos.

Amostras sem metadados recebem `NA`; metadados sem assembly correspondente são
apenas reportados. **Dados clínicos reais não devem ser versionados** — mantenha-os
fora do repositório (ver `.gitignore`).

## Classificação das amostras

| `Tipo_EMM` | Significado | Recebe laudo? |
|---|---|---|
| `EMM...` | *S. pyogenes* confirmado | Sim |
| `NAO_S_PYOGENES` | Sem gene *emm* e sem genes VFDB de *S. pyogenes* (controle negativo) | Não |
| `NAO_PROCESSADO` | Faltam resultados de tipagem | Não |

## Limiares de virulência

Definidos em `config.sh`:

- `VFDB_MIN_PIDENT=90` — identidade mínima (%).
- `VFDB_MIN_QCOV=70` — cobertura mínima do **gene** (sujeito), calculada como
  `length / slen * 100`.

> O campo `qcovhsp` do BLAST não é usado porque a query é o genoma inteiro, o que
> torna a cobertura do HSP sempre próxima de zero. A cobertura do sujeito mede
> corretamente quanto do gene de virulência foi alinhado.

## Laudos (Ollama)

Os laudos são gerados apenas para amostras com tipo `emm` confirmado. Para manter
a inferência viável em CPU, o perfil de virulência é resumido por categoria do
VFDB (com poucos genes de exemplo) e a classificação do alerta é calculada em
Python, garantindo reprodutibilidade:

| Tag | Critério |
|---|---|
| `[ALERTA VERMELHO]` | presença de toxina superantigénica (`speA`, `speC`, `speD`, `speG`, `speH`, `speI`, `speJ`, `speK`, `speL`, `speM`, `ssa`, `smeZ`) |
| `[ALERTA AMARELO]` | evasão imune/adesão sem toxina superantigénica |
| `[PERFIL ENDÉMICO PADRÃO]` | risco basal |

> `speB` é uma protease de cisteína, não um superantigénio, e por isso **não**
> entra no critério de alerta vermelho.

Variáveis de ambiente opcionais:

| Variável | Padrão | Função |
|---|---|---|
| `OLLAMA_MODELO` | `llama3:8b` | modelo do Ollama |
| `OLLAMA_NUM_THREAD` | `16` | threads de CPU para inferência |
| `OLLAMA_NUM_PREDICT` | `300` | limite de tokens da resposta |
| `LAUDO_MAX_GENES` | `24` | genes de exemplo no prompt |
| `LAUDO_MAX_GENES_CATEGORIA` | `4` | exemplos por categoria |

## Avisos conhecidos

- O emmtyper emite `UserWarning: The parameter -d is used more than once.` — é
  inofensivo; a pipeline usa apenas parâmetros longos.
- No workflow PCR pode aparecer `FASTA-Reader: Title ends with at least 20 valid
  nucleotide characters.` — não interrompe a execução.
- A inferência do Ollama em CPU varia com a carga do servidor. Com o perfil
  resumido, cada laudo leva cerca de 15–30 s em carga moderada; em momentos de
  carga alta pode levar vários minutos.

## Reprodutibilidade

```bash
emmtyper --version > resultados/emmtyper_version.txt
micromamba list -n emmtyper > resultados/ambiente_emmtyper.txt
sha256sum banco_dados/VFDB_S.pyogenes.fas > resultados/vfdb.sha256
date -Is > resultados/data_execucao.txt
```
