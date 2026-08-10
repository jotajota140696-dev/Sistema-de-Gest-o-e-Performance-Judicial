import os
import time
from supabase import create_client, Client
import google.generativeai as genai

# Configuração das Credenciais do Supabase (Variáveis de Ambiente)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "SUA_URL_SUPABASE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "SUA_CHAVE_SUPABASE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da Inteligência Artificial (Gemini API)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SUA_CHAVE_GEMINI")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analisar_processo_com_ia(npu, tribunal, ultima_movimentacao):
    """Usa a IA para traduzir e gerar o diagnóstico estratégico do processo."""
    prompt = f"""
    Atue como um advogado especialista em recuperação de crédito e estratégias processuais.
    Analise o seguinte processo jurídico:
    - NPU: {npu}
    - Tribunal: {tribunal}
    - Última Movimentação: {ultima_movimentacao}

    Retorne a resposta estritamente estruturada com os seguintes campos separados por '|':
    1. Fase Processual Atual (ex: Fase de Execução - Citação)
    2. O que já foi feito (resumo simples para o cliente)
    3. O que falta ou pendências críticas
    4. Próximos passos recomendados
    5. Avaliação da condução (se está célere ou travado)
    """
    try:
        response = model.generate_content(prompt)
        partes = response.text.split('|')
        if len(partes) >= 5:
            return {
                "fase": partes[0].strip(),
                "feito": partes[1].strip(),
                "falta": partes[2].strip(),
                "proximos": partes[3].strip(),
                "conducao": partes[4].strip()
            }
    except Exception as e:
        print(f"Erro na IA para o processo {npu}: {e}")
    
    return {
        "fase": "Em monitoramento",
        "feito": ultima_movimentacao,
        "falta": "Aguardando novos despachos",
        "proximos": "Acompanhar andamentos",
        "conducao": "Regular"
    }

def executar_varredura_diaria():
    print("=== INICIANDO VARREDURA DIÁRIA DE PROCESSOS ===")
    
    # 1. Busca todos os processos ativos cadastrados no Supabase
    response = supabase.table("processos").select("*").eq("status_atual", "Ativo").execute()
    processos = response.data

    if not processos:
        print("Nenhum processo ativo encontrado para monitorar.")
        return

    print(f"Total de processos encontrados para varredura: {len(processos)}")

    for proc in processos:
        processo_id = proc["id"]
        npu = proc["npu"]
        tribunal = proc.get("tribunal", "TJSC")

        print(f"Verificando processo NPU: {npu} ({tribunal})...")

        # [PONTO DO ROBÔ] Aqui entraria a chamada real à API Pública (Datajud / Tribunais)
        # Simulando a captura de uma nova movimentação do tribunal:
        movimentacao_exemplo = "Juntada de Mandado de Citação Cumprido Positivo."

        # 2. Salva o novo andamento na tabela 'andamentos'
        supabase.table("andamentos").insert({
            "processo_id": processo_id,
            "data_andamento": "2026-06-06T10:00:00Z",
            "descricao_original": movimentacao_exemplo,
            "descricao_traduzida": "O oficial de justiça cumpriu o mandado de citação com sucesso.",
            "criado_pelo_robo": True
        }).execute()

        # 3. Aciona o Cérebro de IA para atualizar a análise estratégica
        diagnostico = analisar_processo_com_ia(npu, tribunal, movimentacao_exemplo)

        # 4. Salva ou atualiza a análise na tabela 'analises_ia'
        supabase.table("analises_ia").insert({
            "processo_id": processo_id,
            "fase_processual": diagnostico["fase"],
            "o_que_foi_feito": diagnostico["feito"],
            "o_que_falta": diagnostico["falta"],
            "proximos_passos": diagnostico["proximos"],
            "tempo_conducao_analise": diagnostico["conducao"]
        }).execute()

        print(f"Processo {npu} atualizado e analisado com sucesso pela IA!")
        time.sleep(1) # Intervalo para respeitar limites de requisição da API

    print("=== VARREDURA DIÁRIA CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    executar_varredura_diaria()
