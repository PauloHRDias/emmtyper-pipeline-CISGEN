import argparse
import csv
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepara_epibuilder import parse_emmtyper, parse_vfdb


def encontrar_log_emm(id_amostra, pasta_blast):
    """Procura o log de tipagem emm da amostra, incluindo nomes antigos."""
    candidatos = [
        os.path.join(pasta_blast, f"{id_amostra}_emm.stdout.log"),
        os.path.join(pasta_blast, f"{id_amostra}_blast.stdout.log"),
    ]
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho

    # Compatibilidade com logs antigos: <nome_completo>_blast.stdout.log
    antigos = sorted(glob.glob(os.path.join(pasta_blast, f"{id_amostra}*_blast.stdout.log")))
    return antigos[0] if antigos else None


def consolidar(entrada_dir, resultados_blast, resultados_vfdb, saida,
               min_pident=90.0, min_qcov=70.0):
    genomas = sorted(glob.glob(os.path.join(entrada_dir, "*.fna")))
    if not genomas:
        print(f"Erro: nenhum assembly .fna encontrado em {entrada_dir}", file=sys.stderr)
        return 1

    dados = []
    vistos = set()

    for genoma in genomas:
        id_amostra = os.path.basename(genoma).split(".")[0]
        if id_amostra in vistos:
            continue
        vistos.add(id_amostra)

        log_emm = encontrar_log_emm(id_amostra, resultados_blast)
        arq_vfdb = os.path.join(resultados_vfdb, f"{id_amostra}_vfdb.tsv")

        if not log_emm and not os.path.isfile(arq_vfdb):
            tipo_emm = "NAO_PROCESSADO"
            perfil = "Nenhum"
            print(f"AVISO: sem resultados para {id_amostra}", file=sys.stderr)
        else:
            tipo_emm = parse_emmtyper(log_emm) if log_emm else None
            genes = parse_vfdb(arq_vfdb, min_pident, min_qcov) if os.path.isfile(arq_vfdb) else []

            if tipo_emm is None and not genes:
                # Sem gene emm e sem fatores de virulencia de S. pyogenes:
                # a amostra nao e compativel com S. pyogenes (controle negativo).
                tipo_emm = "NAO_S_PYOGENES"
                perfil = "Nenhum"
            else:
                tipo_emm = tipo_emm or "Desconhecido"
                perfil = ";".join(genes) if genes else "Nenhum"

        dados.append({
            "ID_Amostra": id_amostra,
            "Tipo_EMM": tipo_emm,
            "Perfil_Virulencia": perfil,
        })

    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    cabecalho = ["ID_Amostra", "Tipo_EMM", "Perfil_Virulencia"]
    with open(saida, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho, delimiter="\t")
        writer.writeheader()
        writer.writerows(dados)

    print(f"Tabela consolidada: {saida}")
    print(f"Amostras na tabela: {len(dados)}")
    print(f"Limiares VFDB: pident >= {min_pident}% | cobertura >= {min_qcov}%")
    for linha in dados:
        n_genes = 0 if linha["Perfil_Virulencia"] == "Nenhum" else len(linha["Perfil_Virulencia"].split(";"))
        print(f"  - {linha['ID_Amostra']}: emm={linha['Tipo_EMM']} | genes={n_genes}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Consolida resultados reais de emm e virulencia (VFDB) em uma tabela unica"
    )
    parser.add_argument("--entrada-dir", default="entrada",
                        help="Pasta com os assemblies .fna (padrao: entrada)")
    parser.add_argument("--resultados-blast", default="resultados_blast",
                        help="Pasta com os logs do emmtyper (padrao: resultados_blast)")
    parser.add_argument("--resultados-vfdb", default="resultados_consolidados",
                        help="Pasta com os TSV do blastn VFDB (padrao: resultados_consolidados)")
    parser.add_argument("--saida", default="resultados_consolidados/epibuilder_metadata.tsv",
                        help="Caminho da tabela consolidada")
    parser.add_argument("--min-pident", type=float, default=90.0,
                        help="Identidade minima (%%), padrao: 90")
    parser.add_argument("--min-qcov", type=float, default=70.0,
                        help="Cobertura minima do sujeito (%%), padrao: 70")
    args = parser.parse_args()

    sys.exit(consolidar(
        args.entrada_dir,
        args.resultados_blast,
        args.resultados_vfdb,
        args.saida,
        args.min_pident,
        args.min_qcov,
    ))


if __name__ == "__main__":
    main()
