# Tipagem emm de Streptococcus pyogenes e Vigilância Genômica

Pipeline reprodutível para tipagem *in silico* do gene *emm* em assemblies genômicos de *Streptococcus pyogenes* utilizando o **emmtyper**, integrado a um motor de Inteligência Artificial (RAG) para laudos epidemiológicos automatizados.

O pipeline divide-se em três fluxos principais:
1. **BLAST**: Busca direta no assembly contra as referências *emm*.
2. **PCR *in silico***: PCR com os primers distribuídos pela ferramenta, seguida de comparação do amplicon contra as referências *emm*.
3. **Análise de Virulência e Laudo (IA)**: Mapeamento independente de fatores de virulência (VFDB) e geração de laudo clínico via Llama 3 local.

## 📂 Estrutura de Diretórios

```text
teste_emmtyper/
├── entrada/
│   └── GCF_022869605.1_ASM2286960v1_genomic.fna
├── banco_dados/
│   └── VFDB_S.pyogenes.fas
├── scripts/
│   ├── vigilancia_bot.py
│   ├── rag_vigilancia.py
│   └── testar_ollama.py
├── logs/
├── resultados_blast/
├── resultados_pcr/
└── resultados_consolidados/
```
O assembly em `entrada/` pode ser um link simbólico para o arquivo original, evitando duplicação de espaço em disco.

## ⚙️ Requisitos
- `micromamba` com o ambiente `emmtyper` instalado e ativado.
- `emmtyper 0.2.0` e `blastn` disponíveis no mesmo ambiente.
- Executável `isPcr`.
- Assembly em formato FASTA nucleotídico (`.fna`, `.fa` ou `.fasta`).
- **Módulo de IA:** Docker e contêiner do Ollama configurado com Llama 3.

## 🚀 Preparação e Validação

**1. Ativar o ambiente e definir variáveis:**
```bash
micromamba activate emmtyper

GENOME="$HOME/teste_emmtyper/entrada/GCF_022869605.1_ASM2286960v1_genomic.fna"
EMMTYPER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/db/emm.fna"
PRIMER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/data/isPcrPrim.tsv"
ISPCR_PATH="$(command -v isPcr)"
```

**2. Validação pré-execução:**
```bash
for ARQ in "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB" "$ISPCR_PATH"; do
    test -s "$ARQ" && echo "OK: $ARQ" || echo "ERRO: arquivo inexistente ou vazio: $ARQ"
done
echo "Contigs no assembly:"
grep -c '^>' "$GENOME"
```
*A análise só deve prosseguir se todos os arquivos mostrarem OK.*

## 🔬 Execução da Tipagem Genômica

### Rodada BLAST
Busca direta da sequência do assembly contra o banco de referências `emm.fna`.
```bash
mkdir -p resultados_blast logs
emmtyper --workflow blast --blast_db "$EMMTYPER_DB" --keep "$GENOME" > resultados_blast/emmtyper_blast.stdout.log 2> logs/emmtyper_blast.stderr.log
echo "Código de saída: $?"
```

### Rodada PCR in silico
Busca com primers para obter amplicons in silico, comparados ao banco `emm.fna`.
```bash
mkdir -p resultados_pcr
emmtyper --workflow pcr --blast_db "$EMMTYPER_DB" --primer-db "$PRIMER_DB" --ispcr-path "$ISPCR_PATH" --keep "$GENOME" > resultados_pcr/emmtyper_pcr.stdout.log 2> logs/emmtyper_pcr.stderr.log
echo "Código de saída: $?"
```

### Verificação e Arquivamento de Resultados
Os arquivos brutos (`.tmp`) gerados pela flag `--keep` têm formato tabular de BLAST.
```bash
# Visualizar resultados brutos corrigidos
column -t -s $'\t' GCF_022869605_pcr.tmp

# Arquivar resultados intermediários
cp GCF_022869605.tmp resultados_blast/GCF_022869605.blast.raw.tsv
cp GCF_022869605_pcr.tmp resultados_pcr/GCF_022869605.pcr.raw.tsv
```

## 🧠 Módulo de Inteligência Artificial Epidemiológica (RAG)

Após a tipagem e extração dos perfis de virulência pelo EpiBuilder, o pipeline utiliza um motor de IA local (Llama 3 via Ollama) para automatizar a geração de laudos epidemiológicos e alertas de vigilância genômica. A arquitetura utiliza **Retrieval-Augmented Generation (RAG)** em conjunto com o LangChain para garantir precisão clínica absoluta e evitar alucinações.

### Scripts de Integração (`scripts/`)
* **`testar_ollama.py`**: Diagnóstico e validação da API.
* **`rag_vigilancia.py`**: Lê o banco VFDB e cria o dicionário de mapeamento genético.
* **`vigilancia_bot.py`**: Consome os metadados (`epibuilder_metadata.tsv`), traduz os genes e injeta no LLM (`temperature=0.0`) para gerar laudos com classificação de risco (`[ALERTA VERMELHO]`, `[ALERTA AMARELO]`, etc.) em modo de fluxo (*stream*).

### Como gerar o laudo
```bash
# Certifique-se de que o contêiner do Ollama está rodando
docker start ollama

# Execute o bot de vigilância
python3 scripts/vigilancia_bot.py
```

## 📝 Registro para Reprodutibilidade
Arquivamento do ambiente exato utilizado na análise:
```bash
emmtyper --help > emmtyper_help.txt
sha256sum "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB" > referencias_e_entrada.sha256
micromamba list -n emmtyper > ambiente_emmtyper.txt
date -Is > data_execucao.txt
```

## ⚠️ Avisos Conhecidos e Limitações
- **Parâmetro duplicado:** A versão instalada pode emitir `UserWarning: The parameter -d is used more than once.`. Evite a opção curta `-d`; use parâmetros longos.
- **Aviso FASTA-Reader:** No workflow PCR, pode surgir `FASTA-Reader: Title ends with at least 20 valid nucleotide characters.`.
*Esses avisos não interrompem a execução, mas devem ser registrados nos logs para rastreabilidade.*
