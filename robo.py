import os
from supabase import create_client

print("--- INICIANDO ROBÔ DE VARREDURA JURÍDICA ---")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERRO CRÍTICO: As credenciais do Supabase não foram encontradas.")
    exit(1)

# Limpeza automática da URL para garantir compatibilidade com a biblioteca Python
url = url.strip().rstrip("/")
if url.endswith("/rest/v1"):
    url = url[:-8]

try:
    # Conecta ao Supabase
    supabase = create_client(url, key)
    print("Conexão com o cofre do Supabase estabelecida com sucesso.")
    
    # Testa a leitura da tabela de processos
    resposta = supabase.table("processes").select("*").eq("status", "Ativo").execute()
    processos = resposta.data
    
    print(f"Total de processos ativos encontrados: {len(processos)}")
    
    # Registra o log de auditoria LGPD
    log_dados = {
        "user_email": "robo-automatico@sistema.local",
        "action": "VARREDURA_DIARIA",
        "details": f"Varredura concluída. Total de processos verificados: {len(processos)}"
    }
    supabase.table("audit_logs").insert(log_dados).execute()
    print("Log de auditoria LGPD gravado com sucesso.")

except Exception as e:
    print(f"Ocorreu um erro durante a execução: {e}")
    exit(1)

print("--- EXECUÇÃO FINALIZADA COM SUCESSO ---")
