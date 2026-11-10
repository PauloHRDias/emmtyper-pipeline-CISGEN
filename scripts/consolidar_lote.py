import os
import glob
import pandas as pd

def consolidar():
    pasta_resultados = os.path.expanduser("~/teste_emmtyper/resultados_blast")
    pasta_saida = os.path.expanduser("~/teste_emmtyper/resultados_consolidados")
    os.makedirs(pasta_saida, exist_ok=True)

    dados = []

    # Procura por todos os ficheiros de log ou resultados gerados
    logs = glob.glob(os.path.join(pasta_resultados, "*_blast.stdout.log"))

    if not logs:
        print("Nenhum log encontrado em resultados_blast/.")
        return

    print(f"A consolidar dados de {len(logs)} amostras...")

    for log_path in logs:
        nome_base = os.path.basename(log_path).replace("_blast.stdout.log", "")

        # Tenta extrair o tipo emm do log ou define um valor padrão baseado no nome
        tipo_emm = "EMM_Desconhecido"
        try:
            with open(log_path, 'r') as f:
                for linha in f:
                    if "emm" in linha.lower():
                        partes = linha.strip().split()
                        if len(partes) > 1:
                            tipo_emm = partes[1]
                            break
        except:
            pass

        if tipo_emm == "EMM_Desconhecido":
            tipo_emm = f"Linhagem_{nome_base[:10]}"

        # LIMITAÇÃO CONHECIDA (Fase 0): o perfil de virulência abaixo é
        # SIMULADO/hardcoded, apenas para testar o fluxo dos laudos.
        # A substituição pelo perfil real (parse do blastn contra o VFDB)
        # será implementada na Fase 1. NÃO usar para laudos definitivos.
        perfil_virulencia = "VFG0387:mga; VFG0388:scpA; VFG0389:sfbI; VFG0390:speA; VFG0391:sdaB"

        dados.append({
            'ID_Amostra': nome_base,
            'Tipo_EMM': tipo_emm,
            'Perfil_Virulencia': perfil_virulencia
        })

    df_final = pd.DataFrame(dados)
    caminho_tsv = os.path.join(pasta_saida, "epibuilder_metadata.tsv")
    df_final.to_csv(caminho_tsv, sep='\t', index=False)
    print(f"Ficheiro consolidado gerado com sucesso em: {caminho_tsv}")
    print(f"Total de amostras na tabela: {len(df_final)}")

if __name__ == "__main__":
    consolidar()
