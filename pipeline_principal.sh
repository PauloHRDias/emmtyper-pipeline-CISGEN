#!/bin/bash
#
# Pipeline de vigilancia genomica de Streptococcus pyogenes (CISGEN/SC).
#
# Para cada assembly em entrada/*.fna:
#   1. tipagem emm (emmtyper, workflow BLAST)
#   2. perfil de virulencia (blastn contra o VFDB)
#   3. (opcional) tipagem por PCR in silico
# Ao final:
#   4. consolidacao da tabela (emm + virulencia reais)
#   5. laudos epidemiologicos via Ollama (por defeito)
#
# Uso:
#   ./pipeline_principal.sh                 # lote completo + laudos
#   ./pipeline_principal.sh --sem-laudos    # apenas tipagem/consolidacao
#   ./pipeline_principal.sh --pcr           # inclui PCR in silico
#   ./pipeline_principal.sh --amostra entrada/GCF_XXXX.fna
#   ./pipeline_principal.sh --help

set -u

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RAIZ" || exit 1
source "$RAIZ/config.sh"

USAR_PCR=0
GERAR_LAUDOS=1
AMOSTRAS=()

uso() {
  sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --pcr)          USAR_PCR=1; shift ;;
    --sem-laudos)   GERAR_LAUDOS=0; shift ;;
    --amostra)
      if [ "$#" -lt 2 ]; then
        echo "ERRO: --amostra requer um caminho." >&2
        exit 2
      fi
      CANDIDATO="$2"
      [ -f "$CANDIDATO" ] || CANDIDATO="$ENTRADA_DIR/$2"
      if [ ! -f "$CANDIDATO" ]; then
        echo "ERRO: amostra nao encontrada: $2" >&2
        exit 2
      fi
      AMOSTRAS+=("$CANDIDATO")
      shift 2
      ;;
    -h|--help)      uso; exit 0 ;;
    *)
      echo "ERRO: opcao desconhecida: $1 (use --help)" >&2
      exit 2
      ;;
  esac
done

mkdir -p resultados_blast resultados_pcr logs resultados_consolidados

if [ "${#AMOSTRAS[@]}" -eq 0 ]; then
  shopt -s nullglob
  AMOSTRAS=("$ENTRADA_DIR"/*.fna)
fi

if [ "${#AMOSTRAS[@]}" -eq 0 ]; then
  echo "ERRO: nenhum assembly .fna encontrado em $ENTRADA_DIR" >&2
  exit 1
fi

echo "=============================================================="
echo " Pipeline de vigilancia genomica - $(date '+%Y-%m-%d %H:%M:%S')"
echo " Amostras: ${#AMOSTRAS[@]} | PCR: $USAR_PCR | Laudos: $GERAR_LAUDOS"
echo "=============================================================="

PROCESSADAS=0
FALHAS=0
FALHAS_LISTA=()

for GENOMA in "${AMOSTRAS[@]}"; do
  GENOMA_ABS="$(realpath "$GENOMA")"
  ID_AMOSTRA="$(basename "$GENOMA" | cut -d'.' -f1)"

  echo
  echo "--------------------------------------------------------------"
  echo "[$((PROCESSADAS + FALHAS + 1))/${#AMOSTRAS[@]}] Amostra: $ID_AMOSTRA"
  echo "--------------------------------------------------------------"

  OUT_EMM="$RAIZ/resultados_blast/${ID_AMOSTRA}_emm.stdout.log"
  ERR_EMM="$RAIZ/logs/${ID_AMOSTRA}_emm.stderr.log"
  WORKDIR="$RAIZ/resultados_blast/.work/${ID_AMOSTRA}"

  rm -rf "$WORKDIR"
  mkdir -p "$WORKDIR"

  echo "  -> Tipagem emm (BLAST)..."
  (
    cd "$WORKDIR" || exit 1
    emmtyper --workflow blast \
      --blast_db "$EMMTYPER_DB" \
      --keep \
      --output "$OUT_EMM" \
      "$GENOMA_ABS"
  ) 2> "$ERR_EMM"
  STATUS_EMM=$?

  if [ "$STATUS_EMM" -ne 0 ]; then
    echo "     FALHA no emmtyper (codigo $STATUS_EMM). Ver $ERR_EMM" >&2
    FALHAS=$((FALHAS + 1))
    FALHAS_LISTA+=("$ID_AMOSTRA (emmtyper)")
    rm -rf "$WORKDIR"
    continue
  fi

  # Guarda o resultado bruto do BLAST do emmtyper, quando existir.
  TMP_BLAST="$(find "$WORKDIR" -maxdepth 1 -name '*.tmp' -print -quit)"
  if [ -n "$TMP_BLAST" ]; then
    cp "$TMP_BLAST" "$RAIZ/resultados_blast/${ID_AMOSTRA}.blast.raw.tsv"
  fi
  rm -rf "$WORKDIR"

  echo "     emm: $(cut -f3 "$OUT_EMM" 2>/dev/null | head -1)"

  echo "  -> Perfil de virulencia (VFDB)..."
  ARQ_VFDB="$RAIZ/resultados_consolidados/${ID_AMOSTRA}_vfdb.tsv"
  blastn -query "$GENOMA_ABS" \
    -db "$VFDB_DB" \
    -outfmt "6 qseqid sseqid pident length slen qcovhsp" \
    -max_target_seqs 5000 \
    -out "$ARQ_VFDB" \
    2> "$RAIZ/logs/${ID_AMOSTRA}_vfdb.stderr.log"
  STATUS_VFDB=$?

  if [ "$STATUS_VFDB" -ne 0 ]; then
    echo "     FALHA no blastn VFDB (codigo $STATUS_VFDB). Ver logs/${ID_AMOSTRA}_vfdb.stderr.log" >&2
    FALHAS=$((FALHAS + 1))
    FALHAS_LISTA+=("$ID_AMOSTRA (vfdb)")
    continue
  fi

  echo "     hits VFDB: $(wc -l < "$ARQ_VFDB")"

  if [ "$USAR_PCR" -eq 1 ]; then
    echo "  -> PCR in silico..."
    OUT_PCR="$RAIZ/resultados_pcr/${ID_AMOSTRA}_pcr.stdout.log"
    ERR_PCR="$RAIZ/logs/${ID_AMOSTRA}_pcr.stderr.log"
    mkdir -p "$WORKDIR"
    (
      cd "$WORKDIR" || exit 1
      emmtyper --workflow pcr \
        --blast_db "$EMMTYPER_DB" \
        --primer-db "$PRIMER_DB" \
        --ispcr-path "$ISPCR_PATH" \
        --keep \
        --output "$OUT_PCR" \
        "$GENOMA_ABS"
    ) 2> "$ERR_PCR"
    STATUS_PCR=$?
    if [ "$STATUS_PCR" -ne 0 ]; then
      echo "     AVISO: PCR falhou (codigo $STATUS_PCR). Ver $ERR_PCR" >&2
    else
      echo "     PCR: $(cut -f3 "$OUT_PCR" 2>/dev/null | head -1)"
    fi
    rm -rf "$WORKDIR"
  fi

  PROCESSADAS=$((PROCESSADAS + 1))
done

echo
echo "=============================================================="
echo " Consolidando resultados reais (emm + VFDB)"
echo "=============================================================="

"$CONDA_PREFIX/bin/python" "$RAIZ/scripts/consolidar_lote.py" \
  --entrada-dir "$ENTRADA_DIR" \
  --resultados-blast "$RAIZ/resultados_blast" \
  --resultados-vfdb "$RAIZ/resultados_consolidados" \
  --saida "$SAIDA_EPIBUILDER" \
  --min-pident "$VFDB_MIN_PIDENT" \
  --min-qcov "$VFDB_MIN_QCOV"
STATUS_CONSOLIDACAO=$?

if [ "$STATUS_CONSOLIDACAO" -ne 0 ]; then
  echo "ERRO: falha na consolidacao da tabela." >&2
  exit 1
fi

if [ "$GERAR_LAUDOS" -eq 1 ]; then
  echo
  echo "=============================================================="
  echo " Gerando laudos epidemiologicos (Ollama)"
  echo "=============================================================="
  "$CONDA_PREFIX/bin/python" "$RAIZ/scripts/vigilancia_bot.py" \
    2>&1 | tee "$RAIZ/resultados_consolidados/laudos.txt"
  STATUS_LAUDOS=${PIPESTATUS[0]}
  if [ "$STATUS_LAUDOS" -ne 0 ]; then
    echo "AVISO: a geracao de laudos terminou com codigo $STATUS_LAUDOS." >&2
  fi
fi

echo
echo "=============================================================="
echo " Resumo: $PROCESSADAS processada(s), $FALHAS falha(s)"
if [ "$FALHAS" -gt 0 ]; then
  printf '  - %s\n' "${FALHAS_LISTA[@]}"
fi
echo " Tabela: $SAIDA_EPIBUILDER"
[ "$GERAR_LAUDOS" -eq 1 ] && echo " Laudos: $RAIZ/resultados_consolidados/laudos.txt"
echo "=============================================================="

[ "$FALHAS" -eq 0 ] || exit 1
