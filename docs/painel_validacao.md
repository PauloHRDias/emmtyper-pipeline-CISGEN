# Painel de validação — *Streptococcus pyogenes*

Painel de 12 genomas completos de *S. pyogenes* usado para validar a
tipagem *emm* e o perfil de virulência (VFDB) da pipeline.

| ID | Tipo emm | Genes VFDB | Estirpe |
|---|---|---:|---|
| `GCF_000006785` | EMM1.6 | 224 | SF370 (M1 GAS) |
| `GCF_000167435` | EMM49.1 | 180 | M49 591 |
| `GCF_000756485` | EMM23.0 | 215 | M23ND |
| `GCF_001014305` | EMM6.52 | 220 | D471 |
| `GCF_001020185` | EMM28.0 | 219 | M28PF1 |
| `GCF_001620285` | EMM53.0 | 220 | AP53 |
| `GCF_001635895` | EMM89.0 | 218 | MGAS11027 |
| `GCF_001635975` | EMM89.0 | 189 | MGAS27061 |
| `GCF_002355175` | EMM3.1 | 229 | M3-b |
| `GCF_003640605` | EMM4.0 | 189 | SASM4-Duke |
| `GCF_004135875` | EMM75.0 | 199 | M75 |
| `GCF_022869605` | EMM1.0 | 223 | PartK-Spyogenes-RM8376 |

## Resultado

- 12/12 amostras classificadas como *S. pyogenes*.
- 11 tipos emm distintos: EMM1.0, EMM1.6, EMM23.0, EMM28.0, EMM3.1, EMM4.0, EMM49.1, EMM53.0, EMM6.52, EMM75.0, EMM89.0.
- 0 falhas de tipagem ou de BLAST.
- QC de montagem: 12/12 `OK` — 1 contig por amostra, 1,74–1,91 Mb,
  GC 38,35–38,63%, 0 `N`.
- Laudos gerados para todas as amostras (ver `resultados_consolidados/laudos.txt`).

## Proveniência

Genomas completos obtidos do NCBI RefSeq com o comando:

```bash
datasets download genome accession \
  GCF_002355175.1,GCF_001020185.2,GCF_000167435.2,GCF_001620285.1,GCF_004135875.1,\
  GCF_000756485.1,GCF_001635895.1,GCF_001635975.1,GCF_003640605.1,GCF_001014305.1 \
  --include genome --filename painel_spyogenes.zip
```

Os dois genomas já existentes (`GCF_000006785.2` e `GCF_022869605.1`) foram
mantidos. As cinco amostras de outras espécies usadas inicialmente como
controles negativos foram removidas de `entrada/`.

## Reprodução

```bash
# Lote completo (QC + tipagem + VFDB + laudos + relatório)
./pipeline_principal.sh

# Validação rápida com metadados de exemplo (sem laudos)
./pipeline_principal.sh --sem-laudos --metadados docs/metadados_exemplo.tsv
```
