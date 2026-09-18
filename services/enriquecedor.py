from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class FonteConsulta:
    codigo: str
    nome: str
    prioridade: int
    confianca: str
    url_modelo: str


FONTES_CONSULTA = (
    FonteConsulta(
        "DATAJUD",
        "DataJud CNJ",
        1,
        "oficial",
        "https://api-publica.datajud.cnj.jus.br/",
    ),
    FonteConsulta(
        "DJEN",
        "Comunica PJe / DJEN",
        2,
        "publicacao oficial",
        "https://comunica.pje.jus.br/consulta?numeroProcesso={npu}",
    ),
    FonteConsulta(
        "TJSC",
        "Consulta processual oficial TJSC",
        2,
        "portal oficial",
        "https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica&numProcesso={npu}",
    ),
    FonteConsulta(
        "DJETJSC",
        "Diário da Justiça Eletrônico TJSC",
        2,
        "diario oficial",
        "https://www.tjsc.jus.br/diario-da-justica-eletronico",
    ),
    FonteConsulta(
        "JUSBRASIL",
        "Jusbrasil",
        4,
        "auxiliar",
        "https://www.jusbrasil.com.br/busca?q={npu}",
    ),
    FonteConsulta(
        "ESCAVADOR",
        "Escavador",
        5,
        "auxiliar",
        "https://www.escavador.com/busca?qo={npu}",
    ),
)


def fontes_para_processo(npu):
    """Retorna as fontes públicas em ordem de confiabilidade."""
    numero = "".join(char for char in str(npu) if char.isdigit())
    return [
        {
            "codigo": fonte.codigo,
            "nome": fonte.nome,
            "confianca": fonte.confianca,
            "url": fonte.url_modelo.format(npu=quote(numero)),
        }
        for fonte in FONTES_CONSULTA
    ]


def selecionar_melhor_dado(candidatos, campo):
    """Escolhe o valor pela prioridade da fonte, sem apagar divergências."""
    prioridade = {fonte.codigo: fonte.prioridade for fonte in FONTES_CONSULTA}
    validos = [item for item in candidatos if item.get(campo)]
    if not validos:
        return None
    return min(validos, key=lambda item: prioridade.get(item.get("fonte"), 99))
