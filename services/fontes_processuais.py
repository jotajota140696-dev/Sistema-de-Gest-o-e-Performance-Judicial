from dataclasses import dataclass


@dataclass(frozen=True)
class FonteProcessual:
    codigo: str
    nome: str
    tipo: str
    detalhamento_publico: bool


FONTES = {
    "PJE": FonteProcessual("PJE", "Processo Judicial Eletrônico", "PJe", False),
    "EPROC": FonteProcessual("EPROC", "eproc", "eproc", False),
    "ESAJ": FonteProcessual("ESAJ", "e-SAJ", "e-SAJ", False),
    "DATAJUD": FonteProcessual("DATAJUD", "DataJud CNJ", "API", True),
    "DJEN": FonteProcessual("DJEN", "Diário de Justiça Eletrônico Nacional", "Publicação", True),
}


def identificar_fonte(sistema=None, url=None, tribunal=None):
    texto = " ".join(str(valor or "") for valor in (sistema, url, tribunal)).lower()
    if "eproc" in texto:
        return FONTES["EPROC"]
    if "esaj" in texto or "e-saj" in texto:
        return FONTES["ESAJ"]
    if "pje" in texto:
        return FONTES["PJE"]
    return FONTES["DATAJUD"]


def normalizar_movimento(movimento, fonte="DATAJUD"):
    """Converte movimentos de PJe/eproc/e-SAJ/DataJud para o contrato comum."""
    codigo = (
        movimento.get("codigo")
        or movimento.get("codigoMovimento")
        or movimento.get("codigo_movimento")
    )
    nome = (
        movimento.get("nome")
        or movimento.get("descricao")
        or movimento.get("descricaoMovimento")
        or movimento.get("nome_movimento")
    )
    return {
        "codigo_movimento": codigo,
        "nome_movimento": nome or (f"Movimento {codigo}" if codigo else "Não identificado"),
        "descricao_movimento": (
            movimento.get("descricaoDetalhada")
            or movimento.get("descricao_detalhada")
            or movimento.get("complemento")
            or movimento.get("descricao")
        ),
        "data_movimento": movimento.get("dataHora") or movimento.get("data_movimento") or movimento.get("data"),
        "numero_evento": movimento.get("numeroEvento") or movimento.get("numero_evento") or movimento.get("evento"),
        "parte_evento": movimento.get("parte") or movimento.get("polo") or movimento.get("poloAtivo"),
        "advogado_evento": movimento.get("advogado") or movimento.get("representante"),
        "usuario_evento": movimento.get("usuario") or movimento.get("usuario_evento"),
        "documentos_evento": movimento.get("documentos") or movimento.get("documento"),
        "origem_evento": fonte,
        "complementosTabelados": movimento.get("complementosTabelados") or [],
    }
