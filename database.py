# database.py
import sqlite3
import os

DB_NAME = "banco_simj.db"

def conectar():
    """Cria a conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inserir_movimento(
    conn,
    npu,
    data_movimento,
    nome_movimento,
    codigo_movimento,
    descricao_movimento=None,
    numero_evento=None,
    usuario_evento=None,
    documentos_evento=None,
    fonte_detalhe=None,
    confianca_evento=None,
):
    """Insere ou completa um movimento sem duplicar a mesma ocorrência."""
    cursor = conn.execute(
        """SELECT id FROM movimentos
        WHERE npu = ? AND data_movimento = ? AND codigo_movimento = ?""",
        (npu, data_movimento, codigo_movimento),
    )
    existente = cursor.fetchone()
    if existente:
        conn.execute(
            """UPDATE movimentos
            SET nome_movimento = COALESCE(NULLIF(?, ''), nome_movimento),
                descricao_movimento = COALESCE(NULLIF(?, ''), descricao_movimento),
                numero_evento = COALESCE(?, numero_evento),
                usuario_evento = COALESCE(NULLIF(?, ''), usuario_evento),
                documentos_evento = COALESCE(NULLIF(?, ''), documentos_evento)
                , fonte_detalhe = COALESCE(NULLIF(?, ''), fonte_detalhe)
                , confianca_evento = COALESCE(NULLIF(?, ''), confianca_evento)
            WHERE id = ?""",
            (
                nome_movimento,
                descricao_movimento,
                numero_evento,
                usuario_evento,
                documentos_evento,
                fonte_detalhe,
                confianca_evento,
                existente[0],
            ),
        )
        return False

    conn.execute(
        """INSERT INTO movimentos
        (npu, codigo_movimento, nome_movimento, descricao_movimento, numero_evento,
         usuario_evento, documentos_evento, fonte_detalhe, confianca_evento, data_movimento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            npu,
            codigo_movimento,
            nome_movimento,
            descricao_movimento,
            numero_evento,
            usuario_evento,
            documentos_evento,
            fonte_detalhe,
            confianca_evento,
            data_movimento,
        ),
    )
    return True


def atualizar_detalhes_eproc(conn, npu, eventos):
    """Completa movimentos com os dados detalhados capturados no eproc."""
    atualizados = 0
    for evento in eventos:
        numero = evento.get("numero_evento")
        if numero in (None, ""):
            continue
        cursor = conn.execute(
            """UPDATE movimentos
            SET descricao_movimento = COALESCE(NULLIF(?, ''), descricao_movimento),
                usuario_evento = COALESCE(NULLIF(?, ''), usuario_evento),
                documentos_evento = COALESCE(NULLIF(?, ''), documentos_evento),
                parte_evento = COALESCE(NULLIF(?, ''), parte_evento),
                advogado_evento = COALESCE(NULLIF(?, ''), advogado_evento),
                origem_evento = COALESCE(NULLIF(?, ''), origem_evento),
                fonte_detalhe = COALESCE(NULLIF(?, ''), fonte_detalhe),
                confianca_evento = COALESCE(NULLIF(?, ''), confianca_evento),
                data_movimento = COALESCE(NULLIF(?, ''), data_movimento)
            WHERE npu = ? AND numero_evento = ?""",
            (
                evento.get("descricao"),
                evento.get("usuario"),
                evento.get("documentos"),
                evento.get("parte"),
                evento.get("advogado"),
                evento.get("origem"),
                evento.get("fonte_detalhe") or evento.get("origem"),
                evento.get("confianca_evento") or "detalhado pela fonte auxiliar",
                evento.get("data_movimento"),
                npu,
                numero,
            ),
        )
        atualizados += cursor.rowcount
    return atualizados


def atualizar_detalhe_auxiliar(conn, npu, numero_evento, descricao, fonte):
    """Registra descrição encontrada em uma fonte pública auxiliar."""
    cursor = conn.execute(
        """UPDATE movimentos
        SET descricao_movimento = COALESCE(NULLIF(?, ''), descricao_movimento),
            fonte_detalhe = COALESCE(NULLIF(?, ''), fonte_detalhe),
            confianca_evento = 'auxiliar: confirmação pública'
        WHERE npu = ? AND numero_evento = ?""",
        (descricao, fonte, npu, numero_evento),
    )
    return cursor.rowcount


def registrar_evidencia_processo(conn, npu, fonte, tipo, resumo, url=None, numero_evento=None):
    """Registra uma evidência pública sem misturá-la ao dado oficial do DataJud."""
    existente = conn.execute(
        """SELECT 1 FROM evidencias_processo
        WHERE npu = ? AND numero_evento IS ? AND fonte = ? AND tipo = ? AND resumo = ?""",
        (npu, numero_evento, fonte, tipo, resumo),
    ).fetchone()
    if existente:
        return False
    conn.execute(
        """CREATE TABLE IF NOT EXISTS evidencias_processo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npu TEXT NOT NULL,
            numero_evento INTEGER,
            fonte TEXT NOT NULL,
            tipo TEXT NOT NULL,
            resumo TEXT NOT NULL,
            url TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.execute(
        """INSERT INTO evidencias_processo
        (npu, numero_evento, fonte, tipo, resumo, url)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (npu, numero_evento, fonte, tipo, resumo, url),
    )
    return True

def criar_tabelas():
    """Cria e atualiza o esquema sem apagar dados já coletados."""
    with conectar() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_razasocial TEXT NOT NULL,
                cpf_cnpj TEXT UNIQUE NOT NULL,
                email TEXT,
                telefone TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prestadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf_oab TEXT UNIQUE NOT NULL,
                tipo_servico TEXT,
                telefone TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processos (
                npu TEXT PRIMARY KEY,
                tribunal TEXT,
                classe_judicial TEXT,
                assessoria TEXT,
                marco_atual INTEGER DEFAULT 0,
                data_ultima_atualizacao TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npu TEXT,
                codigo_movimento INTEGER,
                nome_movimento TEXT,
                descricao_movimento TEXT,
                numero_evento INTEGER,
                usuario_evento TEXT,
                documentos_evento TEXT,
                parte_evento TEXT,
                advogado_evento TEXT,
                origem_evento TEXT,
                fonte_detalhe TEXT,
                confianca_evento TEXT,
                data_movimento TEXT,
                FOREIGN KEY(npu) REFERENCES processos(npu)
            )
        ''')

        colunas_movimentos = {row[1] for row in cursor.execute("PRAGMA table_info(movimentos)")}
        if "descricao_movimento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN descricao_movimento TEXT")
        if "numero_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN numero_evento INTEGER")
        if "usuario_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN usuario_evento TEXT")
        if "documentos_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN documentos_evento TEXT")
        if "parte_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN parte_evento TEXT")
        if "advogado_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN advogado_evento TEXT")
        if "origem_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN origem_evento TEXT")
        if "fonte_detalhe" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN fonte_detalhe TEXT")
        if "confianca_evento" not in colunas_movimentos:
            cursor.execute("ALTER TABLE movimentos ADD COLUMN confianca_evento TEXT")

        colunas = {row[1] for row in cursor.execute("PRAGMA table_info(processos)")}
        if "cliente_id" not in colunas:
            cursor.execute("ALTER TABLE processos ADD COLUMN cliente_id INTEGER")
        if "prestador_id" not in colunas:
            cursor.execute("ALTER TABLE processos ADD COLUMN prestador_id INTEGER")
        if "status_monitoramento" not in colunas:
            cursor.execute("ALTER TABLE processos ADD COLUMN status_monitoramento TEXT DEFAULT 'PENDENTE'")
        if "data_cadastro" not in colunas:
            cursor.execute("ALTER TABLE processos ADD COLUMN data_cadastro DATETIME")
            cursor.execute(
                "UPDATE processos SET data_cadastro = CURRENT_TIMESTAMP WHERE data_cadastro IS NULL"
            )
        for nome_coluna, tipo_coluna in {
            "nome_autor": "TEXT",
            "nome_reu": "TEXT",
            "papel_cliente": "TEXT",
            "relacao_carteira": "TEXT",
            "juizo": "TEXT",
            "assuntos": "TEXT",
            "data_autuacao": "TEXT",
            "ultimo_evento_texto": "TEXT",
            "situacao_processo": "TEXT",
        }.items():
            if nome_coluna not in colunas:
                cursor.execute(
                    f"ALTER TABLE processos ADD COLUMN {nome_coluna} {tipo_coluna}"
                )

        cursor.execute("UPDATE processos SET status_monitoramento = 'PENDENTE' WHERE status_monitoramento IS NULL")
        # (Sua linha 259 atual)
        cursor.execute("UPDATE processos SET status_monitoramento = 'PENDENTE' WHERE status_monitoramento IS NULL")
        
        # --- COMECE A COLAR AQUI (na nova linha que você criou) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processo_marcos_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npu TEXT,
                marco_id INTEGER,
                data_atingimento TIMESTAMP,
                tempo_permanencia_dias INTEGER,
                sla_esperado_mediana INTEGER,
                origem_gargalo TEXT,
                observacao_ia TEXT
            )
        ''')

        # ---> COLE AQUI A TABELA DE APRENDIZADO DA IA <---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aprendizados_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processo_numero TEXT,
                erro_apontado TEXT,
                regra_aprendida TEXT,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        colunas_processos = {row[1] for row in cursor.execute("PRAGMA table_info(processos)")}
        novas_colunas = {
            "faixa_ticket": "TEXT",
            "tipo_garantia": "TEXT",
            "produto_origem": "TEXT",
            "marco_atual": "INTEGER DEFAULT 0",
            "score_recuperacao": "NUMERIC"
        }
        
        for nome_coluna, tipo_coluna in novas_colunas.items():
            if nome_coluna not in colunas_processos:
                cursor.execute(f"ALTER TABLE processos ADD COLUMN {nome_coluna} {tipo_coluna}")
        # --- TERMINE DE COLAR AQUI ---

        # (Suas linhas 260 e 261 atuais)
        print("[Database] Tabelas verificadas/criadas com sucesso!")
        print("[Database] Tabelas verificadas/criadas com sucesso!")
    print("[Database] Tabelas verificadas/criadas com sucesso!")
    print("[Database] Tabelas verificadas/criadas com sucesso!")

# Executa a criação ao importar o módulo
if __name__ == "__main__":
    criar_tabelas()