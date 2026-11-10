import pandas as pd
from langchain_ollama import OllamaLLM
import sys
import os
import time

MODELO_OLLAMA = "llama3:8b"


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


def processar_lote_amostras(caminho_tsv, dicionario_vfdb):
    """Lê o TSV consolidado, faz o loop por todas as amostras e gera os laudos via Llama 3"""
    try:
        df = pd.read_csv(caminho_tsv, sep='\t')
    except Exception as e:
        print(f"Erro ao ler o TSV consolidado: {e}")
        print("Certifique-se de que o ficheiro de metadados do EpiBuilder existe no caminho especificado.")
        sys.exit(1)

    if df.empty:
        print(f"Erro: o TSV consolidado está vazio: {caminho_tsv}")
        sys.exit(1)

    print(f"Iniciando motor {MODELO_OLLAMA} via Docker (Temperatura=0.0)...")
    llm = OllamaLLM(model=MODELO_OLLAMA, base_url="http://localhost:11434", temperature=0.0)

    total_amostras = len(df)
    print(f"\n[Encontradas {total_amostras} estirpes para análise em lote]\n")

    # 1. Inicia o cronómetro ANTES do loop
    tempo_inicio = time.time()

    # 2. Loop por todas as amostras do DataFrame
    for index, amostra in df.iterrows():

        # 3. Matemática do progresso
        amostra_atual = index + 1
        percentual = (amostra_atual / total_amostras) * 100
        tempo_decorrido = (time.time() - tempo_inicio) / 60

        # 4. Extrai os dados da amostra atual
        id_amostra = amostra.get('ID_Amostra', f'Amostra_{amostra_atual}')
        tipo_emm = amostra.get('Tipo_EMM', 'Desconhecido')
        perfil_raw = str(amostra.get('Perfil_Virulencia', ''))

        genes_raw = perfil_raw.split(';') if perfil_raw and perfil_raw != 'nan' else []

        genes_traduzidos = []
        for gene in genes_raw:
            gene_limpo = gene.strip()
            if gene_limpo in dicionario_vfdb:
                genes_traduzidos.append(f"- {gene_limpo}: {dicionario_vfdb[gene_limpo]}")
            elif gene_limpo:
                genes_traduzidos.append(f"- {gene_limpo}: Função não descrita no índice VFDB local")

        lista_formatada = "\n".join(genes_traduzidos) if genes_traduzidos else "Nenhum fator de virulência mapeado."
        total_genes = len(genes_traduzidos)

        prompt = f"""Atue como um analista de vigilância epidemiológica.

        DADOS DA AMOSTRA:
        - ID: {id_amostra}
        - Linhagem: {tipo_emm}
        - Fatores de virulência detetados (Total de {total_genes} genes):
        {lista_formatada}

        INSTRUÇÕES ESTRITAS:
        1. Baseie-se APENAS nos genes listados acima. Não invente genes ou funções.
        2. Resuma em um parágrafo o perfil clínico esperado para a linhagem {tipo_emm}.
        3. Destaque os principais mecanismos patogénicos (ex: choque tóxico, adesão, evasão imune), citando genes específicos da lista como exemplo para justificar cada mecanismo encontrado.
        4. Inicie a resposta obrigatoriamente com uma destas TAGS:
           - [ALERTA VERMELHO] (se houver genes explícitos de toxinas superantigénicas ou choque tóxico).
           - [ALERTA AMARELO] (se houver perfil de evasão imune/adesão sem toxinas severas).
           - [PERFIL ENDÉMICO PADRÃO] (risco basal).

        LAUDO:"""

        # 5. Painel de controlo visual da amostra atual
        print("\n" + "=" * 70)
        print(f"PROCESSANDO AMOSTRA ({amostra_atual}/{total_amostras}): {id_amostra} | Linhagem: {tipo_emm}")
        print(f"Progresso: [ {percentual:.1f}% ] | Tempo decorrido: {tempo_decorrido:.2f} minutos")
        print("=" * 70)

        try:
            resposta = llm.invoke(prompt)
            print(resposta)
        except Exception as e:
            print(f"\nFalha na comunicação com o Llama para a amostra {id_amostra}: {e}")

        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Caminhos resolvidos a partir da raiz do projeto (independente do cwd)
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fasta_db = os.path.join(raiz_projeto, "banco_dados", "VFDB_S.pyogenes.fas")
    tsv_resultados = os.path.join(raiz_projeto, "resultados_consolidados", "epibuilder_metadata.tsv")

    print("A carregar base de conhecimento VFDB...")
    dict_vfdb = carregar_dicionario_vfdb(fasta_db)

    processar_lote_amostras(tsv_resultados, dict_vfdb)
