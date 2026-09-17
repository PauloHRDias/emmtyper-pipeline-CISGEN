# Tipagem emm de Streptococcus pyogenes com emmtyper

Pipeline reprodutível para tipagem in silico do gene emm em assemblies genômicos de Streptococcus pyogenes, usando emmtyper em dois fluxos:

- blast: busca direta no assembly contra as referências emm.
- pcr: PCR in silico com os primers distribuídos pela ferramenta, seguida de comparação do amplicon contra as referências emm.

A pesquisa de fatores de virulência com VFDB é uma etapa independente e não utiliza o banco emm.fna dentro do emmtyper.

## Estrutura de diretórios

text
teste_emmtyper/
├── entrada/

│   └── GCF_022869605.1_ASM2286960v1_genomic.fna

├── logs/

├── resultados_blast/

├── resultados_pcr/

└── README.md


O assembly em entrada/ pode ser um link simbólico para o arquivo original, evitando duplicação de espaço em disco.

## Requisitos

- micromamba com o ambiente emmtyper instalado e ativado.
- emmtyper 0.2.0.
- blastn disponível no mesmo ambiente.
- Assembly em formato FASTA nucleotídico (.fna, .fa ou .fasta).
- Executável isPcr disponível para a rodada pcr.

## Ativar o ambiente

bash
micromamba activate emmtyper

command -v emmtyper
command -v blastn
command -v isPcr

emmtyper --help


> Observação: a exibição de avisos sobre a opção curta -d duplicada é um comportamento da combinação instalada de emmtyper/click.
> Não use a opção curta -d; prefira sempre opções longas.

## Definir variáveis

Execute a partir do diretório do projeto:

bash
GENOME="$HOME/teste_emmtyper/entrada/GCF_022869605.1_ASM2286960v1_genomic.fna"

EMMTYPER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/db/emm.fna"

PRIMER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/data/isPcrPrim.tsv"


Se o ambiente for criado com outra versão do Python, ajuste somente o trecho lib/python3.14. Para evitar essa dependência, localize o banco com:

bash
find "$CONDA_PREFIX/lib" -path "*/emmtyper/db/emm.fna" -print
find "$CONDA_PREFIX/lib" -path "*/emmtyper/data/isPcrPrim.tsv" -print


## Validação pré-execução

bash
printf 'Assembly: %s\nBanco emm: %s\nPrimers: %s\n' \
  "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB"

for ARQ in "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB"; do
  if test -s "$ARQ"; then
    echo "OK: $ARQ"
  else
    echo "ERRO: arquivo inexistente, inacessível ou vazio: $ARQ"
  fi
done

echo "Contigs no assembly:"
grep -c '^>' "$GENOME"


A análise só deve prosseguir se todos os arquivos mostrarem OK.

## Rodada BLAST

Esta rodada pesquisa diretamente a sequência do assembly contra o banco de referências emm.fna.

bash
mkdir -p resultados_blast logs

emmtyper \
  --workflow blast \
  --blast_db "$EMMTYPER_DB" \
  --keep \
  "$GENOME" \
  > resultados_blast/emmtyper_blast.stdout.log \
  2> logs/emmtyper_blast.stderr.log

echo "Código de saída: $?"


## Rodada PCR in silico

Esta rodada usa os primers de isPcrPrim.tsv para obter amplicons in silico. Os amplicons são então comparados ao banco emm.fna.

bash
mkdir -p resultados_pcr logs

emmtyper \
  --workflow pcr \
  --blast_db "$EMMTYPER_DB" \
  --primer-db "$PRIMER_DB" \
  --keep \
  "$GENOME" \
  > resultados_pcr/emmtyper_pcr.stdout.log \
  2> logs/emmtyper_pcr.stderr.log

echo "Código de saída: $?"


## Verificação de resultados

bash
echo "===== BLAST: saída principal ====="
cat resultados_blast/emmtyper_blast.stdout.log

echo "===== PCR: saída principal ====="
cat resultados_pcr/emmtyper_pcr.stdout.log

echo "===== Logs ====="
cat logs/emmtyper_blast.stderr.log
cat logs/emmtyper_pcr.stderr.log

echo "===== Arquivos gerados ====="
find . -type f -printf "%p\t%k KB\n" | sort


O código de saída 0 indica que a execução terminou sem erro operacional. O tipo/subtipo emm deve ser registrado conforme reportado pelo emmtyper e 
comparado entre os fluxos blast e pcr.

## Registro para reprodutibilidade

bash
emmtyper --help > emmtyper_help.txt

sha256sum "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB" \
  > referencias_e_entrada.sha256

micromamba list -n emmtyper > ambiente_emmtyper.txt

date -Is > data_execucao.txt


Arquive, juntamente com o resultado, os arquivos emmtyper_help.txt, referencias_e_entrada.sha256, ambiente_emmtyper.txt, os logs e os outputs preservados pela opção --keep.

## Escopo do projeto

- Tipagem emm: emmtyper + banco de referência emm.fna.
- Virulência: uma etapa separada com blastn/outra ferramenta, usando VFDB.
- O VFDB não deve ser empregado como argumento de --blast_db do emmtyper.

## Pareceres pós teste

 1 Criado estrutura organizada de diretórios para Entradas, logs e resultados 
~/teste_emmtyper/
├── entrada/

│   └── GCF_022869605.1_ASM2286960v1_genomic.fna

├── logs/

│   ├── emmtyper_blast.stderr.log

│   └── emmtyper_pcr.stderr.log

├── resultados_blast/

│   └── emmtyper_blast.stdout.log

├── resultados_pcr/

│   └── emmtyper_pcr.stdout.log

├── GCF_022869605.tmp

└── GCF_022869605_pcr.tmp

## Fluxo executado

A tipagem in silico do gene emm é realizada por duas estratégias disponíveis no emmtyper:

1. *Workflow BLAST (--workflow blast)*: busca direta da sequência do assembly contra o banco de referências emm.fna.
2. *Workflow PCR (--workflow pcr): PCR *in silico com isPcr, seguida de busca BLAST do amplicon recuperado contra o banco emm.fna.

Os dois workflows utilizam o banco de referência de emm distribuído com a própria ferramenta. A análise de fatores de virulência com VFDB é independente e não deve substituir o banco emm.fna neste workflow.

## Caminhos das dependências

Com o ambiente emmtyper ativo:

bash
GENOME="$HOME/teste_emmtyper/entrada/GCF_022869605.1_ASM2286960v1_genomic.fna"

EMMTYPER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/db/emm.fna"

PRIMER_DB="$CONDA_PREFIX/lib/python3.14/site-packages/emmtyper/data/isPcrPrim.tsv"

ISPCR_PATH="$(command -v isPcr)"


Verificar instalação:

bash
command -v emmtyper
command -v blastn
command -v isPcr

for ARQ in "$GENOME" "$EMMTYPER_DB" "$PRIMER_DB" "$ISPCR_PATH"; do
  test -s "$ARQ" && echo "OK: $ARQ" || echo "ERRO: $ARQ"
done


## Execução: BLAST

bash
mkdir -p resultados_blast logs

emmtyper \
  --workflow blast \
  --blast_db "$EMMTYPER_DB" \
  --keep \
  "$GENOME" \
  > resultados_blast/emmtyper_blast.stdout.log \
  2> logs/emmtyper_blast.stderr.log


## Execução: PCR in silico

bash
mkdir -p resultados_pcr logs

emmtyper \
  --workflow pcr \
  --blast_db "$EMMTYPER_DB" \
  --primer-db "$PRIMER_DB" \
  --ispcr-path "$ISPCR_PATH" \
  --keep \
  "$GENOME" \
  > resultados_pcr/emmtyper_pcr.stdout.log \
  2> logs/emmtyper_pcr.stderr.log


## Resultados e interpretação

Os resultados resumidos ficam em:

text
resultados_blast/emmtyper_blast.stdout.log
resultados_pcr/emmtyper_pcr.stdout.log


Os arquivos brutos preservados pela opção --keep ficam inicialmente no diretório de execução:

text
GCF_022869605.tmp
GCF_022869605_pcr.tmp


Esses arquivos têm formato tabular de BLAST e devem ser visualizados com:

bash
column -t -s $'\t' GCF_022869605.tmp
column -t -s $'\t' GCF_022869605_pcr.tmp


Antes de uma nova execução, arquivar os intermediários:

bash
cp GCF_022869605.tmp resultados_blast/GCF_022869605.blast.raw.tsv
cp GCF_022869605_pcr.tmp resultados_pcr/GCF_022869605.pcr.raw.tsv


## Exemplo de teste executado

Assembly analisado:

text
GCF_022869605.1_ASM2286960v1_genomic.fna


Resultado principal:

| Workflow | Tipo emm principal | Identidade | Alinhamento | Cobertura da referência |
|---|---:|---:|---:|---:|
| BLAST | emm1.0 | 100% | 180/180 bp | 100% |
| PCR in silico + BLAST | emm1.0 | 100% | 180/180 bp | 100% |

A concordância entre os dois workflows apoia a chamada de emm1.0 para este assembly. A busca direta por BLAST também identificou um hit perfeito adicional para EMM166.1 em uma coordenada distinta do genoma. Esse hit deve ser mantido no resultado bruto e revisado, mas não deve ser interpretado automaticamente como um segundo tipo emm sem investigação adicional.

## Avisos conhecidos

A versão instalada pode emitir o aviso:

text
UserWarning: The parameter -d is used more than once.


O aviso não interrompeu as execuções realizadas, que terminaram com código de saída 0. Evite utilizar a opção curta -d; use parâmetros longos.

No workflow PCR, pode aparecer o aviso:

text
FASTA-Reader: Title ends with at least 20 valid nucleotide characters.


Esse aviso deve ser registrado no log e investigado mediante inspeção do arquivo intermediário gerado pelo workflow PCR.

## Resultado do teste

Assembly analisado:

text
GCF_022869605.1_ASM2286960v1_genomic.fna


O emmtyper foi executado em dois workflows:

- blast: alinhamento direto do assembly contra o banco de referência emm.fna;
- pcr: PCR in silico com isPcr, seguida de alinhamento do amplicon contra emm.fna.

| Workflow | Tipo emm | Identidade | Alinhamento | Cobertura | Mismatches | Gaps | Bitscore |
|---|---|---:|---:|---:|---:|---:|---:|
| BLAST | emm1.0 | 100.000% | 180 bp | 180/180 bp (100%) | 0 | 0 | 333 |
| PCR in silico + BLAST | emm1.0 | 100.000% | 180 bp | 180/180 bp (100%) | 0 | 0 | 333 |

A chamada emm1.0 foi concordante nos dois workflows.

Os dados consolidados estão em:

text
resultados/resultados_emm_resumo.tsv


Os resultados brutos e logs podem ser encontrados em:

text
resultados_blast/
resultados_pcr/
logs/


## Limitações conhecidas da versão instalada

- A versão do emmtyper instalada pode emitir avisos sobre a opção curta `-d` duplicada.
- O workflow PCR pode exibir o aviso `FASTA-Reader: Title ends with at least 20 valid nucleotide characters`.
- Esses avisos não interrompem a execução, mas devem ser registrados nos logs para rastreabilidade.
