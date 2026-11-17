# Painel de validação — *Streptococcus pyogenes* (30 genomas)

Painel de 30 genomas completos de *S. pyogenes* usado para validar a tipagem *emm* e o perfil de virulência (VFDB) da pipeline.

| ID | Tipo emm | Genes VFDB | Município (sintético) | UF |
|---|---|---:|---|---|
| `GCF_000006785` | EMM1.6 | 224 | Florianopolis | SC |
| `GCF_000167435` | EMM49.1 | 180 | Joinville | SC |
| `GCF_000756485` | EMM23.0 | 215 | Blumenau | SC |
| `GCF_001014305` | EMM6.52 | 220 | Chapeco | SC |
| `GCF_001020185` | EMM28.0 | 219 | Criciuma | SC |
| `GCF_001620285` | EMM53.0 | 220 | Itajai | SC |
| `GCF_001635895` | EMM89.0 | 218 | Lages | SC |
| `GCF_001635975` | EMM89.0 | 189 | Balneario_Camboriu | SC |
| `GCF_002055535` | EMM1.0 | 223 | Petropolis | RJ |
| `GCF_002355175` | EMM3.1 | 229 | Florianopolis | SC |
| `GCF_003640605` | EMM4.0 | 189 | Joinville | SC |
| `GCF_004028355` | EMM1.0 | 223 | Belo_Horizonte | MG |
| `GCF_004124075` | EMM77.0 | 199 | Niteroi | RJ |
| `GCF_004135875` | EMM75.0 | 199 | Blumenau | SC |
| `GCF_006364235` | EMM1.0 | 223 | Salvador | BA |
| `GCF_009832845` | EMM238.1 | 209 | Fortaleza | CE |
| `GCF_020826935` | EMM9.0 | 210 | Guarulhos | SP |
| `GCF_022869605` | EMM1.0 | 223 | Criciuma | SC |
| `GCF_029637645` | EMM1.0 | 222 | Brasilia | DF |
| `GCF_041071735` | EMM77.0 | 199 | Curitiba | PR |
| `GCF_041072535` | EMM77.0 | 189 | Itajai | SC |
| `GCF_041072725` | EMM77.0 | 200 | Porto_Alegre | RS |
| `GCF_041072835` | EMM77.0 | 199 | Santos | SP |
| `GCF_041073745` | EMM77.0 | 199 | Campinas | SP |
| `GCF_041074825` | EMM77.0 | 201 | Joinville | SC |
| `GCF_041430535` | EMM94.1 | 204 | Blumenau | SC |
| `GCF_044361195` | EMM82.0 | 225 | Manaus | AM |
| `GCF_056673615` | EMM58.0 | 214 | Recife | PE |
| `GCF_057980765` | EMM28.0 | 219 | Florianopolis | SC |
| `GCF_900475035` | EMM83.1 | 206 | Sao_Paulo | SP |

## Resultado

- 30/30 amostras classificadas como *S. pyogenes*; **0** `NAO_S_PYOGENES` e **0** `NAO_PROCESSADO`.
- 18 tipos emm distintos: EMM1.0, EMM1.6, EMM23.0, EMM238.1, EMM28.0, EMM3.1, EMM4.0, EMM49.1, EMM53.0, EMM58.0, EMM6.52, EMM75.0, EMM77.0, EMM82.0, EMM83.1, EMM89.0, EMM9.0, EMM94.1.
- 0 falhas de tipagem ou de BLAST; QC de montagem 30/30 `OK`.
- 30 laudos gerados via Ollama (todos `[ALERTA VERMELHO]` no painel atual, por presença de superantígenos).

## Procedência e filtros

Os assemblies foram obtidos da **NCBI Datasets API** (`taxon 1314` = *Streptococcus pyogenes*) em 17/11/2026, com os seguintes filtros:
- `organism_name` exatamente `Streptococcus pyogenes`;
- `assembly_level = Complete Genome`;
- apenas acessos **RefSeq (`GCF_`)**;
- nenhum accession repetido em relação às 12 amostras originais.

Endpoint: `https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/taxon/1314/dataset_report`

> **Atenção:** os genomas são reais, mas `Municipio`, `Data_Coleta`, `Sitio_Anatomico`, `Desfecho`, `Idade` e `Sexo` são **metadados sintéticos** de `docs/metadados_exemplo.tsv`, criados apenas para exercitar a pipeline e o mapa. Nenhuma amostra clínica real foi processada.

## Reprodução

```bash
./pipeline_principal.sh --metadados docs/metadados_exemplo.tsv
```
