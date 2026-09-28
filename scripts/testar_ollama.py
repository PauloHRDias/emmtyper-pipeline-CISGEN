from langchain_ollama import OllamaLLM
import sys

print("A enviar pergunta para o Llama 3 local...")

try:
    llm = OllamaLLM(model="llama3", base_url="http://localhost:11434")

    resposta = llm.invoke("Responda em uma frase em português: O que é a bactéria Streptococcus pyogenes?")
    print("\n[Resposta do Modelo]:\n", resposta)
except Exception as e:
    print(f"\nErro de conexão: {e}")
    sys.exit(1)
