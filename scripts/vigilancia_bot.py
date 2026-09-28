import pandas as pd
from langchain_ollama import OllamaLLM
import sys

def carregar_dicionario_vfdb(caminho_fasta):
    """Lê o FASTA do VFDB e cria um dicionário: {ID_Gene: Descrição}"""
    banco_virulencia = {}
    try:
        with open(caminho_fasta, 'r') as fasta:
            for linha in fasta:
                if linha.startswith('>'):
                    partes = linha.strip().split(' ', 1)
                    vfg_id = partes[0].replace('>', '')
                    if len(partes) > 1:
                        descricao = partes[1].rsplit(' [Streptococcus', 1)[0]
                        banco_virulencia[vfg_id] = descricao
    except FileNotFoundError:
        print(f"Erro: Ficheiro VFDB não encontrado em {caminho_fasta}")
        sys.exit(1)
    return banco_virulencia

def processar_amostra(caminho_tsv, dicionario_vfdb):
    """Lê o TSV do EpiBuilder, mapeia os genes e envia para o Llama 3"""
    try:
        df = pd.read_csv(caminho_tsv, sep='\t')
    except Exception as e:
        print(f"Erro ao ler o TSV: {e}")
        sys.exit(1)

    print("Iniciando motor Llama 3 local (Temperatura=0.0)...")
    llm = OllamaLLM(model="llama3", base_url="http://localhost:11434", temperature=0.0)

    amostra = df.iloc[0]
    id_amostra = amostra['ID_Amostra']
    tipo_emm = amostra['Tipo_EMM']
    genes_raw = amostra['Perfil_Virulencia'].split(';')

    genes_traduzidos = []
    for gene in genes_raw:
        if gene in dicionario_vfdb:
            genes_traduzidos.append(f"- {gene}: {dicionario_vfdb[gene]}")

    lista_formatada = "\n".join(genes_traduzidos[:15]) + "\n... (lista truncada para sumarização)"

    prompt = f"""Atue como um analista de vigilância epidemiológica.

    DADOS DA AMOSTRA:
    - ID: {id_amostra}
    - Linhagem: {tipo_emm}
    - Fatores de virulência detetados (amostra de 15 genes):
    {lista_formatada}

    INSTRUÇÕES ESTRITAS:
    1. Baseie-se APENAS nos genes listados acima. Não invente genes não citados.
    2. Resuma em um parágrafo o perfil clínico esperado para a linhagem {tipo_emm}.
    3. Indique se os genes acima conferem risco de choque tóxico, adesão ou evasão imune.
    4. Inicie a resposta com uma das seguintes TAGS de alerta: [ALERTA VERMELHO], [ALERTA AMARELO] ou [PERFIL ENDÉMICO PADRÃO].

    LAUDO:"""

    print(f"\n[A processar amostra {id_amostra} - {tipo_emm}]\n")
    print("A gerar laudo (modo fluxo ao vivo):\n")
    print("-" * 50)

    try:
        for texto in llm.stream(prompt):
            print(texto, end="", flush=True)
        print("\n" + "-" * 50)
        print("\n[Processamento concluído]")
    except Exception as e:
        print(f"\nFalha na comunicação com o Llama: {e}")

if __name__ == "__main__":
    fasta_db = "../banco_dados/VFDB_S.pyogenes.fas"
    tsv_resultados = "../resultados_consolidados/epibuilder_metadata.tsv"

    print("A carregar base de conhecimento VFDB...")
    dict_vfdb = carregar_dicionario_vfdb(fasta_db)

    processar_amostra(tsv_resultados, dict_vfdb)
