import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(override=True)
api_key = os.getenv("GROQ_API_KEY", "").strip()

try:
    client = Groq(api_key=api_key)
    print("Consultando a Groq...")
    
    modelos = client.models.list()
    print("\n=== MODELOS LIBERADOS PARA SUA CHAVE ===")
    for m in modelos.data:
        print(f'"{m.id}"')
        
except Exception as e:
    print(f"\nErro ao consultar a API: {e}")