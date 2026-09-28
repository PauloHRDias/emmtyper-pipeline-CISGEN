import os

def construir_base_conheciemnto(caminho_fasta):
	banco_virulencia = {}

	with open(caminho_fasta, 'r') as fasta:
		for linha in fasta:
			if linha.startswith('>'):
				# Divide o cabeçalho: ID de um lado, Descrição do outro
				partes = linha.strip().split(' ', 1)
				vfg_id = partes[0].replace('>', '')

				if len(partes) > 1:
					# Isola a descrição útil descartando o "[Streptococcus pyogenes...]" no final
					descricao = partes[1].rsplit(' [Streptococcus', 1)[0]
				else:
					descricao = "Função não anotada"

				banco_virulencia[vfg_id] = descricao

	return banco_virulencia
# Execução de teste
if __name__ == "__main__":
   caminho = "../banco_dados/VFDB_S.pyogenes.fas"
   banco = construir_base_conhecimento(caminho)

   print(f"Total de genes de virulência mapeados: {len(banco)}")
   if "VFG000948" in banco:
	print(f"Anotação extraída: {banco['VFG000948']}"
