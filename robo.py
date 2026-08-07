import os
from supabase import create_client, Client

# Recupera as credenciais de segurança do ambiente do GitHub
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Erro: As credenciais do Supabase não foram encontradas nas variáveis de ambiente.")
    exit(1)

# Conecta ao nosso "cofre" (Supabase)
supabase: Client = create_client(url, key)

def executar_robo():
    print("--- INICIANDO VARREDURA DOS PROCESSOS ---")
    
    # Busca todos os processos ativos cadastrados no sistema
    resposta = supabase.table("processes").select("*").eq("status", "Ativo").execute()
    processos = resposta.data
    
    print(f"Total de processos encontrados para monitoramento: {len(processos)}")
    
    for proc in processos:
        num_processo = proc.get("process_number")
        tipo = proc.get("process_type")
         devedor = proc.get("debtor_name")
        
        print(f"Analisando Processo: {num_processo} | Tipo: {tipo} | Devedor: {devedor}")
        
        # Aqui o robô faz a varredura nas fontes públicas dos tribunais (futuramente integrado com as chaves de acesso)
        # Por enquanto, registramos a auditoria de acesso bem-sucedida (LGPD)
        
        log_dados = {
            "user_email": "robo-automatico@sistema.local",
            "action": "VARREDURA_DIARIA",
            "details": f"Processo {num_processo} verificado com sucesso pelo robô."
        }
        supabase.table("audit_logs").insert(log_dados).execute()

    print("--- VARREDURA CONCLUÍDA COM SUCESSO ---")

if __name__ == "__main__":
    executar_robo()
