#!/bin/bash
#
# Pipeline de vigilancia genomica de Streptococcus pyogenes (CIGenS/SC).
#
# Para cada assembly em entrada/*.fna:
#   1. QC basico de montagem
#   2. tipagem emm (emmtyper, workflow BLAST)
#   3. perfil de virulencia (blastn contra o VFDB)
#   4. (opcional) tipagem por PCR in silico
# Ao final:
#   5. consolidacao da tabela (emm + virulencia reais)
#   6. juncao de metadados clinico-epidemiologicos (opcional)
#   7. laudos epidemiologicos via Ollama (por defeito)
#   8. relatorio resumido do lote

set -u

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RAIZ" || exit 1
source "$RAIZ/config.sh"

USAR_PCR=0
USAR_QC=1
GERAR_LAUDOS=1
GERAR_RELATORIO=1
METADADOS=""
AMOSTRAS=()

uso() {
  cat <<'EOF'
Uso: ./pipeline_principal.sh [opcoes]

  (sem opcoes)          lote completo: QC + tipagem + VFDB + laudos + relatorio
  --sem-laudos          pula a geracao de laudos (mais rapido)
  --sem-qc              pula o QC basico de montagem
  --sem-relatorio       pula o relatorio resumido do lote
  --pcr                 inclui tipagem por PCR in silico
  --metadados CAMINHO   junta metadados clinico-epidemiologicos (CSV/TSV)
  --amostra CAMINHO     processa apenas uma amostra
  -h, --help            mostra esta ajuda
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --pcr)          USAR_PCR=1; shift ;;
    --sem-laudos)   GERAR_LAUDOS=0; shift ;;
    --sem-qc)       USAR_QC=0; shift ;;
    --sem-relatorio) GERAR_RELATORIO=0; shift ;;
    --metadados)
      if [ "$#" -lt 2 ]; then
        echo "ERRO: --metadados requer um caminho." >&2
        exit 2
      fi
      if [ ! -f "$2" ]; then
        echo "ERRO: metadados nao encontrados: $2" >&2
        exit 2
      fi
      METADADOS="$2"
      shift 2
      ;;
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
echo " Amostras: ${#AMOSTRAS[@]} | PCR: $USAR_PCR | QC: $USAR_QC | Laudos: $GERAR_LAUDOS"
echo "=============================================================="

QC_TSV="$RAIZ/resultados_consolidados/qc_montagem.tsv"
if [ "$USAR_QC" -eq 1 ]; then
  echo
  echo "=============================================================="
  echo " QC basico de montagem"
  echo "=============================================================="
  "$CONDA_PREFIX/bin/python" "$RAIZ/scripts/qc_montagem.py" \
    --saida "$QC_TSV" "${AMOSTRAS[@]}"
  STATUS_QC=$?
  if [ "$STATUS_QC" -ne 0 ]; then
    echo "AVISO: o QC de montagem terminou com codigo $STATUS_QC." >&2
  fi
fi

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

TABELA_FINAL="$SAIDA_EPIBUILDER"
if [ -n "$METADADOS" ]; then
  echo
  echo "=============================================================="
  echo " Juntando metadados clinico-epidemiologicos"
  echo "=============================================================="
  TABELA_FINAL="$RAIZ/resultados_consolidados/epibuilder_completo.tsv"
  QC_ARG=""
  if [ "$USAR_QC" -eq 1 ]; then
    QC_ARG="$QC_TSV"
  fi
  "$CONDA_PREFIX/bin/python" "$RAIZ/scripts/juntar_metadados.py" \
    --genomico "$SAIDA_EPIBUILDER" \
    --metadados "$METADADOS" \
    --qc "$QC_ARG" \
    --saida "$TABELA_FINAL"
  STATUS_META=$?
  if [ "$STATUS_META" -ne 0 ]; then
    echo "AVISO: a juncao de metadados falhou (codigo $STATUS_META); a usar apenas a tabela genomica." >&2
    TABELA_FINAL="$SAIDA_EPIBUILDER"
  fi
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

if [ "$GERAR_RELATORIO" -eq 1 ]; then
  echo
  echo "=============================================================="
  echo " Gerando relatorio resumido do lote"
  echo "=============================================================="
  ARQ_LAUDOS_RELATORIO=""
  if [ "$GERAR_LAUDOS" -eq 1 ]; then
    ARQ_LAUDOS_RELATORIO="$RAIZ/resultados_consolidados/laudos.txt"
  fi
  "$CONDA_PREFIX/bin/python" "$RAIZ/scripts/relatorio_lote.py" \
    --tabela "$TABELA_FINAL" \
    --laudos "$ARQ_LAUDOS_RELATORIO" \
    --vfdb "$RAIZ/banco_dados/VFDB_S.pyogenes.fas" \
    --saida "$RAIZ/resultados_consolidados/relatorio_lote.md"
  STATUS_RELATORIO=$?
  if [ "$STATUS_RELATORIO" -ne 0 ]; then
    echo "AVISO: o relatorio do lote terminou com codigo $STATUS_RELATORIO." >&2
  fi
fi

echo
echo "=============================================================="
echo " Resumo: $PROCESSADAS processada(s), $FALHAS falha(s)"
if [ "$FALHAS" -gt 0 ]; then
  printf '  - %s\n' "${FALHAS_LISTA[@]}"
fi
[ "$USAR_QC" -eq 1 ] && echo " QC: $QC_TSV"
echo " Tabela: $TABELA_FINAL"
[ "$GERAR_LAUDOS" -eq 1 ] && echo " Laudos: $RAIZ/resultados_consolidados/laudos.txt"
[ "$GERAR_RELATORIO" -eq 1 ] && echo " Relatorio: $RAIZ/resultados_consolidados/relatorio_lote.md"
echo "=============================================================="

[ "$FALHAS" -eq 0 ] || exit 1
