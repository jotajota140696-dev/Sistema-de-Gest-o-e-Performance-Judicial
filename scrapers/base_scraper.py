from playwright.sync_api import sync_playwright
import os

class BaseScraper:
    def __init__(self, nome, headless=False):
        self.nome = nome
        self.headless = headless 
        self.playwright = None
        self.context = None
        self.page = None

    def iniciar_navegador(self):
        print(f"[{self.nome}] Iniciando navegador com configuração padrão...")
        self.playwright = sync_playwright().start()
        
        user_data_dir = os.path.abspath("./browser_profile")
        
        # Mantém uma sessão persistente, sem alterar a identificação do navegador.
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=self.headless,
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
        )
        
        self.page = self.context.new_page()
        

    def fechar_navegador(self):
        print(f"[{self.nome}] Encerrando robô...")
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()