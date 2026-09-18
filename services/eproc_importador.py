import re
from io import StringIO

import pandas as pd


def _texto(valor):
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def extrair_eventos_eproc_html(conteudo_html):
    """Extrai a tabela de eventos salva pelo operador no eproc."""
    eventos = []
    for tabela in pd.read_html(StringIO(conteudo_html)):
        colunas = {_texto(col).lower(): col for col in tabela.columns}
        def achar(*termos):
            for nome, original in colunas.items():
                if any(termo in nome for termo in termos):
                    return original
            return None

        coluna_evento = achar("evento")
        coluna_data = achar("data")
        coluna_descricao = achar("descri")
        if not coluna_evento or not coluna_descricao:
            continue

        coluna_usuario = achar("usu")
        coluna_documentos = achar("document")
        coluna_parte = achar("parte", "autor", "réu", "reu")
        coluna_advogado = achar("advog", "representante")

        for _, linha in tabela.iterrows():
            numero = _texto(linha.get(coluna_evento))
            numero = re.search(r"\d+", numero)
            if not numero:
                continue
            eventos.append(
                {
                    "numero_evento": numero.group(0),
                    "data_movimento": _texto(linha.get(coluna_data)),
                    "descricao": _texto(linha.get(coluna_descricao)),
                    "usuario": _texto(linha.get(coluna_usuario)),
                    "documentos": _texto(linha.get(coluna_documentos)),
                    "parte": _texto(linha.get(coluna_parte)),
                    "advogado": _texto(linha.get(coluna_advogado)),
                    "origem": "eproc importado pelo operador",
                }
            )
        if eventos:
            return eventos
    return eventos
