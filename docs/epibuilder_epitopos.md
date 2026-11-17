# Análise complementar: epítopos de células B com EpiBuilder

Esta é uma **análise científica separada** da pipeline de vigilância. Ela não
produz tipagem *emm*, perfil de virulência nem laudos — seu objetivo é prever
**epítopos lineares de células B** nas proteínas de fatores de virulência de
*S. pyogenes*, com aplicação em pesquisa de vacinas e testes diagnósticos.

> ⚠️ O EpiBuilder **não é** um painel de vigilância epidemiológica. Ele é uma
> plataforma do LabBioInfo/UFSC que orquestra BepiPred-3, PSORTb e BLAST para
> predição/classificação de epítopos. Para visualização dos resultados da
> vigilância, use o `dashboard.html` (e, no futuro, um app Streamlit).

## 1. Preparar a entrada (proteínas do VFDB)

O EpiBuilder consome **proteínas**, enquanto o VFDB local está em nucleotídeos.
O script abaixo traduz os genes e grava também um TSV de referência:

```bash
cd ~/teste_emmtyper
source config.sh
"$CONDA_PREFIX/bin/python" scripts/preparar_epitopos.py
```

Saídas:

- `analises/epibuilder/VFDB_S_pyogenes_proteins.fasta` — 333 proteínas (de 336 genes);
- `analises/epibuilder/proteins_metadata.tsv` — ID da proteína ↔ VFG, gene e produto.

Três sequências são descartadas por serem curtas ou ambíguas após a tradução.
O `analises/epibuilder/` não é versionado pelo Git.

## 2. Rodar o EpiBuilder (CLI)

As imagens já estão no servidor (`bioinfoufsc/epibuilder-core:latest` e
`bioinfoufsc/bepipred3:latest`). Copie o FASTA para o volume do EpiBuilder e
execute o comando oficial, com as flags de rede necessárias neste servidor:

```bash
# 1) copiar a entrada para o volume nomeado (extensao .fasta e obrigatoria)
docker run --rm --entrypoint sh \
  -v epibuilder-data:/tmp/epibuilder \
  -v "$PWD/analises/epibuilder":/entrada:ro \
  bioinfoufsc/epibuilder-core:latest \
  -c 'cp /entrada/VFDB_S_pyogenes_proteins.fasta /tmp/epibuilder/'

# 2) executar a predicao de epitopos (o diretorio --output NAO pode existir)
docker run --rm \
  --sysctl net.ipv6.conf.all.disable_ipv6=1 \
  --dns 150.162.1.1 --dns 150.162.2.2 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v epibuilder-data:/tmp/epibuilder \
  -e EPIBUILDER_VOLUME=epibuilder-data \
  bioinfoufsc/epibuilder-core:latest \
  epibuilder \
    --input_file /tmp/epibuilder/VFDB_S_pyogenes_proteins.fasta \
    --output /tmp/epibuilder/resultado_vfdb \
    --loc gram_pos
```

`--loc gram_pos` ativa o PSORTb para Gram-positivos (o caso de *S. pyogenes*).
O comando gera, em `resultado_vfdb/`: `epitope-detail.tsv`,
`protein-summary.tsv`, `scores.tsv`, `epitopes.fasta` e `epibuilder.xlsx`.

A primeira execução pode demorar: o BepiPred-3 roda deep learning sobre cada
proteína e o Nextflow pode verificar plugins na rede. Validação feita em
16/11/2026 com 3 proteínas: 5/5 processos Nextflow concluídos em 2m19s.
A interface web (`docker compose up -d`, acesso em `http://localhost`) é uma
alternativa para acompanhar os jobs pela interface.

## Resultados obtidos em 16/11/2026

Execução completa das 333 proteínas: **5/5 processos Nextflow concluídos em
14m41s** (`logs/epibuilder.log`, EXIT=0). As saídas foram copiadas para
`analises/epibuilder/resultado_vfdb/` (não versionado).

| Métrica | Valor |
|---|---|
| Proteínas analisadas | 333 |
| Proteínas com pelo menos um epítopo | 287 |
| Epítopos lineares preditos | 1099 |
| Comprimento médio do epítopo | 16,4 resíduos |
| Localização mais frequente | parede celular (80), extracelular (65) |

Proteínas com maior número de epítopos: `VFG005275` (adhesin, 16),
`endoS` (13–14 em seis variantes) e `sfbII/sof` (13). Os epítopos com maior
score BepiPred-3 pertencem a `sfbII/sof`, `endoS` e `hylA` (scores 0,24–0,25).
O cruzamento com `proteins_metadata.tsv` permite associar cada epítopo ao gene
de virulência (VFG) correspondente.

## 3. Interpretar os resultados no contexto do TCC

- Cruze os epítopos preditos com `proteins_metadata.tsv` para saber a que gene
  de virulência (VFG) cada epítopo pertence.
- Priorize epítopos de **adesão** e **toxinas** — são os alvos mais discutidos
  na revisão bibliográfica do TCC.
- Resultados de epítopos são **hipóteses de pesquisa**: exigem validação
  experimental antes de qualquer uso diagnóstico ou vacinal.
- Use como seção de **perspectivas futuras** do TCC, ou como apêndice, sem
  misturar com os resultados de tipagem/virulência (escopo principal).

## Referência

EpiBuilder — labioinfoufsc/UFSC. Disponível em:
https://github.com/labioinfoufsc/EpiBuilder. README interno da imagem
`bioinfoufsc/epibuilder-core:latest` (`/epibuilder/README.pt-br.md`).
