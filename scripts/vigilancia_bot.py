import pandas as pd
from langchain_ollama import OllamaLLM
import sys
import os
import re
import time

MODELO_OLLAMA = os.environ.get("OLLAMA_MODELO", "llama3:8b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "160"))
NUM_THREAD = int(os.environ.get("OLLAMA_NUM_THREAD", "16"))
LAUDO_MAX_GENES = int(os.environ.get("LAUDO_MAX_GENES", "24"))
LAUDO_MAX_GENES_CATEGORIA = int(os.environ.get("LAUDO_MAX_GENES_CATEGORIA", "4"))

VFG_RE = re.compile(r"VFG\d+")
CATEGORIA_RE = re.compile(r"\[[^\]]*?-\s*([^\[\]()]+?)\s*\(VFC\d+\)\]")
SIMBOLO_RE = re.compile(r"^\(([^()]+)\)")
ACESSO_RE = re.compile(r"^(gb|ref|emb|dbj|sp|tr)\|")


def _limpar_descricao(descricao):
    """Remove o bracket final com a espécie de origem."""
    return re.sub(r"\s*\[Streptococcus[^\]]*\]\s*$", "", descricao).strip()


def extrair_categoria(descricao):
    """Extrai a categoria funcional do VFDB, ex.: Adherence, Exotoxin."""
    if not descricao:
        return "Outros"

    match = CATEGORIA_RE.search(descricao)
    if match:
        return match.group(1).strip()

    # Fallback: usa o último bracket, removendo códigos VF/VFC.
    brackets = re.findall(r"\[([^\]]+)\]", descricao)
    if brackets:
        categoria = re.sub(r"\s*\(V[FC]\d+\).*", "", brackets[-1]).strip()
        if categoria:
            return categoria

    return "Outros"


def extrair_simbolo(descricao):
    """Extrai o símbolo curto do gene, ex.: speB, emm, slo."""
    if not descricao:
        return None

    for br in re.findall(r"\(([^()]+)\)", descricao):
        br = br.strip()
        if ACESSO_RE.match(br) or re.match(r"^V[FC]\d+$", br):
            continue
        if br:
            return br
    return None


def carregar_dicionario_vfdb(caminho_fasta):
    """Lê o FASTA do VFDB e cria um dicionário: {ID_Gene: Descrição}

    O ID é normalizado para ``VFG\\d+`` porque alguns cabeçalhos trazem
    acessos entre parênteses (ex.: ``VFG000949(gb|WP_...)``).
    """
    banco_virulencia = {}
    try:
        with open(caminho_fasta, 'r') as fasta:
            for linha in fasta:
                if not linha.startswith('>'):
                    continue

                cabecalho = linha[1:].strip()
                match = VFG_RE.match(cabecalho)
                if not match:
                    continue

                vfg_id = match.group(0)
                descricao = _limpar_descricao(cabecalho[len(vfg_id):].strip())
                banco_virulencia[vfg_id] = descricao
    except FileNotFoundError:
        print(f"Erro: Ficheiro VFDB não encontrado em {caminho_fasta}")
        sys.exit(1)
    return banco_virulencia


def agrupar_por_categoria(genes_raw, dicionario_vfdb):
    """Agrupa os genes detetados pela categoria funcional do VFDB."""
    grupos = {}
    for gene in genes_raw:
        gene_limpo = gene.strip()
        if not gene_limpo:
            continue

        descricao = dicionario_vfdb.get(gene_limpo, "")
        categoria = extrair_categoria(descricao)
        grupos.setdefault(categoria, []).append((gene_limpo, descricao))

    return grupos


def _selecionar_exemplos(itens, maximo):
    """Prefere genes com símbolo reconhecível e evita símbolos repetidos."""
    escolhidos = []
    vistos = set()

    ordenados = sorted(
        itens,
        key=lambda item: (0 if extrair_simbolo(item[1]) else 1, item[0]),
    )
    for gene, descricao in ordenados:
        simbolo = extrair_simbolo(descricao) or gene
        chave = simbolo.lower()
        if chave in vistos:
            continue

        vistos.add(chave)
        escolhidos.append((gene, descricao))
        if len(escolhidos) >= maximo:
            break

    return escolhidos


def formatar_perfil(grupos, max_total=LAUDO_MAX_GENES,
                    max_por_categoria=LAUDO_MAX_GENES_CATEGORIA):
    """Resume o perfil por categoria, com poucos genes de exemplo.

    Listar 200+ genes torna o prompt enorme e a inferência em CPU lenta.
    O laudo precisa apenas dos mecanismos e de alguns exemplos.
    """
    linhas = []
    restante = max_total

    categorias = sorted(grupos.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for categoria, itens in categorias:
        if restante <= 0:
            break

        n_exemplos = min(max_por_categoria, len(itens), restante)
        exemplos = _selecionar_exemplos(itens, n_exemplos)
        nomes = [
            extrair_simbolo(descricao) or gene
            for gene, descricao in exemplos
        ]
        linhas.append(
            f"- {categoria}: {len(itens)} gene(s) — ex.: {', '.join(nomes)}"
        )
        restante -= n_exemplos

    return "\n".join(linhas)


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
    llm = OllamaLLM(
        model=MODELO_OLLAMA,
        base_url=OLLAMA_URL,
        temperature=0.0,
        num_predict=NUM_PREDICT,
        num_thread=NUM_THREAD,
        num_ctx=2048,
    )

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

        # Amostras que nao sao S. pyogenes (ou sem resultado) nao recebem laudo clinico.
        if tipo_emm in ('NAO_S_PYOGENES', 'NAO_PROCESSADO'):
            print("\n" + "=" * 70)
            print(f"AMOSTRA ({amostra_atual}/{total_amostras}): {id_amostra}")
            print(f"Progresso: [ {percentual:.1f}% ] | Tempo decorrido: {tempo_decorrido:.2f} minutos")
            if tipo_emm == 'NAO_S_PYOGENES':
                print("Disposicao: NAO COMPATIVEL COM S. pyogenes (controle negativo). Laudo clinico nao aplicavel.")
            else:
                print("Disposicao: SEM RESULTADO DE TIPAGEM. Verifique os logs da amostra.")
            print("=" * 70 + "\n")
            continue

        genes_raw = [] if perfil_raw in ('', 'nan', 'Nenhum', 'None') else perfil_raw.split(';')

        grupos = agrupar_por_categoria(genes_raw, dicionario_vfdb)
        total_genes = sum(len(itens) for itens in grupos.values())
        perfil_formatado = formatar_perfil(grupos)
        if not perfil_formatado:
            perfil_formatado = "Nenhum fator de virulência mapeado."

        prompt = f"""Atue como analista de vigilância epidemiológica molecular.
Responda em português de Portugal, em texto corrido.

DADOS DA AMOSTRA:
- ID: {id_amostra}
- Linhagem emm: {tipo_emm}
- Total de fatores de virulência detetados: {total_genes}

PERFIL POR CATEGORIA (exemplos representativos):
{perfil_formatado}

INSTRUÇÕES ESTRITAS:
1. Baseie-se APENAS nos dados acima. Não invente genes nem funções.
2. Escreva no máximo 100 palavras, num único parágrafo.
3. Mencione os mecanismos patogénicos presentes (adesão, evasão imune, toxinas, enzimas), citando 2 a 4 genes da lista como exemplo.
4. Inicie a resposta obrigatoriamente com uma destas TAGS:
   - [ALERTA VERMELHO] (se houver toxinas superantigénicas ou de choque tóxico).
   - [ALERTA AMARELO] (se houver evasão imune/adesão sem toxinas severas).
   - [PERFIL ENDÉMICO PADRÃO] (risco basal).

LAUDO:"""

        # 5. Painel de controlo visual da amostra atual
        print("\n" + "=" * 70)
        print(f"PROCESSANDO AMOSTRA ({amostra_atual}/{total_amostras}): {id_amostra} | Linhagem: {tipo_emm}")
        print(f"Progresso: [ {percentual:.1f}% ] | Tempo decorrido: {tempo_decorrido:.2f} minutos")
        print(f"Genes no perfil: {total_genes} | Categorias: {len(grupos)}")
        print("=" * 70)

        inicio_amostra = time.time()
        try:
            resposta = llm.invoke(prompt)
            print(resposta)
        except Exception as e:
            print(f"\nFalha na comunicação com o Llama para a amostra {id_amostra}: {e}")
        else:
            duracao = time.time() - inicio_amostra
            print(f"\n[Tempo da amostra: {duracao / 60:.2f} minutos]")

        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Caminhos resolvidos a partir da raiz do projeto (independente do cwd)
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fasta_db = os.path.join(raiz_projeto, "banco_dados", "VFDB_S.pyogenes.fas")
    tsv_resultados = os.path.join(raiz_projeto, "resultados_consolidados", "epibuilder_metadata.tsv")

    print("A carregar base de conhecimento VFDB...")
    dict_vfdb = carregar_dicionario_vfdb(fasta_db)

    processar_lote_amostras(tsv_resultados, dict_vfdb)
