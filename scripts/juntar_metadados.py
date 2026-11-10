#!/usr/bin/env python3
"""Junta a tabela genomica com metadados clinico-epidemiologicos e QC.

A tabela genomica (ID_Amostra, Tipo_EMM, Perfil_Virulencia) e a fonte
primaria. Os metadados e o QC sao acrescentados por ID_Amostra. Amostras
sem metadados recebem "NA"; metadados sem genoma sao apenas reportados.
"""

import argparse
import csv
import os
import sys

ID_CANDIDATOS = ["ID_Amostra", "ID", "Amostra", "Sample", "sample_id"]


def ler_tabela(caminho):
    """Le CSV/TSV e devolve (linhas, colunas)."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(caminho)

    extensao = os.path.splitext(caminho)[1].lower()
    delimitador = "," if extensao == ".csv" else "\t"

    with open(caminho, "r", newline="") as f:
        leitor = csv.DictReader(f, delimiter=delimitador)
        linhas = list(leitor)
        colunas = list(leitor.fieldnames or [])

    # Fallback para CSV com separador alternativo.
    if len(colunas) == 1 and "\t" not in colunas[0]:
        with open(caminho, "r", newline="") as f:
            leitor = csv.DictReader(f, delimiter=",")
            linhas = list(leitor)
            colunas = list(leitor.fieldnames or [])

    return linhas, colunas


def detectar_coluna_id(colunas, preferida):
    if preferida in colunas:
        return preferida
    for candidato in ID_CANDIDATOS:
        if candidato in colunas:
            return candidato
    return None


def indexar_por_id(linhas, coluna_id, origem):
    indice = {}
    duplicados = []
    for linha in linhas:
        chave = (linha.get(coluna_id) or "").strip()
        if not chave:
            continue
        if chave in indice:
            duplicados.append(chave)
        else:
            indice[chave] = linha

    if duplicados:
        print(
            f"AVISO: {len(set(duplicados))} ID(s) duplicado(s) em {origem}: "
            + ", ".join(sorted(set(duplicados))[:10]),
            file=sys.stderr,
        )
    return indice


def main():
    parser = argparse.ArgumentParser(
        description="Junta tabela genomica, QC e metadados por ID_Amostra"
    )
    parser.add_argument(
        "--genomico", default="resultados_consolidados/epibuilder_metadata.tsv",
        help="Tabela genomica consolidada",
    )
    parser.add_argument(
        "--metadados", required=True,
        help="CSV/TSV com metadados clinico-epidemiologicos",
    )
    parser.add_argument(
        "--qc", default="resultados_consolidados/qc_montagem.tsv",
        help="TSV de QC de montagem (opcional)",
    )
    parser.add_argument(
        "--saida", default="resultados_consolidados/epibuilder_completo.tsv",
        help="TSV final",
    )
    parser.add_argument(
        "--id-col", default="ID_Amostra",
        help="Nome da coluna de ID nos metadados (padrao: ID_Amostra)",
    )
    args = parser.parse_args()

    try:
        genomico, colunas_gen = ler_tabela(args.genomico)
    except FileNotFoundError:
        print(f"Erro: tabela genomica nao encontrada: {args.genomico}",
              file=sys.stderr)
        return 1

    if not genomico:
        print("Erro: tabela genomica vazia.", file=sys.stderr)
        return 1

    coluna_gen = detectar_coluna_id(colunas_gen, "ID_Amostra")
    if not coluna_gen:
        print("Erro: tabela genomica sem coluna de ID reconhecida.",
              file=sys.stderr)
        return 1

    try:
        metadados, colunas_meta = ler_tabela(args.metadados)
    except FileNotFoundError:
        print(f"Erro: metadados nao encontrados: {args.metadados}",
              file=sys.stderr)
        return 1

    coluna_meta = detectar_coluna_id(colunas_meta, args.id_col)
    if not coluna_meta:
        print(
            "Erro: metadados sem coluna de ID. "
            f"Colunas disponiveis: {', '.join(colunas_meta)}",
            file=sys.stderr,
        )
        return 1

    indice_meta = indexar_por_id(metadados, coluna_meta, args.metadados)

    qc_por_id = {}
    colunas_qc = []
    if args.qc and os.path.isfile(args.qc):
        qc, colunas_qc = ler_tabela(args.qc)
        coluna_qc = detectar_coluna_id(colunas_qc, "ID_Amostra")
        if coluna_qc:
            qc_por_id = indexar_por_id(qc, coluna_qc, args.qc)
            colunas_qc = [c for c in colunas_qc if c != coluna_qc]
        else:
            print(f"AVISO: QC sem coluna de ID: {args.qc}", file=sys.stderr)
            colunas_qc = []

    # Evita colunas duplicadas entre genomico, QC e metadados.
    usadas = set(colunas_gen)
    colunas_qc_final = []
    for coluna in colunas_qc:
        if coluna in usadas:
            continue
        usadas.add(coluna)
        colunas_qc_final.append(coluna)

    colunas_meta_final = []
    for coluna in colunas_meta:
        if coluna == coluna_meta:
            continue
        nome = coluna
        if nome in usadas:
            nome = f"Meta_{nome}"
        while nome in usadas:
            nome = f"Meta_{nome}"
        usadas.add(nome)
        colunas_meta_final.append((coluna, nome))

    colunas_saida = colunas_gen + colunas_qc_final + [
        nome for _, nome in colunas_meta_final
    ]

    linhas_saida = []
    ids_genomicos = set()
    ids_com_meta = set()

    for linha in genomico:
        chave = (linha.get(coluna_gen) or "").strip()
        ids_genomicos.add(chave)
        nova = dict(linha)

        qc = qc_por_id.get(chave, {})
        for coluna in colunas_qc_final:
            nova[coluna] = qc.get(coluna, "NA")

        meta = indice_meta.get(chave, {})
        if meta:
            ids_com_meta.add(chave)
        for coluna_original, coluna_saida in colunas_meta_final:
            valor = meta.get(coluna_original, "NA")
            nova[coluna_saida] = valor if valor not in (None, "") else "NA"

        linhas_saida.append(nova)

    os.makedirs(os.path.dirname(args.saida) or ".", exist_ok=True)
    with open(args.saida, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=colunas_saida, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(linhas_saida)

    sem_meta = sorted(ids_genomicos - ids_com_meta)
    meta_sem_genoma = sorted(set(indice_meta) - ids_genomicos)

    print(f"Tabela final: {args.saida}")
    print(f"Amostras genomicas: {len(genomico)}")
    print(f"Metadados: {len(metadados)}")
    print(f"Com metadados: {len(ids_com_meta)}")
    print(f"Sem metadados: {len(sem_meta)}")
    if sem_meta:
        print("  " + ", ".join(sem_meta[:20]))
    if meta_sem_genoma:
        print(f"Metadados sem genoma: {len(meta_sem_genoma)}")
        print("  " + ", ".join(meta_sem_genoma[:20]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
