import os
import json
import sqlite3
from google import genai
from google.genai import types

def buscar_regras_aprendidas():
    """Busca no banco de dados todas as correções ensinadas anteriormente."""
    try:
        conn = sqlite3.connect("banco_simj.db")
        cursor = conn.cursor()
        cursor.execute("SELECT regra_aprendida FROM aprendizados_ia")
        regras = [row[0] for row in cursor.fetchall()]
        conn.close()
        return "\n".join([f"- {r}" for r in regras]) if regras else "Nenhuma regra específica cadastrada ainda."
    except Exception:
        return "Nenhuma regra cadastrada."

def analisar_processo_com_ia(processo_numero, movimentos_datajud, decisoes_dje):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # 1. Unificar e ordenar cronologicamente DataJud e DJE
    timeline = []
    for m in movimentos_datajud:
        timeline.append({"data": m.get("dataHora", ""), "fonte": "DataJud", "texto": m.get("nome", "")})
    for d in decisoes_dje:
        timeline.append({"data": d.get("dataPublicacao", ""), "fonte": "DJE", "texto": d.get("teor", "")})
    
    timeline_ordenada = sorted(timeline, key=lambda x: x["data"])
    
    # 2. Resgatar lições aprendidas com você anteriormente
    historico_aprendizados = buscar_regras_aprendidas()
    
    # 3. Prompt de Sistema com Inteligência Jurídica e Instruções Rígidas
    system_instruction = f"""
    Você é um Analista Jurídico Sênior de Recuperação de Crédito. 
    Sua missão é ler a linha do tempo cronológica do processo (DataJud + DJE) e classificá-lo na Jornada de Ouro (M1 a M10).

    REGRAS APRENDIDAS COM O USUÁRIO EM CASOS ANTERIORES (SIGA RIGOROSAMENTE):
    {historico_aprendizados}

    DIRETRIZES DE CONTEXTO JURÍDICO:
    - Despachos iniciais padrão (ex: "defiro o processamento, cite-se e, caso infrutífero, bloqueie-se...") contêm menções a atos futuros. Eles NÃO significam que o ato ocorreu.
    - Se a citação (Marco 2) não foi efetivamente cumprida, o processo NÃO pode avançar para constrições ou fases finais (M3 a M10).
    - Retorne obrigatoriamente um JSON puro contendo: "marco" (int de 1 a 10), "gargalo" (string) e "resumo" (string explicativa baseada no contexto).
    """

    conteudo_prompt = f"Processo: {processo_numero}\nLinha do tempo:\n{json.dumps(timeline_ordenada, ensure_ascii=False, indent=2)}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conteudo_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        return {"marco": 1, "gargalo": "Erro na IA", "resumo": str(e)}
    
def analisar_marco_e_gargalo(dados_processo):
    """
    Função ponte criada para compatibilidade com o main.py.
    Redireciona a chamada para analisar_processo_com_ia.
    """
    # Extrai os dados do processo enviados pelo main.py
    processo_numero = dados_processo.get("numero", dados_processo.get("processo_numero", "N/D"))
    movimentos_datajud = dados_processo.get("movimentos", dados_processo.get("movimentos_datajud", []))
    decisoes_dje = dados_processo.get("decisoes", dados_processo.get("decisoes_dje", []))
    
    # Chama a sua função principal de IA
    return analisar_processo_com_ia(processo_numero, movimentos_datajud, decisoes_dje)