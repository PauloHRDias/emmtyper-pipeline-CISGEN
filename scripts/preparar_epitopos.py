#!/usr/bin/env python3
"""Prepara a entrada de proteínas para a análise de epítopos no EpiBuilder.

O EpiBuilder/BepiPred-3 consome sequências proteicas. Esta ferramenta traduz
o FASTA nucleotídico do VFDB (S. pyogenes) para proteínas, mantendo apenas os
genes com tradução confiável, e grava um TSV de metadados de referência.

É uma análise complementar (vacinas/diagnóstico), separada da pipeline de
vigilância; não altera nenhum resultado genômico.
"""

import argparse
import csv
import re
from pathlib import Path

CODON = {}
BASES = "TCAG"
AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
for i, b1 in enumerate(BASES):
    for j, b2 in enumerate(BASES):
        for k, b3 in enumerate(BASES):
            CODON[b1 + b2 + b3] = AAS[i * 16 + j * 4 + k]


def cabecalho(header):
    cab = header[1:].strip()
    match_id = re.match(r"^(VFG\d+)", cab)
    vfg = match_id.group(1) if match_id else "VFG_UNKNOWN"
    match_gene = re.match(r"^VFG\d+(?:\([^)]*\))?\s+\(([^)]+)\)", cab)
    gene = match_gene.group(1) if match_gene else "sem_gene"
    match_prod = re.search(r"^\S+\s+\([^)]*\)\s+([^\[]+?)\s*\[", cab)
    produto = match_prod.group(1).strip() if match_prod else ""
    return vfg, gene, produto


def traduzir(seq):
    seq = re.sub(r"[^ACGTU]", "", seq.upper().replace("U", "T"))
    proteina = []
    for i in range(0, len(seq) - 2, 3):
        aa = CODON.get(seq[i:i + 3], "X")
        if aa == "*":
            break
        proteina.append(aa)
    return "".join(proteina)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="banco_dados/VFDB_S.pyogenes.fas")
    parser.add_argument("--saida", default="analises/epibuilder/VFDB_S_pyogenes_proteins.fasta")
    parser.add_argument("--min-aa", type=int, default=30, help="tamanho mínimo da proteína")
    args = parser.parse_args()

    entrada = Path(args.entrada)
    if not entrada.is_file():
        parser.error(f"FASTA não encontrado: {entrada}")

    sequences = {}
    header_atual = None
    for linha in entrada.read_text(encoding="utf-8", errors="replace").splitlines():
        linha = linha.strip()
        if linha.startswith(">"):
            header_atual = linha
            sequences[header_atual] = []
        elif header_atual and linha:
            sequences[header_atual].append(linha)

    fasta = []
    metadados = []
    ignoradas = 0
    for header, pedacos in sequences.items():
        vfg, gene, produto = cabecalho(header)
        proteina = traduzir("".join(pedacos))
        if len(proteina) < args.min_aa or proteina.count("X") > len(proteina) * 0.05:
            ignoradas += 1
            continue
        identificador = f"{vfg}_{re.sub(r'[^A-Za-z0-9]', '', gene) or 'sem_gene'}"
        fasta.append(f">{identificador}\n{proteina}\n")
        metadados.append({
            "ID_Proteina": identificador,
            "VFG": vfg,
            "Gene": gene,
            "Produto": produto,
            "Residuos": len(proteina),
        })

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("".join(fasta), encoding="utf-8")
    tsv = saida.with_name("proteins_metadata.tsv")
    with tsv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metadados[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(metadados)

    print(f"Proteínas geradas: {len(fasta)} (ignoradas: {ignoradas})")
    print(f"FASTA: {saida}")
    print(f"Metadados: {tsv}")


if __name__ == "__main__":
    main()
