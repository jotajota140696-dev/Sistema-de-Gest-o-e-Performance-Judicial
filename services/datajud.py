import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def consultar_processo_datajud(npu):
    print(f"[DataJud] Iniciando consulta via API CNJ para o NPU: {npu}")
    
    npu_limpo = ''.join(filter(str.isdigit, npu))
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsc/_search"
    
    # Lê a chave diretamente da variável de ambiente do sistema de forma segura
    api_key = os.getenv("DATAJUD_API_KEY")
    
    if not api_key:
        print("[DataJud] ❌ Erro crítico: A variável de ambiente DATAJUD_API_KEY não está configurada.")
        return None

    headers = {
        "Authorization": f"APIKey {api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": {
            "match": {
                "numeroProcesso": npu_limpo
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            total_encontrado = dados.get("hits", {}).get("total", {}).get("value", 0)
            
            if total_encontrado > 0:
                print("[DataJud] ✅ Processo localizado com sucesso no CNJ!")
                processo_info = dados["hits"]["hits"][0]["_source"]
                
                with open(f"processo_{npu_limpo}.json", "w", encoding="utf-8") as f:
                    json.dump(processo_info, f, indent=4, ensure_ascii=False)
                    
                return processo_info
            else:
                print("[DataJud] ⚠️ Processo não encontrado na base pública do DataJud.")
                return None
            
        else:
            print(f"[DataJud] ❌ Erro de resposta da API: Código {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[DataJud] ❌ Falha técnica na conexão HTTP: {e}")
        
    return None