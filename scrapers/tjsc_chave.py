import time
import os
from io import StringIO
import pandas as pd
import easyocr
from scrapers.base_scraper import BaseScraper

# Inicializa o EasyOCR uma única vez para otimizar a velocidade (roda 100% em Python)
print("[TJSC-Chave] 🔄 Inicializando motor de IA do EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)


def extrair_eventos_html(html):
    """Converte a tabela de eventos do eproc para registros do sistema."""
    eventos = []
    try:
        tabelas = pd.read_html(StringIO(html))
    except ValueError:
        return eventos

    for tabela in tabelas:
        tabela.columns = [
            " ".join(str(col).split()).strip().lower()
            for col in tabela.columns
        ]
        mapa = {}
        for coluna in tabela.columns:
            if "evento" in coluna and "descri" not in coluna:
                mapa["numero_evento"] = coluna
            elif "data" in coluna:
                mapa["data"] = coluna
            elif "descri" in coluna:
                mapa["descricao"] = coluna
            elif "usu" in coluna:
                mapa["usuario"] = coluna
            elif "document" in coluna:
                mapa["documentos"] = coluna
        if not {"numero_evento", "descricao"}.issubset(mapa):
            continue

        for _, linha in tabela.iterrows():
            eventos.append(
                {
                    "numero_evento": str(linha.get(mapa["numero_evento"], "")).strip(),
                    "descricao": str(linha.get(mapa["descricao"], "")).strip(),
                    "usuario": str(linha.get(mapa.get("usuario"), "")).strip(),
                    "documentos": str(linha.get(mapa.get("documentos"), "")).strip(),
                }
            )
        break
    return eventos

def resolver_captcha_automaticamente(scraper):
    try:
        print("[TJSC-Chave] 🤖 Capturando e lendo o Captcha via EasyOCR...")
        
        # Aguarda a imagem aparecer na tela de bloqueio do eproc
        scraper.page.wait_for_selector("img", timeout=8000)
        
        imagens = scraper.page.locator("img").all()
        captcha_element = None
        
        for img_element in imagens:
            src = img_element.get_attribute("src") or ""
            if "captcha" in src.lower() or "externo" in src.lower() or len(imagens) > 2:
                captcha_element = img_element
                break
                
        if not captcha_element and len(imagens) > 0:
            captcha_element = imagens[1] if len(imagens) > 1 else imagens[0]

        if not captcha_element:
            print("[TJSC-Chave] ⚠️ Imagem do captcha não localizada.")
            return False

        # Salva o print do captcha temporariamente no diretório
        captcha_path = "captcha_temp.png"
        captcha_element.screenshot(path=captcha_path)
        
        # Faz a leitura do texto usando o EasyOCR
        resultados = reader.readtext(captcha_path, detail=0)
        if not resultados:
            print("[TJSC-Chave] ⚠️ O EasyOCR não retornou nenhum texto.")
            return False
            
        texto_resolvido = "".join(resultados).strip()
        # Filtra apenas caracteres alfanuméricos válidos
        texto_resolvido = ''.join(c for c in texto_resolvido if c.isalnum())
        
        print(f"[TJSC-Chave] 🔍 Texto decifrado pelo EasyOCR: '{texto_resolvido}'")
        
        if len(texto_resolvido) >= 3:
            # Preenche o campo de texto do captcha
            input_texto = scraper.page.locator("input[type='text']").first
            input_texto.fill(texto_resolvido)
            time.sleep(1)
            
            # Clica no botão ENVIAR
            scraper.page.locator("input[value='ENVIAR'], button:has-text('ENVIAR'), input[type='submit']").first.click()
            time.sleep(3)
            return True
            
    except Exception as e:
        print(f"[TJSC-Chave] ⚠️ Erro na rotina de resolução do EasyOCR: {e}")
    
    return False

def consultar_processo_por_chave_tjsc(npu, chave_acesso):
    print(f"[TJSC-Chave] Iniciando consulta autônoma para o NPU: {npu}")
    
    scraper = BaseScraper("TJSC-Chave", headless=False)
    scraper.iniciar_navegador()

    try:
        url = "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=processo_consulta_publica&hash=eeec6dcb7f2ba4501592c86976c34582"
        print("[TJSC-Chave] Acessando portal...")
        scraper.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)

        # Verifica se caiu na tela de bloqueio com captcha
        conteudo = scraper.page.content()
        if "Prezado(a) usuário(a)" in conteudo or "código exibido na imagem" in conteudo:
            sucesso_captcha = resolver_captcha_automaticamente(scraper)
            if not sucesso_captcha:
                print("[TJSC-Chave] ❌ O OCR não conseguiu passar automaticamente nesta tentativa.")
                return {"npu": npu}

        # Aguarda o formulário principal de consulta do processo liberar
        print("[TJSC-Chave] Aguardando formulário de consulta...")
        scraper.page.wait_for_selector("input#txtNumProcesso", timeout=20000)
        
        print(f"[TJSC-Chave] Preenchendo NPU: {npu}")
        scraper.page.fill("input#txtNumProcesso", npu)
        
        if chave_acesso:
            print(f"[TJSC-Chave] Preenchendo Chave: {chave_acesso}")
            scraper.page.locator("input#txtChaveProcesso").fill(str(chave_acesso))
        
        print("[TJSC-Chave] Disparando botão Consultar...")
        scraper.page.locator("button#sbmConsultar, input#sbmConsultar, button:has-text('Consultar')").first.click()
        time.sleep(5)
        
        html = scraper.page.content()
        with open("resultado_processo.html", "w", encoding="utf-8") as f:
            f.write(html)
        eventos = extrair_eventos_html(html)
            
        print("[TJSC-Chave] ✅ Consulta concluída de forma totalmente autônoma!")

    except Exception as e:
        print(f"[TJSC-Chave] ❌ Erro durante o fluxo: {e}")
    finally:
        scraper.fechar_navegador()

    return {"npu": npu, "eventos": eventos if "eventos" in locals() else []}