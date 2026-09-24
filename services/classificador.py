import os
import json
import sqlite3
from dotenv import load_dotenv
from groq import Groq

# Força a leitura atualizada do ficheiro .env
load_dotenv(override=True)

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
    api_key = os.getenv("GROQ_API_KEY", "").strip().replace('"', '').replace("'", "")
    
    if not api_key:
        print("\n[ERRO]: A GROQ_API_KEY não foi encontrada no ficheiro .env\n")
        return {"marco": 1, "gargalo": "Chave de API em falta", "resumo": "Configure a GROQ_API_KEY no .env"}

    # Inicializa o cliente oficial do Groq com a sua chave de API
    client = Groq(api_key=api_key)

    # 1. Unificar e ordenar cronologicamente DataJud e DJE
    timeline = []
    for m in movimentos_datajud:
        timeline.append({"data": m.get("dataHora", ""), "fonte": "DataJud", "texto": m.get("nome", "")})
    for d in decisoes_dje:
        timeline.append({"data": d.get("dataPublicacao", ""), "fonte": "DJE", "texto": d.get("teor", "")})
    
    timeline_ordenada = sorted(timeline, key=lambda x: x["data"])
    
    # LIMITADOR RIGOROSO DE TOKENS (Aqui a variável timeline_enxuta é criada)
    # Pega apenas os últimos 15 eventos e limita o texto de cada um a 200 caracteres
    timeline_enxuta = []
    for item in timeline_ordenada[-15:]:
        texto_cortado = str(item.get("texto", ""))[:200]
        timeline_enxuta.append({
            "data": item.get("data", ""),
            "fonte": item.get("fonte", ""),
            "texto": texto_cortado
        })
    
    # 2. Resgatar lições aprendidas anteriormente
    historico_aprendizados = buscar_regras_aprendidas()
    
    # 3. Prompt de Análise Jurídica Blindado
    prompt_completo = f"""
    Você é um Analista Jurídico Sênior e Especialista em Recuperação de Crédito. 
    Sua missão é analisar a linha do tempo recente do processo aplicando rigoroso RACIOCÍNIO JURÍDICO para classificá-lo na Jornada de Ouro (M1 a M10).

    REGRAS APRENDIDAS COM O USUÁRIO EM CASOS ANTERIORES:
    {historico_aprendizados}

    DIRETRIZES DE ANÁLISE JURÍDICA PROFUNDA (OBRIGATÓRIO):
    1. NÃO OLHE APENAS PARA O ÚLTIMO EVENTO ISOLADO. Analise a cadeia de eventos. 
    2. Ferramentas de localização de patrimônio/medidas constritivas (ex: PREVJUD, SisbaJud, InfoJud, Renajud, penhora) indicam que o processo JÁ PASSOU da fase inicial (nunca Marco 1).
    3. Despachos iniciais padrão contêm menções a atos futuros e não consumados.

    PROCESSO: {processo_numero}
    LINHA DO TEMPO RECENTE:
    {json.dumps(timeline_enxuta, ensure_ascii=False, indent=2)}

    INSTRUÇÕES CRÍTICAS DE SAÍDA:
    - Retorne APENAS um objeto JSON válido e absolutamente nada mais.
    - NÃO inclua blocos de formatação Markdown (não use ```json).
    - Evite quebras de linha dentro dos textos.

    Retorne exatamente esta estrutura:
    {{
      "marco": <número inteiro de 1 a 10>,
      "gargalo": "<texto curto e preciso>",
      "resumo": "<explicação curta>"
    }}
    """

    try:
        # Execução via SDK oficial da Groq com modelo selecionado
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Você é uma API de dados que responde exclusivamente com JSON puro e sem formatação markdown."
                },
                {
                    "role": "user",
                    "content": prompt_completo
                }
            ],
            model="qwen/qwen3.8-27b",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        texto_gerado = chat_completion.choices[0].message.content
        dados_brutos = json.loads(texto_gerado)
        
        return {
            "marco": int(dados_brutos.get("marco", 1)),
            "gargalo": str(dados_brutos.get("gargalo", "Analisado via Groq SDK")),
            "resumo": str(dados_brutos.get("resumo", ""))
        }

    except Exception as e:
        print(f"\n[ERRO NA IA - PROCESSO {processo_numero}]: {e}\n")
        return {"marco": 1, "gargalo": "Erro de Execução", "resumo": str(e)}

def analisar_marco_e_gargalo(dados_processo):
    processo_numero = dados_processo.get("numero", dados_processo.get("processo_numero", "N/D"))
    movimentos_datajud = dados_processo.get("movimentos", dados_processo.get("movimentos_datajud", []))
    decisoes_dje = dados_processo.get("decisoes", dados_processo.get("decisoes_dje", []))
    
    return analisar_processo_com_ia(processo_numero, movimentos_datajud, decisoes_dje)