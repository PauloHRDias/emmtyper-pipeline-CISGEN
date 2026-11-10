import argparse
import csv
import os
import re

# Formato esperado do emmtyper (workflow BLAST, saida "short"):
#   <amostra>.tmp\t<n_hits>\tEMM1.0\tEMM166.1\tA-C3
EMM_RE = re.compile(r"^EMM\d+(?:\.\d+)?$", re.IGNORECASE)
VFG_RE = re.compile(r"VFG\d+")


def parse_emmtyper(caminho_emm):
    """Extrai o tipo emm da saida padrao bruta do emmtyper.

    Retorna None quando o ficheiro nao existe ou nenhum tipo emm e encontrado.
    """
    if not caminho_emm or not os.path.exists(caminho_emm):
        return None

    with open(caminho_emm, "r") as f:
        for linha in f:
            colunas = linha.rstrip("\n").split("\t")
            for coluna in colunas[1:]:
                valor = coluna.strip()
                if EMM_RE.match(valor):
                    return valor
    return None


def parse_vfdb(caminho_vfdb, min_pident=90.0, min_qcov=70.0):
    """Extrai os genes de virulencia (IDs VFG) aprovados pelos limiares.

    A query do blastn e o genoma inteiro, portanto `qcovhsp` nao serve para
    medir a cobertura do gene. Usamos a cobertura do sujeito:
        cobertura = length / slen * 100
    Quando `slen` nao esta disponivel, cai para `qcovhsp`.
    """
    genes_detectados = set()
    if not caminho_vfdb or not os.path.exists(caminho_vfdb):
        return []

    with open(caminho_vfdb, "r") as f:
        for linha in f:
            colunas = linha.rstrip("\n").split("\t")
            if len(colunas) < 3:
                continue

            sseqid = colunas[1]
            try:
                pident = float(colunas[2])
            except ValueError:
                continue

            length = float(colunas[3]) if len(colunas) > 3 else None
            if len(colunas) >= 6:
                # Formato novo: qseqid sseqid pident length slen qcovhsp
                slen = float(colunas[4])
                qcovhsp = float(colunas[5])
            elif len(colunas) == 5:
                # Formato antigo: qseqid sseqid pident length qcovhsp
                slen = None
                qcovhsp = float(colunas[4])
            else:
                slen = None
                qcovhsp = None

            if length is not None and slen and slen > 0:
                cobertura = length / slen * 100.0
            elif qcovhsp is not None:
                cobertura = qcovhsp
            else:
                cobertura = 100.0

            if pident >= min_pident and cobertura >= min_qcov:
                match = VFG_RE.search(sseqid)
                if match:
                    genes_detectados.add(match.group(0))

    return sorted(genes_detectados)


def carregar_tabela(caminho):
    """Le a tabela consolidada existente (se houver)."""
    if not os.path.isfile(caminho):
        return []
    with open(caminho, "r", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main():
    parser = argparse.ArgumentParser(
        description="Gera/atualiza a tabela de metadados para o EpiBuilder"
    )
    parser.add_argument("--id", required=True, help="ID da Amostra")
    parser.add_argument("--emm", required=True, help="Caminho para o resumo do emmtyper")
    parser.add_argument("--vfdb", required=True, help="Caminho para o resultado tabular do blastn")
    parser.add_argument("--out", required=True, help="Caminho do ficheiro de saida para o EpiBuilder")
    parser.add_argument("--min-pident", type=float, default=90.0,
                        help="Identidade minima (%%), padrao: 90")
    parser.add_argument("--min-qcov", type=float, default=70.0,
                        help="Cobertura minima do sujeito (%%), padrao: 70")

    args = parser.parse_args()

    emm_type = parse_emmtyper(args.emm) or "Desconhecido"
    fatores_vir = parse_vfdb(args.vfdb, args.min_pident, args.min_qcov)
    str_virulencia = ";".join(fatores_vir) if fatores_vir else "Nenhum"

    cabecalho = ["ID_Amostra", "Tipo_EMM", "Perfil_Virulencia"]
    nova_linha = {
        "ID_Amostra": args.id,
        "Tipo_EMM": emm_type,
        "Perfil_Virulencia": str_virulencia,
    }

    # Upsert: substitui a linha da mesma amostra em vez de duplicar.
    linhas = carregar_tabela(args.out)
    linhas = [linha for linha in linhas if linha.get("ID_Amostra") != args.id]
    linhas.append(nova_linha)

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho, delimiter="\t")
        writer.writeheader()
        writer.writerows(linhas)

    print(f"[{args.id}] Adicionado/atualizado com sucesso em {args.out}")


if __name__ == "__main__":
    main()
