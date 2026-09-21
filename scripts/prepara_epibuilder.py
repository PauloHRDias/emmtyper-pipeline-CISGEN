import argparse
import csv
import os

def parse_emmtyper(caminho_emm):
    """Extrai o tipo emm da saída padrão bruta do emmtyper."""
    with open(caminho_emm, 'r') as f:
        for linha in f:
            colunas = linha.strip().split('\t')
            if len(colunas) >= 3 and '.tmp' in colunas[0]:
                return colunas[2]
    return "Desconhecido"

def parse_vfdb(caminho_vfdb, min_pident=90.0):
    """Extrai os genes de virulência com base na identidade mínima."""
    genes_detectados = set()
    if not os.path.exists(caminho_vfdb):
        return []

    with open(caminho_vfdb, 'r') as f:
        for linha in f:
            colunas = linha.strip().split('\t')
            if len(colunas) >= 3:
                gene_id = colunas[1]
                pident = float(colunas[2])

                # Se atingir a identidade mínima, considera o gene detectado
                if pident >= min_pident:
                    if '(' in gene_id and ')' in gene_id:
                        nome_gene = gene_id.split('(')[0]
                    else:
                        nome_gene = gene_id
                    genes_detectados.add(nome_gene)

    return sorted(list(genes_detectados))

def main():
    parser = argparse.ArgumentParser(description="Gera tabela de metadados para o EpiBuilder")
    parser.add_argument("--id", required=True, help="ID da Amostra")
    parser.add_argument("--emm", required=True, help="Caminho para o resumo do emmtyper")
    parser.add_argument("--vfdb", required=True, help="Caminho para o resultado tabular do blastn")
    parser.add_argument("--out", required=True, help="Caminho do ficheiro de saída para o EpiBuilder")

    args = parser.parse_args()

    emm_type = parse_emmtyper(args.emm)
    fatores_vir = parse_vfdb(args.vfdb)
    str_virulencia = ";".join(fatores_vir) if fatores_vir else "Nenhum"

    cabecalho = ["ID_Amostra", "Tipo_EMM", "Perfil_Virulencia"]
    linha_dados = [args.id, emm_type, str_virulencia]

    arquivo_existe = os.path.isfile(args.out)

    with open(args.out, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        if not arquivo_existe:
            writer.writerow(cabecalho)
        writer.writerow(linha_dados)

    print(f"[{args.id}] Adicionado com sucesso a {args.out}")

if __name__ == "__main__":
    main()
