# Vigilância Genômica de *Streptococcus pyogenes* (CISGEN/SC)

Pipeline reprodutível para **tipagem *emm***, **perfil de virulência (VFDB)** e **laudos epidemiológicos automatizados** de assemblies de *S. pyogenes*.

## O que a pipeline faz

```text
entrada/*.fna
   │
   ├── emmtyper (BLAST) ──────► tipo emm
   ├── blastn contra VFDB ────► genes de virulência
   └── (opcional) PCR in silico
   │
   ▼
resultados_consolidados/epibuilder_metadata.tsv
   │
   ▼
laudos via Ollama (llama3:8b) ──► resultados_consolidados/laudos.txt
```

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

# Lote completo: tipagem + virulência + consolidação + laudos
./pipeline_principal.sh

# Apenas tipagem/virulência/consolidação (sem laudos)
./pipeline_principal.sh --sem-laudos

# Incluir PCR in silico
./pipeline_principal.sh --pcr

# Processar uma amostra específica
./pipeline_principal.sh --amostra entrada/GCF_000006785.2_ASM678v2_genomic.fna

# Ajuda
./pipeline_principal.sh --help
```

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

O painel em `entrada/` contém **12 genomas completos de *S. pyogenes*** com
**11 tipos emm distintos** (EMM1.0, EMM1.6, EMM3.1, EMM4.0, EMM6.52, EMM23.0,
EMM28.0, EMM49.1, EMM53.0, EMM75.0 e EMM89.0). O resultado detalhado está em
[`docs/painel_validacao.md`](docs/painel_validacao.md).

As cinco amostras de outras espécies usadas inicialmente como controles
negativos foram removidas de `entrada/`.

## O que cada script faz

| Script | Função |
|---|---|
| `pipeline_principal.sh` | Orquestra o lote: emmtyper → VFDB → consolidação → laudos. |
| `scripts/consolidar_lote.py` | Monta a tabela final com emm e virulência **reais**. |
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
│   └── vfdb_pyogenes_index.*    # índice BLAST do VFDB
├── scripts/
├── resultados_blast/            # logs do emmtyper e BLAST bruto
├── resultados_pcr/              # saídas do PCR in silico (opcional)
├── resultados_consolidados/     # tabela final e laudos
├── logs/                        # stderr e logs de execução
├── config.sh                    # configuração local (não versionada)
└── pipeline_principal.sh
```

## Saídas esperadas

- `resultados_blast/<ID>_emm.stdout.log` — saída do emmtyper por amostra.
- `resultados_consolidados/<ID>_vfdb.tsv` — hits do blastn contra o VFDB.
- `resultados_consolidados/epibuilder_metadata.tsv` — tabela consolidada:
  `ID_Amostra`, `Tipo_EMM`, `Perfil_Virulencia`.
- `resultados_consolidados/laudos.txt` — laudos gerados pelo Ollama.
- `logs/<ID>_*.stderr.log` — erros e avisos por etapa.

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
| `[ALERTA VERMELHO]` | presença de toxina superantigénica (`speA`, `speB`, `speC`, `speG`, `speI`, `ssa`, ...) |
| `[ALERTA AMARELO]` | evasão imune/adesão sem toxina superantigénica |
| `[PERFIL ENDÉMICO PADRÃO]` | risco basal |

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
