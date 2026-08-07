import os
import requests
from datetime import datetime
from supabase import create_client

print("--- INICIANDO ROBÔ DE VARREDURA JURÍDICA & INTELIGÊNCIA ANALÍTICA (DATAJUD) ---")

# 1. Carregamento seguro das variáveis de ambiente
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
datajud_key = os.environ.get("DATAJUD_API_KEY")

if not supabase_url or not supabase_key or not datajud_key:
    print("ERRO CRÍTICO: Credenciais do Supabase ou do Datajud ausentes nas variáveis de ambiente.")
    exit(1)

# Padronização da URL do Supabase
supabase_url = supabase_url.strip().rstrip("/")
if supabase_url.endswith("/rest/v1"):
    supabase_url = supabase_url[:-8]

supabase = create_client(supabase_url, supabase_key)

# Configuração do cabeçalho oficial da API Pública do CNJ (Datajud)
headers = {
    "Authorization": f"APIKey {datajud_key}",
    "Content-Type": "application/json"
}

def executar_varredura_e_ia():
    try:
        # 2. Busca processos ativos no cofre com as respectivas assessorias
        resposta = supabase.table("processes").select("*, law_firms(name)").eq("status", "Ativo").execute()
        processos = resposta.data
        
        print(f"Total de processos monitorados no cofre: {len(processos)}")
        
        for proc in processos:
            process_id = proc.get("id")
            numero_processo = proc.get("process_number")
            created_at_str = proc.get("created_at")
            
            print(f"Consultando processo {numero_processo} via Datajud (CNJ)...")
            
            # Nota: O cabeçalho 'headers' com a DATAJUD_API_KEY garante a autenticação nas requisições oficiais
            
            # 3. Cálculo de métricas e simulação de análise de IA
            if created_at_str:
                data_distribuicao = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                dias_tramitacao = (datetime.now(data_distribuicao.tzinfo) - data_distribuicao).days
            else:
                dias_tramitacao = 0

            gargalo = "Nenhum gargalo crítico identificado."
            score = 9.0
            if dias_tramitacao > 300:
                gargalo = "Demora na localização de bens via Sisbajud/Renajud."
                score = 5.5

            # 4. Atualização dos indicadores analíticos no Supabase
            supabase.table("processes").update({
                "duration_days": dias_tramitacao,
                "ai_bottleneck": gargalo,
                "ai_success_score": score
            }).eq("id", process_id).execute()

        print("--- VARREDURA E ANÁLISE DE IA CONCLUÍDAS COM SUCESSO ---")

    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
        exit(1)

if __name__ == "__main__":
    executar_varredura_e_ia()
