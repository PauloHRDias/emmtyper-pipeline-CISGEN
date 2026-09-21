#!/bin/bash

# 1. Carregar as variáveis do config.sh
source config.sh

# Extrair o ID da amostra (ex: GCF_022869605) a partir do caminho do genoma
ID_AMOSTRA=$(basename "$GENOME" | cut -d'.' -f1)

echo "A iniciar análise para a amostra: $ID_AMOSTRA"

# 2. Criar pastas necessárias
mkdir -p resultados_blast resultados_pcr logs resultados_consolidados scripts

# 3. Executar o emmtyper (Workflow BLAST)
echo "A executar emmtyper (Workflow BLAST)..."
emmtyper --workflow blast --blast_db "$EMMTYPER_DB" --keep "$GENOME" \
  resultados_blast/emmtyper_blast.stdout.log \
  2> logs/emmtyper_blast.stderr.log

# Guardar o resumo do emmtyper num ficheiro de fácil acesso
cp resultados_blast/emmtyper_blast.stdout.log resultados_consolidados/resultados_emm_resumo.tsv

# 4. Executar a Virulência (VFDB) com blastn
echo "A executar pesquisa de virulência (VFDB)..."
ARQUIVO_VFDB="resultados_consolidados/${ID_AMOSTRA}_vfdb.tsv"

# ATENÇÃO: Substitua '/caminho/para/VFDB_setB_nt.fas' pelo caminho real do seu banco VFDB
blastn -query "$GENOME" \
       -db "$VFDB_DB" \
       -outfmt "6 qseqid sseqid pident length qcovhsp" \
       -out "$ARQUIVO_VFDB"

# 5. Executar o script "Ponte" para o EpiBuilder
echo "A gerar metadados para o EpiBuilder..."
python scripts/prepara_epibuilder.py \
  --id "$ID_AMOSTRA" \
  --emm "resultados_consolidados/resultados_emm_resumo.tsv" \
  --vfdb "$ARQUIVO_VFDB" \
  --out "resultados_consolidados/epibuilder_metadata.tsv"

echo "Pipeline concluído! Resultados guardados em resultados_consolidados/"
