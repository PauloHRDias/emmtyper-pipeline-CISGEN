#!/usr/bin/env python3
"""QC basico de assemblies FASTA para vigilancia de S. pyogenes.

Calcula metricas de montagem (contigs, tamanho total, N50, GC, Ns) e
sinaliza valores fora do esperado para S. pyogenes. Nao bloqueia o
pipeline por defeito; use --strict para falhar em casos criticos.
"""

import argparse
import glob
import os
import sys


def ler_fasta(caminho):
    """Le um FASTA e devolve [(nome_contig, sequencia)]."""
    sequencias = []
    nome = None
    partes = []

    with open(caminho, "r") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith(">"):
                if nome is not None:
                    sequencias.append((nome, "".join(partes)))
                nome = linha[1:].split()[0] if len(linha) > 1 else "contig"
                partes = []
            else:
                partes.append(linha.upper())

    if nome is not None:
        sequencias.append((nome, "".join(partes)))
    return sequencias


def calcular_n50(tamanhos):
    if not tamanhos:
        return 0
    total = sum(tamanhos)
    acumulado = 0
    for tamanho in sorted(tamanhos, reverse=True):
        acumulado += tamanho
        if acumulado >= total / 2:
            return tamanho
    return 0


def avaliar(metricas, min_total, max_total, max_contigs, max_ns_pct,
            min_gc, max_gc):
    observacoes = []
    critico = False

    if metricas["Comprimento_Total"] < min_total:
        observacoes.append(
            f"comprimento total abaixo de {min_total} pb"
        )
        critico = True
    if metricas["Comprimento_Total"] > max_total:
        observacoes.append(
            f"comprimento total acima de {max_total} pb"
        )
    if metricas["Contigs"] > max_contigs:
        observacoes.append(f"mais de {max_contigs} contigs")
        critico = True
    if metricas["Ns_pct"] > max_ns_pct:
        observacoes.append(f"Ns acima de {max_ns_pct}%")
        critico = True
    if not (min_gc <= metricas["GC_pct"] <= max_gc):
        observacoes.append(
            f"GC fora da faixa {min_gc}-{max_gc}%"
        )

    if critico:
        metricas["Status"] = "FALHA"
    elif observacoes:
        metricas["Status"] = "ATENCAO"
    else:
        metricas["Status"] = "OK"

    metricas["Observacoes"] = "; ".join(observacoes) if observacoes else "-"
    return metricas


def analisar(caminho, args):
    sequencias = ler_fasta(caminho)
    tamanhos = [len(seq) for _, seq in sequencias]
    total = sum(tamanhos)
    gc = sum(seq.count("G") + seq.count("C") for _, seq in sequencias)
    ns = sum(seq.count("N") for _, seq in sequencias)

    metricas = {
        "ID_Amostra": os.path.basename(caminho).split(".")[0],
        "Ficheiro": os.path.basename(caminho),
        "Contigs": len(tamanhos),
        "Comprimento_Total": total,
        "N50": calcular_n50(tamanhos),
        "Maior_Contig": max(tamanhos) if tamanhos else 0,
        "Menor_Contig": min(tamanhos) if tamanhos else 0,
        "GC_pct": round(gc / total * 100, 2) if total else 0.0,
        "Ns": ns,
        "Ns_pct": round(ns / total * 100, 4) if total else 0.0,
    }
    return avaliar(
        metricas,
        args.min_total_length,
        args.max_total_length,
        args.max_contigs,
        args.max_ns_pct,
        args.min_gc,
        args.max_gc,
    )


def main():
    parser = argparse.ArgumentParser(
        description="QC basico de assemblies FASTA de S. pyogenes"
    )
    parser.add_argument(
        "fasta", nargs="*",
        help="Ficheiros FASTA. Se omitido, usa --entrada-dir.",
    )
    parser.add_argument(
        "--entrada-dir", default="entrada",
        help="Pasta com assemblies .fna (padrao: entrada)",
    )
    parser.add_argument(
        "--saida", default="resultados_consolidados/qc_montagem.tsv",
        help="TSV de saida",
    )
    parser.add_argument("--min-total-length", type=int, default=1_500_000,
                        help="Comprimento minimo esperado (padrao: 1500000)")
    parser.add_argument("--max-total-length", type=int, default=2_500_000,
                        help="Comprimento maximo esperado (padrao: 2500000)")
    parser.add_argument("--max-contigs", type=int, default=500,
                        help="Numero maximo de contigs (padrao: 500)")
    parser.add_argument("--max-ns-pct", type=float, default=1.0,
                        help="Percentagem maxima de Ns (padrao: 1.0)")
    parser.add_argument("--min-gc", type=float, default=35.0,
                        help="GC minimo esperado (padrao: 35.0)")
    parser.add_argument("--max-gc", type=float, default=42.0,
                        help="GC maximo esperado (padrao: 42.0)")
    parser.add_argument("--strict", action="store_true",
                        help="Sai com codigo 1 se alguma amostra tiver FALHA")
    args = parser.parse_args()

    ficheiros = list(args.fasta)
    if not ficheiros:
        ficheiros = sorted(glob.glob(os.path.join(args.entrada_dir, "*.fna")))

    if not ficheiros:
        print("Erro: nenhum FASTA encontrado.", file=sys.stderr)
        return 1

    resultados = [analisar(caminho, args) for caminho in ficheiros]

    colunas = [
        "ID_Amostra", "Ficheiro", "Contigs", "Comprimento_Total", "N50",
        "Maior_Contig", "Menor_Contig", "GC_pct", "Ns", "Ns_pct",
        "Status", "Observacoes",
    ]

    os.makedirs(os.path.dirname(args.saida) or ".", exist_ok=True)
    with open(args.saida, "w", newline="") as f:
        writer = __import__("csv").DictWriter(
            f, fieldnames=colunas, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(resultados)

    print(f"QC de montagem: {args.saida}")
    print(f"Amostras avaliadas: {len(resultados)}")
    for r in resultados:
        print(
            f"  - {r['ID_Amostra']}: {r['Status']} | "
            f"{r['Contigs']} contigs | {r['Comprimento_Total']} pb | "
            f"N50={r['N50']} | GC={r['GC_pct']}% | Ns={r['Ns']}"
        )
        if r["Observacoes"] != "-":
            print(f"      {r['Observacoes']}")

    if args.strict and any(r["Status"] == "FALHA" for r in resultados):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
