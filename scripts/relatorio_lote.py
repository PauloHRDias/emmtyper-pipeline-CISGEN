#!/usr/bin/env python3
"""Gera um relatorio resumido do lote de vigilancia de S. pyogenes.

Le a tabela consolidada (com ou sem metadados), o ficheiro de laudos e
produz um Markdown com distribuicao de tipos emm, fatores de virulencia,
alertas e agregacoes temporais/espaciais quando os metadados existem.
"""

import argparse
import csv
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime

CATEGORIA_RE = re.compile(r"\[[^\]]*?-\s*([^\[\]()]+?)\s*\(VFC\d+\)\]")
VFG_RE = re.compile(r"VFG\d+")

TAGS = {
    "[ALERTA VERMELHO]": "Alerta vermelho",
    "[ALERTA AMARELO]": "Alerta amarelo",
    "[PERFIL ENDÉMICO PADRÃO]": "Perfil endémico padrão",
}

COLUNAS_META = {
    "data": ["Data_Coleta", "Data", "data_coleta", "Collection_Date"],
    "municipio": ["Municipio", "Município", "Municipality", "Cidade"],
    "sitio": ["Sitio_Anatomico", "Sítio_Anatômico", "Sitio", "Site",
              "Sitio_Anatomico"],
    "desfecho": ["Desfecho", "Outcome", "Evolucao", "Evolução"],
}


def ler_tabela(caminho):
    extensao = os.path.splitext(caminho)[1].lower()
    delimitador = "," if extensao == ".csv" else "\t"
    with open(caminho, "r", newline="") as f:
        leitor = csv.DictReader(f, delimiter=delimitador)
        return list(leitor), list(leitor.fieldnames or [])


def encontrar_coluna(colunas, candidatos):
    for candidato in candidatos:
        if candidato in colunas:
            return candidato
    return None


def carregar_categorias_vfdb(caminho):
    """Mapeia VFG -> categoria funcional do VFDB."""
    categorias = {}
    if not caminho or not os.path.isfile(caminho):
        return categorias

    with open(caminho, "r") as f:
        for linha in f:
            if not linha.startswith(">"):
                continue
            cabecalho = linha[1:].strip()
            match = VFG_RE.match(cabecalho)
            if not match:
                continue
            descricao = cabecalho[len(match.group(0)):].strip()
            descricao = re.sub(
                r"\s*\[Streptococcus[^\]]*\]\s*$", "", descricao
            )
            cat = CATEGORIA_RE.search(descricao)
            categorias[match.group(0)] = (
                cat.group(1).strip() if cat else "Outros"
            )
    return categorias


def contar_alertas(caminho):
    contagem = Counter()
    if not caminho or not os.path.isfile(caminho):
        return contagem
    with open(caminho, "r", errors="replace") as f:
        for linha in f:
            limpa = linha.lstrip()
            for tag in TAGS:
                if limpa.startswith(tag):
                    contagem[tag] += 1
                    break
    return contagem


def parse_mes(valor):
    valor = (valor or "").strip()
    if not valor or valor.upper() == "NA":
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y",
                    "%Y-%m", "%m/%Y"):
        try:
            return datetime.strptime(valor, formato).strftime("%Y-%m")
        except ValueError:
            continue
    return None


def tabela_markdown(cabecalho, linhas):
    saida = ["| " + " | ".join(cabecalho) + " |"]
    saida.append("|" + "|".join(["---"] * len(cabecalho)) + "|")
    for linha in linhas:
        saida.append("| " + " | ".join(str(c) for c in linha) + " |")
    return "\n".join(saida)


def main():
    parser = argparse.ArgumentParser(
        description="Relatorio resumido do lote de vigilancia"
    )
    parser.add_argument(
        "--tabela", default="resultados_consolidados/epibuilder_completo.tsv",
        help="Tabela consolidada (com ou sem metadados)",
    )
    parser.add_argument(
        "--laudos", default="resultados_consolidados/laudos.txt",
        help="Ficheiro de laudos (opcional)",
    )
    parser.add_argument(
        "--vfdb", default="banco_dados/VFDB_S.pyogenes.fas",
        help="FASTA do VFDB para categorias funcionais",
    )
    parser.add_argument(
        "--saida", default="resultados_consolidados/relatorio_lote.md",
        help="Markdown de saida",
    )
    parser.add_argument("--top", type=int, default=10,
                        help="Numero de categorias/tipos no topo (padrao: 10)")
    args = parser.parse_args()

    if not os.path.isfile(args.tabela):
        print(f"Erro: tabela nao encontrada: {args.tabela}", file=sys.stderr)
        return 1

    linhas, colunas = ler_tabela(args.tabela)
    if not linhas:
        print("Erro: tabela vazia.", file=sys.stderr)
        return 1

    coluna_id = encontrar_coluna(colunas, ["ID_Amostra", "ID", "Amostra"])
    coluna_emm = encontrar_coluna(colunas, ["Tipo_EMM", "EMM", "emm"])
    coluna_vir = encontrar_coluna(
        colunas, ["Perfil_Virulencia", "Virulencia", "Virulence"]
    )
    if not coluna_id or not coluna_emm:
        print("Erro: tabela sem colunas ID_Amostra/Tipo_EMM.", file=sys.stderr)
        return 1

    total = len(linhas)
    tipos_emm = Counter()
    genes_por_amostra = []
    categorias_amostras = Counter()
    categorias_hits = Counter()

    mapa_categorias = carregar_categorias_vfdb(args.vfdb)

    for linha in linhas:
        emm = (linha.get(coluna_emm) or "Desconhecido").strip()
        tipos_emm[emm] += 1

        perfil = (linha.get(coluna_vir) or "").strip() if coluna_vir else ""
        genes = [] if perfil in ("", "Nenhum", "NA") else [
            g.strip() for g in perfil.split(";") if g.strip()
        ]
        genes_por_amostra.append(len(genes))

        categorias_amostra = set()
        for gene in genes:
            categoria = mapa_categorias.get(gene, "Outros")
            categorias_hits[categoria] += 1
            categorias_amostra.add(categoria)
        for categoria in categorias_amostra:
            categorias_amostras[categoria] += 1

    n_s_pyogenes = sum(
        1 for emm in tipos_emm.elements() if emm.upper().startswith("EMM")
    )
    n_nao_s = tipos_emm.get("NAO_S_PYOGENES", 0)
    n_nao_processado = tipos_emm.get("NAO_PROCESSADO", 0)

    alertas = contar_alertas(args.laudos)

    colunas_meta = {
        chave: encontrar_coluna(colunas, candidatos)
        for chave, candidatos in COLUNAS_META.items()
    }
    tem_meta = any(colunas_meta.values())

    agregados = {}
    if tem_meta:
        por_mes = Counter()
        por_municipio = Counter()
        por_sitio = Counter()
        por_desfecho = Counter()
        emm_por_municipio = defaultdict(Counter)

        for linha in linhas:
            emm = (linha.get(coluna_emm) or "Desconhecido").strip()
            if colunas_meta["data"]:
                mes = parse_mes(linha.get(colunas_meta["data"], ""))
                if mes:
                    por_mes[mes] += 1
            if colunas_meta["municipio"]:
                municipio = (linha.get(colunas_meta["municipio"]) or "").strip()
                if municipio and municipio.upper() != "NA":
                    por_municipio[municipio] += 1
                    emm_por_municipio[municipio][emm] += 1
            if colunas_meta["sitio"]:
                sitio = (linha.get(colunas_meta["sitio"]) or "").strip()
                if sitio and sitio.upper() != "NA":
                    por_sitio[sitio] += 1
            if colunas_meta["desfecho"]:
                desfecho = (linha.get(colunas_meta["desfecho"]) or "").strip()
                if desfecho and desfecho.upper() != "NA":
                    por_desfecho[desfecho] += 1

        agregados = {
            "mes": por_mes,
            "municipio": por_municipio,
            "sitio": por_sitio,
            "desfecho": por_desfecho,
            "emm_por_municipio": emm_por_municipio,
        }

    # ---- Montagem do Markdown ----
    md = [
        "# Relatório de lote — Vigilância de *Streptococcus pyogenes*",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Tabela de entrada: `{args.tabela}`",
        "",
        "## Resumo",
        "",
    ]

    resumo = [
        ["Amostras no lote", total],
        ["Com tipo emm (S. pyogenes)", n_s_pyogenes],
        ["NAO_S_PYOGENES", n_nao_s],
        ["NAO_PROCESSADO", n_nao_processado],
    ]
    if "Status" in colunas:
        status = Counter(
            (linha.get("Status") or "NA").strip() for linha in linhas
        )
        for chave, valor in sorted(status.items()):
            resumo.append([f"QC: {chave}", valor])
    md.append(tabela_markdown(["Métrica", "Valor"], resumo))
    md.append("")

    md += ["## Distribuição de tipos emm", ""]
    linhas_emm = [
        [emm, qtd, f"{qtd / total * 100:.1f}%"]
        for emm, qtd in tipos_emm.most_common(args.top)
    ]
    md.append(tabela_markdown(["Tipo emm", "Amostras", "%"], linhas_emm))
    md.append("")

    if genes_por_amostra:
        md += ["## Fatores de virulência", ""]
        stats = [
            ["Mínimo de genes por amostra", min(genes_por_amostra)],
            ["Mediana", statistics.median(genes_por_amostra)],
            ["Máximo", max(genes_por_amostra)],
        ]
        md.append(tabela_markdown(["Métrica", "Valor"], stats))
        md.append("")

        if categorias_amostras:
            md += ["### Principais categorias funcionais", ""]
            linhas_cat = [
                [cat, qtd, categorias_hits[cat]]
                for cat, qtd in categorias_amostras.most_common(args.top)
            ]
            md.append(tabela_markdown(
                ["Categoria VFDB", "Amostras com a categoria",
                 "Total de genes"],
                linhas_cat,
            ))
            md.append("")

    if alertas:
        md += ["## Alertas nos laudos", ""]
        linhas_alertas = [
            [TAGS[tag], alertas.get(tag, 0)] for tag in TAGS
        ]
        md.append(tabela_markdown(["Classificação", "Laudos"], linhas_alertas))
        md.append("")

    if tem_meta:
        md += ["## Agregação por metadados", ""]
        if agregados["mes"]:
            md += ["### Por mês de coleta", ""]
            md.append(tabela_markdown(
                ["Mês", "Amostras"],
                [[mes, qtd] for mes, qtd in sorted(agregados["mes"].items())],
            ))
            md.append("")
        if agregados["municipio"]:
            md += ["### Por município", ""]
            linhas_mun = []
            for municipio, qtd in agregados["municipio"].most_common(args.top):
                emm_top = ", ".join(
                    f"{emm} ({n})"
                    for emm, n in agregados["emm_por_municipio"][municipio].most_common(3)
                )
                linhas_mun.append([municipio, qtd, emm_top])
            md.append(tabela_markdown(
                ["Município", "Amostras", "Tipos emm predominantes"],
                linhas_mun,
            ))
            md.append("")
        if agregados["sitio"]:
            md += ["### Por sítio anatômico", ""]
            md.append(tabela_markdown(
                ["Sítio", "Amostras"],
                [[s, q] for s, q in agregados["sitio"].most_common(args.top)],
            ))
            md.append("")
        if agregados["desfecho"]:
            md += ["### Por desfecho clínico", ""]
            md.append(tabela_markdown(
                ["Desfecho", "Amostras"],
                [[d, q] for d, q in agregados["desfecho"].most_common(args.top)],
            ))
            md.append("")
    else:
        md += [
            "## Agregação por metadados",
            "",
            "Nenhuma coluna de metadados clínico-epidemiológicos foi encontrada "
            "na tabela. Use `scripts/juntar_metadados.py` para acrescentar "
            "`Data_Coleta`, `Municipio`, `Sitio_Anatomico` e `Desfecho`.",
            "",
        ]

    md += [
        "## Notas",
        "",
        "- Os tipos emm são obtidos pelo emmtyper (workflow BLAST).",
        "- Os genes de virulência são detectados por blastn contra o VFDB "
        "filtrado para *S. pyogenes*, com limiares de identidade e cobertura "
        "definidos em `config.sh`.",
        "- As classificações de alerta são calculadas de forma determinística "
        "a partir dos genes detetados; o modelo apenas redige o texto.",
        "- Amostras `NAO_S_PYOGENES` e `NAO_PROCESSADO` não recebem laudo "
        "clínico.",
        "",
    ]

    os.makedirs(os.path.dirname(args.saida) or ".", exist_ok=True)
    with open(args.saida, "w") as f:
        f.write("\n".join(md) + "\n")

    print(f"Relatorio: {args.saida}")
    print(f"Amostras: {total} | S. pyogenes: {n_s_pyogenes} | "
          f"NAO_S_PYOGENES: {n_nao_s} | NAO_PROCESSADO: {n_nao_processado}")
    if alertas:
        print("Alertas: " + ", ".join(
            f"{TAGS[tag]}={alertas.get(tag, 0)}" for tag in TAGS
        ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
