name: Robô Jurídico Diário

on:
  workflow_dispatch: # Permite rodar manualmente pelo botão Actions no GitHub
  schedule:
    - cron: '0 3 * * *' # Roda todos os dias às 03:00 da manhã (horário seguro)

jobs:
  executar:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout do Repositório
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Instalar Dependências
        run: |
          pip install requests supabase

      - name: Executar Robô Híbrido
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          DATAJUD_API_KEY: ${{ secrets.DATAJUD_API_KEY }}
        run: |
          python robo_ia.py
