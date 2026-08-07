import os
from supabase import create_client
from datetime import datetime

print("--- INICIANDO ROBÔ DE INTELIGÊNCIA ANALÍTICA & BENCHMARKING ---")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERRO: Credenciais ausentes.")
    exit(1)

url = url.strip().rstrip("/")
if url.endswith("/rest/v1"):
    url = url[:-8]

supabase = create_client(url, key)

def analisar_performance_e_ia():
    # 1. Busca processos ativos com suas respectivas assessorias
    resposta = supabase.table("processes").select("*, law_firms(name)").eq("status", "Ativo").execute()
    processos = resposta.data
    
    print(f"Processando indicadores para {len(processos)} processos...")
    
    for proc in processos:
        process_id = proc.get("id")
        created_at_str = proc.get("created_at")
        tipo = proc.get("process_type")
        
        # Simula cálculo de dias em andamento (poderia ser baseado na data real de distribuição)
        data_distribuicao = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        dias_tramitacao = (datetime.now(data_distribuicao.tzinfo) - data_distribuicao).days
        
        # Simulação de análise de IA para detectar gargalos com base no tipo de ação
        gargalo = "Nenhum gargalo crítico identificado."
        score = 8.5
        if dias_tramitacao > 300:
            gargalo = "Demora na localização de bens via Sisbajud/Renajud."
            score = 5.0
            
        # Atualiza o processo com as métricas calculadas
        supabase.table("processes").update({
            "duration_days": dias_tramitacao,
            "ai_bottleneck": gargalo,
            "ai_success_score": score
        }).eq("id", process_id).execute()

    print("--- ANÁLISE CONCLUÍDA E MÉTRICAS ATUALIZADAS NO SUPABASE ---")

if __name__ == "__main__":
    analisar_performance_e_ia()
