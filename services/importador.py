import re
import sqlite3

import pandas as pd

from database import conectar


def limpar_npu(valor):
    return re.sub(r"\D", "", str(valor))


def texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def coluna(df, *nomes):
    for nome in nomes:
        if nome in df.columns:
            return nome
    return None


def normalizar_nome(valor):
    return re.sub(r"[^A-Z0-9]", "", texto(valor).upper())


def nomes_correspondem(primeiro, segundo):
    primeiro = normalizar_nome(primeiro)
    segundo = normalizar_nome(segundo)
    return bool(primeiro and segundo) and (
        primeiro == segundo
        or (len(primeiro) >= 8 and (primeiro in segundo or segundo in primeiro))
    )


def importar_processos_excel(caminho_arquivo_excel):
    """Importa o layout do eproc e o layout legado da carteira."""
    df = pd.read_excel(caminho_arquivo_excel)
    npu_coluna = coluna(df, "Nº Processo", "N° Processo", "NPU")
    autor_coluna = coluna(df, "Autor", "AUTOR", "NOME_AUTOR")
    reu_coluna = coluna(df, "Réu", "Reu", "RÉU", "NOME_REU")
    assessoria_coluna = coluna(df, "ASSESSORIA", "Assessoria")
    classe_coluna = coluna(df, "Classe Judicial")
    juizo_coluna = coluna(df, "Juízo", "Juizo")
    assuntos_coluna = coluna(df, "Assunto(s)", "Assuntos")
    data_coluna = coluna(df, "Data de Autuação", "Data de Atuacao")
    ultimo_coluna = coluna(df, "Último Evento", "Ultimo Evento")
    situacao_coluna = coluna(df, "Situação", "Situacao")
    legado_cliente_doc = coluna(df, "CPF_CNPJ_CLIENTE") if "CPF_CNPJ_CLIENTE" in df.columns else None
    legado_prestador_doc = coluna(df, "CPF_OAB_PRESTADOR") if "CPF_OAB_PRESTADOR" in df.columns else None
    if not npu_coluna:
        raise ValueError("A planilha precisa conter a coluna Nº Processo ou NPU.")

    inseridos = 0
    atualizados = 0
    erros = []
    with conectar() as conn:
        cursor = conn.cursor()
        clientes = cursor.execute("SELECT id, nome_razasocial, cpf_cnpj FROM clientes").fetchall()
        for numero_linha, row in df.iterrows():
            npu = limpar_npu(row.get(npu_coluna))
            autor = texto(row.get(autor_coluna)) if autor_coluna else ""
            reu = texto(row.get(reu_coluna)) if reu_coluna else ""
            assessoria = texto(row.get(assessoria_coluna)) if assessoria_coluna else ""
            if not npu:
                erros.append(f"linha {numero_linha + 2}: NPU vazio")
                continue

            cliente = None
            cliente_nome = ""
            for item in clientes:
                if nomes_correspondem(item[1], autor) or nomes_correspondem(item[1], reu):
                    cliente = item
                    cliente_nome = item[1]
                    break
            if cliente is None and legado_cliente_doc:
                documento = texto(row.get(legado_cliente_doc))
                cliente = cursor.execute(
                    "SELECT id, nome_razasocial, cpf_cnpj FROM clientes WHERE cpf_cnpj = ?",
                    (documento,),
                ).fetchone()
                cliente_nome = cliente[1] if cliente else ""

            prestador = None
            if legado_prestador_doc:
                prestador = cursor.execute(
                    "SELECT id, nome, cpf_oab FROM prestadores WHERE cpf_oab = ?",
                    (texto(row.get(legado_prestador_doc)),),
                ).fetchone()

            papel_cliente = None
            relacao = "cliente não identificado na planilha"
            if cliente:
                if nomes_correspondem(cliente_nome, autor):
                    papel_cliente, relacao = "AUTOR", "cobrança do cliente"
                elif nomes_correspondem(cliente_nome, reu):
                    papel_cliente, relacao = "RÉU", "processo contra o cliente"

            campos = (
                autor,
                reu,
                papel_cliente,
                relacao,
                texto(row.get(juizo_coluna)) if juizo_coluna else "",
                texto(row.get(assuntos_coluna)) if assuntos_coluna else "",
                texto(row.get(data_coluna)) if data_coluna else "",
                texto(row.get(ultimo_coluna)) if ultimo_coluna else "",
                texto(row.get(situacao_coluna)) if situacao_coluna else "",
                assessoria,
                texto(row.get(classe_coluna)) if classe_coluna else "",
            )
            
            # Pega o ID do cliente e do prestador de forma segura (se não achar, fica None)
            cliente_id = cliente[0] if cliente else None
            prestador_id = prestador[0] if prestador else None

            existente = cursor.execute("SELECT 1 FROM processos WHERE npu = ?", (npu,)).fetchone()
            if existente:
                cursor.execute(
                    """UPDATE processos SET nome_autor=?, nome_reu=?, papel_cliente=?,
                    relacao_carteira=?, juizo=?, assuntos=?, data_autuacao=?,
                    ultimo_evento_texto=?, situacao_processo=?, assessoria=?, classe_judicial=?,
                    cliente_id=COALESCE(?, cliente_id), prestador_id=COALESCE(?, prestador_id)
                    WHERE npu=?""",
                    (*campos, cliente_id, prestador_id, npu),
                )
                atualizados += 1
                continue

            # Se o cliente não foi encontrado, registra o aviso, mas O PROCESSO SOBE PARA O BANCO!
            if cliente is None:
                erros.append(f"linha {numero_linha + 2}: processo importado sem vínculo de cliente (pendente de associação)")

            try:
                cursor.execute(
                    """INSERT INTO processos
                    (npu, tribunal, assessoria, cliente_id, prestador_id, nome_autor,
                     nome_reu, papel_cliente, relacao_carteira, juizo, assuntos,
                     data_autuacao, ultimo_evento_texto, situacao_processo,
                     classe_judicial, status_monitoramento)
                    VALUES (?, 'TJSC', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDENTE')""",
                    (npu, assessoria, cliente_id, prestador_id, *campos[:9], campos[10]),
                )
                inseridos += 1
            except sqlite3.IntegrityError as error:
                erros.append(f"linha {numero_linha + 2}: {error}")

    conn.commit()
    return {"inseridos": inseridos, "atualizados": atualizados, "erros": erros}
