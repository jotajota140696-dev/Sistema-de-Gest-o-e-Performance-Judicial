# services/djen.py
import os
import re
import time
import requests
from fpdf import FPDF

DIR_DOWNLOADS = "downloads"
BASE_URL_DJEN = "https://comunicaapi.pje.jus.br/api/v1"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
})

def criar_pdf_local(caminho_arquivo: str, npu_limpo: str, id_comunica: int, item: dict):
    """Gera um PDF local formatado com o texto do Diário caso o CNJ não possua PDF anexo."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Cabeçalho
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "DIÁRIO DE JUSTIÇA ELETRÔNICO (CNJ / COMUNICA PJE)", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        # Metadados
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"Processo (NPU): {npu_limpo}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"ID Comunicacao: {id_comunica}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Data Disponibilizacao: {item.get('data_disponibilizacao', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Tribunal: {item.get('siglaTribunal', 'N/A')} - {item.get('nomeOrgao', '')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Conteúdo do Movimento
        pdf.set_font("Helvetica", "", 10)
        texto = item.get("texto") or "Sem conteúdo textual cadastrado."
        
        # Trata caracteres não mapeados na codificação padrão
        texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, texto_limpo)
        
        pdf.output(caminho_arquivo)
        print(f"   📄 PDF gerado a partir do texto: {caminho_arquivo}")
        return caminho_arquivo
    except Exception as e:
        print(f"   ⚠️ Erro ao gerar PDF local do ID {id_comunica}: {e}")
        return None


def baixar_ou_gerar_pdf(id_comunicacao: int, npu_limpo: str, item: dict) -> str | None:
    """Baixa o PDF nativo do PJe ou cria o PDF local com o conteúdo do diário."""
    os.makedirs(DIR_DOWNLOADS, exist_ok=True)
    caminho_arquivo = os.path.join(DIR_DOWNLOADS, f"comunica_{npu_limpo}_{id_comunicacao}.pdf")
    url_pdf = f"{BASE_URL_DJEN}/comunicacao/{id_comunicacao}/pdf"
    
    try:
        response = session.get(url_pdf, timeout=15)
        # Se existir PDF anexo no servidor do CNJ
        if response.status_code == 200 and len(response.content) > 0:
            with open(caminho_arquivo, "wb") as f:
                f.write(response.content)
            print(f"   📄 PDF oficial baixado: {caminho_arquivo}")
            return caminho_arquivo
    except Exception:
        pass

    # Se retornar 404 (sem anexo), gera o PDF a partir do texto da publicação
    return criar_pdf_local(caminho_arquivo, npu_limpo, id_comunicacao, item)


def consultar_djen(numero_processo: str, max_tentativas: int = 3) -> list:
    """Busca publicações na API do DJEN e assegura o arquivo PDF para cada item."""
    url = f"{BASE_URL_DJEN}/comunicacao"
    proc_limpo = re.sub(r'\D', '', str(numero_processo))
    
    params = {
        "meio": "D",
        "numeroProcesso": proc_limpo,
        "pagina": 1,
        "itensPorPagina": 50
    }

    for tentativa in range(1, max_tentativas + 1):
        try:
            response = session.get(url, params=params, timeout=25)
            
            if response.status_code == 200:
                dados = response.json()
                items = dados.get("items", [])
                
                publicacoes = []
                for item in items:
                    id_comunica = item.get("id")
                    caminho_pdf = None
                    
                    if id_comunica:
                        caminho_pdf = baixar_ou_gerar_pdf(id_comunica, proc_limpo, item)

                    publicacoes.append({
                        "id": id_comunica,
                        "data": item.get("data_disponibilizacao"),
                        "tribunal": item.get("siglaTribunal"),
                        "conteudo": item.get("texto", ""),
                        "orgao": item.get("nomeOrgao"),
                        "arquivo_local": caminho_pdf
                    })
                return publicacoes

            elif response.status_code == 429:
                time.sleep(3)

        except Exception as e:
            print(f"   ⚠️ Falha ao acessar Comunica PJe: {e}")
            break

    return []