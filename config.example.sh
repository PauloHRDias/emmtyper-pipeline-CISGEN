# Copie este ficheiro para config.sh e ajuste os caminhos se necessario.
# Configuracao do pipeline de vigilancia genomica (S. pyogenes).

# Caminho absoluto do micromamba (necessario em shells nao-interativos).
export MICROMAMBA_EXE="${MICROMAMBA_EXE:-/resultados/Analises_Paulo/micromamba/micromamba}"
export MICROMAMBA_ENV="${MICROMAMBA_ENV:-emmtyper}"

# Garante CONDA_PREFIX e PATH mesmo sem `micromamba activate` previo.
if [ -z "${CONDA_PREFIX:-}" ] || [ "$(basename "${CONDA_PREFIX}")" != "$MICROMAMBA_ENV" ]; then
  export CONDA_PREFIX="$("$MICROMAMBA_EXE" run -n "$MICROMAMBA_ENV" printenv CONDA_PREFIX 2>/dev/null)"
fi
export PATH="$CONDA_PREFIX/bin:$PATH"

# Raiz do projeto (diretorio onde este ficheiro vive).
export PROJETO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ENTRADA_DIR="$PROJETO_DIR/entrada"

# Amostra unica (compatibilidade com execucao individual).
export GENOME="$ENTRADA_DIR/GCF_022869605.1_ASM2286960v1_genomic.fna"

# Bancos e ferramentas do emmtyper.
export EMMTYPER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/db/emm.fna"
export PRIMER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/data/isPcrPrim.tsv"
export ISPCR_PATH="$(command -v isPcr)"

# Banco de virulencia (VFDB) e indice BLAST.
export VFDB_DB="$PROJETO_DIR/banco_dados/vfdb_pyogenes_index"

# Limiares de deteccao de genes de virulencia.
# Cobertura do sujeito = length/slen * 100 (a query e o genoma inteiro).
export VFDB_MIN_PIDENT="${VFDB_MIN_PIDENT:-90}"
export VFDB_MIN_QCOV="${VFDB_MIN_QCOV:-70}"

# Saidas consolidadas.
export SCRIPT_EPIBUILDER="$PROJETO_DIR/scripts/prepara_epibuilder.py"
export SAIDA_EPIBUILDER="$PROJETO_DIR/resultados_consolidados/epibuilder_metadata.tsv"
