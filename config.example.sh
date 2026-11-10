# Copie este ficheiro para config.sh e ajuste os caminhos conforme necessário.
# Caminho absoluto do micromamba (necessário em shells não-interativos,
# onde o binário não está no PATH). Pode ser sobreposto pelo ambiente.
export MICROMAMBA_EXE="${MICROMAMBA_EXE:-/resultados/Analises_Paulo/micromamba/micromamba}"

export GENOME="$HOME/teste_emmtyper/entrada/GCF_022869605.1_ASM2286960v1_genomic.fna"
export EMMTYPER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/db/emm.fna"
export PRIMER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/data/isPcrPrim.tsv"
export ISPCR_PATH="$(command -v isPcr)"
export SCRIPT_EPIBUILDER="$HOME/teste_emmtyper/scripts/prepara_epibuilder.py"
export SAIDA_EPIBUILDER="$HOME/teste_emmtyper/resultados_consolidados/epibuilder_metadata.tsv"
export VFDB_DB="$HOME/teste_emmtyper/banco_dados/vfdb_pyogenes_index"
