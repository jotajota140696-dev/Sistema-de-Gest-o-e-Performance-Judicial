import re
from playwright.sync_api import sync_playwright


URL_PROCESSO = (
    "https://www.jusbrasil.com.br/processos/922083723/"
    "processo-n-5027153-9220268240930-do-tjsc"
)


def consultar_jusbrasil_publico(npu):
    """Consulta a página pública do Jusbrasil sem login ou bypass de proteção."""
    npu_limpo = re.sub(r"\D", "", str(npu))
    url = URL_PROCESSO if npu_limpo == "50271539220268240930" else (
        f"https://www.jusbrasil.com.br/busca?q={npu_limpo}"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(locale="pt-BR")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            verificar = page.get_by_text("Verificar situação", exact=True)
            if verificar.count():
                verificar.first.click()
                page.wait_for_timeout(5000)

            # O historico e carregado em paginas pelo botao "Mostrar mais".
            # Clique somente no controle publico da pagina, sem contornar protecoes.
            for _ in range(30):
                botoes = page.get_by_text("Mostrar mais", exact=True)
                visivel = None
                for indice in range(botoes.count()):
                    botao = botoes.nth(indice)
                    if botao.is_visible():
                        visivel = botao
                        break
                if visivel is None:
                    break
                antes = len(page.locator("body").inner_text())
                visivel.click()
                page.wait_for_timeout(1200)
                depois = len(page.locator("body").inner_text())
                if depois <= antes:
                    break

            for texto_exibir in ("Exibir mais", "Mostrar explicação"):
                controles = page.get_by_text(texto_exibir, exact=True)
                for indice in range(controles.count()):
                    controle = controles.nth(indice)
                    if controle.is_visible() and texto_exibir == "Exibir mais":
                        controle.click()
                        page.wait_for_timeout(500)
            texto = page.locator("body").inner_text()
            sinais_bloqueio = (
                "verificação de segurança",
                "verificacao de seguranca",
                "cloudflare",
                "não é um bot",
                "nao e um bot",
            )
            bloqueado = any(sinal in texto.lower() for sinal in sinais_bloqueio)
            return {"url": page.url, "texto": texto, "bloqueado": bloqueado}
        except Exception as erro:
            return {"url": page.url, "texto": "", "bloqueado": True, "erro": str(erro)}
        finally:
            browser.close()


def extrair_descricoes_jusbrasil(texto):
    """Localiza várias descrições públicas e associa cada uma à data exibida."""
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    datas = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
    descricoes = []
    data_atual = None
    for linha in linhas:
        data = datas.search(linha)
        if data:
            data_atual = data.group(0)
        encontrados = re.findall(
            r"(?:PEDIDO DE [A-ZÀ-Ú ]+|CIÊNCIA, COM RENÚNCIA AO PRAZO|"
            r"DECORRIDO PRAZO[^|\n]*|CONCLUSOS PARA [A-ZÀ-Ú ]+)",
            linha.upper(),
        )
        for descricao in encontrados:
            descricao = re.sub(r"\s+", " ", descricao).strip(" -")
            item = {"descricao": descricao, "data": data_atual}
            if item not in descricoes:
                descricoes.append(item)
    return descricoes


def extrair_descricao_jusbrasil(texto, data="21/05/2026"):
    """Mantém compatibilidade e retorna a descrição da data solicitada."""
    for item in extrair_descricoes_jusbrasil(texto):
        if item["data"] == data:
            return item["descricao"]
    return None
