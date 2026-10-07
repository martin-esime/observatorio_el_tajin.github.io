name: vivos-4549-chava

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  run-vivos:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instala deps
        run: pip install requests

      - name: Corre auto_4549_vivos.py
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          CHAVA_EMAIL: ${{ secrets.CHAVA_EMAIL }}
        run: python auto_4549_vivos.py

      - name: Guarda tabla_30.csv
        run: |
          git config user.name "tajin-bot-vivos"
          git config user.email "bot-vivos@tajin.mx"
          git add tabla_30.csv
          git commit -m "vivos: AR4549 M:45% alerta" || echo "sin cambios"
          git push
