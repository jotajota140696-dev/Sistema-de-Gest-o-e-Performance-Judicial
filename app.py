import os
import re
import sqlite3
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

DIR_DOWNLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

def get_db_connection():
    conn = sqlite3.connect('banco_simj.db')
    conn.row_factory = sqlite3.Row
    return conn


def obter_colunas_tabela(conn, tabela):
    """Retorna as colunas existentes na tabela para evitar erros de SQL."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({tabela})")
        return [row[1] for row in cursor.fetchall()]
    except Exception:
        return []


def executar_motor_ia_e_scores(conn):
    """Atualiza marcos e scores de recuperação na base."""
    cursor = conn.cursor()
    colunas = obter_colunas_tabela(conn, 'processos')

    if 'marco_atual' in colunas:
        try:
            cursor.execute("""
                UPDATE processos
                SET marco_atual = COALESCE((
                    SELECT MAX(h.marco_id) 
                    FROM processo_marcos_historico h 
                    WHERE h.npu = processos.npu 
                       OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(processos.npu, '.', ''), '-', ''), '/', '')
                ), marco_atual, 1)
                WHERE marco_atual IS NULL OR marco_atual = 0
            """)
        except Exception as e:
            print(f"Aviso na sincronização de marcos: {e}")

    if 'score_recuperacao' in colunas:
        try:
            cursor.execute("SELECT npu, marco_atual, situacao_processo FROM processos")
            processos = cursor.fetchall()

            for p in processos:
                npu = p['npu']
                marco = p['marco_atual'] or 1 if 'marco_atual' in colunas else 1
                situacao = (p['situacao_processo'] or '').lower() if 'situacao_processo' in colunas else ''

                base_score = min(10.0, float(marco) * 0.9 + 1.0)
                if any(term in situacao for term in ['bloqueio positivo', 'penhora', 'sisbajud', 'renajud']):
                    base_score = min(10.0, base_score + 1.5)
                if any(term in situacao for term in ['alvará', 'pago', 'liquidado', 'acordo', 'homologado']):
                    base_score = 10.0
                if any(term in situacao for term in ['revisional', 'embargos', 'suspenso']):
                    base_score = max(1.0, base_score - 2.0)

                cursor.execute("UPDATE processos SET score_recuperacao = ? WHERE npu = ?", (round(base_score, 1), npu))

            conn.commit()
        except Exception as e:
            print(f"Aviso no cálculo do Score: {e}")


def obter_dados_filtrados(params):
    """Calcula os indicadores padronizados no formato de Quantidade, Mediana e Meta/Subtexto."""
    conn = get_db_connection()
    executar_motor_ia_e_scores(conn)

    cursor = conn.cursor()
    colunas_proc = obter_colunas_tabela(conn, 'processos')

    # Filtros
    cliente = params.get('cliente', 'TODOS')
    assessoria = params.get('assessoria', 'TODOS')
    parte_ativa = params.get('parte_ativa', '').strip()
    parte_passiva = params.get('parte_passiva', '').strip()
    carteira = params.get('carteira', 'TODAS')

    where_clauses = ["1=1"]
    sql_args = []

    if cliente and cliente != 'TODOS' and 'nome_autor' in colunas_proc:
        where_clauses.append("(nome_autor LIKE ? OR nome_reu LIKE ?)")
        sql_args.extend([f"%{cliente}%", f"%{cliente}%"])

    if assessoria and assessoria != 'TODOS' and 'assessoria' in colunas_proc:
        where_clauses.append("assessoria = ?")
        sql_args.append(assessoria)

    if parte_ativa and 'nome_autor' in colunas_proc:
        where_clauses.append("nome_autor LIKE ?")
        sql_args.append(f"%{parte_ativa}%")

    if parte_passiva:
        conds = []
        if 'nome_reu' in colunas_proc:
            conds.append("nome_reu LIKE ?")
            sql_args.append(f"%{parte_passiva}%")
        if 'npu' in colunas_proc:
            conds.append("npu LIKE ?")
            sql_args.append(f"%{parte_passiva}%")
        if conds:
            where_clauses.append("(" + " OR ".join(conds) + ")")

    if carteira and carteira != 'TODAS' and 'carteira' in colunas_proc:
        where_clauses.append("carteira = ?")
        sql_args.append(carteira)

    where_sql = " WHERE " + " AND ".join(where_clauses)

    cursor.execute(f"SELECT COUNT(*) as total FROM processos {where_sql}", sql_args)
    total_processos = cursor.fetchone()['total'] or 0

    # -------------------------------------------------------------------------
    # KPI 1: ACORDOS HOMOLOGADOS (MÊS)
    # -------------------------------------------------------------------------
    cond_acordo = "(marco_atual >= 8 OR LOWER(COALESCE(situacao_processo, '')) LIKE '%acordo%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%homologad%')" if 'marco_atual' in colunas_proc else "1=1"
    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND {cond_acordo}", sql_args)
    qtd_acordos = cursor.fetchone()['qtd'] or 0

    try:
        cursor.execute(f"""
            SELECT h.tempo_permanencia_dias 
            FROM processo_marcos_historico h
            JOIN processos p ON p.npu = h.npu OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(p.npu, '.', ''), '-', ''), '/', '')
            {where_sql} AND {cond_acordo} AND h.tempo_permanencia_dias > 0
        """, sql_args)
        tempos_acordos = [r['tempo_permanencia_dias'] for r in cursor.fetchall()]
        mediana_acordos = int(np.median(tempos_acordos)) if tempos_acordos else 0
    except Exception:
        mediana_acordos = 0

    # -------------------------------------------------------------------------
    # KPI 2: LEAD TIME MÉDIO (CAUSAS) & ETAPAS
    # -------------------------------------------------------------------------
    lead_time_dias, mediana_leadtime = 0, 0
    etapa1_dias, etapa2_dias, etapa3_dias = 0, 0, 0

    try:
        cursor.execute(f"""
            SELECT h.marco_id, h.tempo_permanencia_dias 
            FROM processo_marcos_historico h
            JOIN processos p ON p.npu = h.npu OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(p.npu, '.', ''), '-', ''), '/', '')
            {where_sql} AND h.tempo_permanencia_dias IS NOT NULL AND h.tempo_permanencia_dias > 0
        """, sql_args)
        rows_lt = cursor.fetchall()
        tempos_todos = [r['tempo_permanencia_dias'] for r in rows_lt]

        if tempos_todos:
            lead_time_dias = int(np.mean(tempos_todos))
            mediana_leadtime = int(np.median(tempos_todos))

        tempos_e1 = [r['tempo_permanencia_dias'] for r in rows_lt if r['marco_id'] <= 2]
        tempos_e2 = [r['tempo_permanencia_dias'] for r in rows_lt if 3 <= r['marco_id'] <= 5]
        tempos_e3 = [r['tempo_permanencia_dias'] for r in rows_lt if r['marco_id'] >= 6]

        etapa1_dias = int(np.mean(tempos_e1)) if tempos_e1 else 0
        etapa2_dias = int(np.mean(tempos_e2)) if tempos_e2 else 0
        etapa3_dias = int(np.mean(tempos_e3)) if tempos_e3 else 0
    except Exception as e:
        print(f"Aviso no lead time: {e}")

    # -------------------------------------------------------------------------
    # KPI 3: EFICIÊNCIA SISBAJUD/RENAJUD (COM QUANTIDADE)
    # -------------------------------------------------------------------------
    cond_constricao = "(marco_atual BETWEEN 3 AND 5 OR LOWER(COALESCE(situacao_processo, '')) LIKE '%bloqueio%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%penhora%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%sisbajud%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%renajud%')" if 'marco_atual' in colunas_proc else "1=1"
    
    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND {cond_constricao}", sql_args)
    qtd_constricao = cursor.fetchone()['qtd'] or 0

    try:
        cursor.execute(f"""
            SELECT h.tempo_permanencia_dias 
            FROM processo_marcos_historico h
            JOIN processos p ON p.npu = h.npu OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(p.npu, '.', ''), '-', ''), '/', '')
            {where_sql} AND {cond_constricao} AND h.tempo_permanencia_dias > 0
        """, sql_args)
        tempos_sis = [r['tempo_permanencia_dias'] for r in cursor.fetchall()]
        mediana_sisbajud = int(np.median(tempos_sis)) if tempos_sis else 0
    except Exception:
        mediana_sisbajud = 0

    # -------------------------------------------------------------------------
    # KPI 4: VOLUME EM RISCO (PASSIVO) - CLIENTE É RÉU
    # -------------------------------------------------------------------------
    cond_passivo = "(LOWER(COALESCE(situacao_processo, '')) LIKE '%revisional%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%embargo%' OR LOWER(COALESCE(nome_reu, '')) LIKE '%cresol%')"
    cond_favoravel = f"{cond_passivo} AND (LOWER(COALESCE(situacao_processo, '')) LIKE '%improceden%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%favoravel%' OR LOWER(COALESCE(situacao_processo, '')) LIKE '%vitoria%')"

    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND {cond_passivo}", sql_args)
    qtd_passivo = cursor.fetchone()['qtd'] or 0

    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND {cond_favoravel}", sql_args)
    qtd_favoravel = cursor.fetchone()['qtd'] or 0

    try:
        cursor.execute(f"""
            SELECT h.tempo_permanencia_dias 
            FROM processo_marcos_historico h
            JOIN processos p ON p.npu = h.npu OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(p.npu, '.', ''), '-', ''), '/', '')
            {where_sql} AND {cond_favoravel} AND h.tempo_permanencia_dias > 0
        """, sql_args)
        tempos_fav = [r['tempo_permanencia_dias'] for r in cursor.fetchall()]
        mediana_favoravel = int(np.median(tempos_fav)) if tempos_fav else 0
    except Exception:
        mediana_favoravel = 0

    kpis = {
        # KPI 1: Acordos Homologados
        "acordos_qtd": f"{qtd_acordos} Acordos",
        "acordos_mediana": f"Mediana: {mediana_acordos} dias",
        "acordos_meta": "Meta Interna: 50 acordos/mês",

        # KPI 2: Lead Time
        "lead_time": f"{lead_time_dias} Dias",
        "mediana_lead_time": f"Mediana: {mediana_leadtime} dias",
        "meta_lead_time": "Meta Interna: 30 dias",
        "lead_time_etapas": {
            "etapa1": f"{etapa1_dias} dias",
            "etapa2": f"{etapa2_dias} dias",
            "etapa3": f"{etapa3_dias} dias"
        },

        # KPI 3: Eficiência SISBAJUD/RENAJUD
        "sisbajud_qtd": f"{qtd_constricao} Medidas Efetivadas",
        "sisbajud_mediana": f"Mediana: {mediana_sisbajud} dias",
        "sisbajud_meta": "Meta Interna: 40 penhoras/mês",

        # KPI 4: Volume em Risco (Passivo)
        "passivo_qtd": f"{qtd_passivo} Processos",
        "passivo_mediana": f"Mediana Improcedência: {mediana_favoravel} dias",
        "passivo_favoravel_sub": f"{qtd_favoravel} Decisões Favoráveis (Improcedência)"
    }

    # -------------------------------------------------------------------------
    # FUNIL DE RECUPERAÇÃO
    # -------------------------------------------------------------------------
    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND (marco_atual BETWEEN 0 AND 2 OR marco_atual IS NULL)", sql_args)
    f1_qtd = cursor.fetchone()['qtd'] or 0

    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND marco_atual BETWEEN 3 AND 5", sql_args)
    f2_qtd = cursor.fetchone()['qtd'] or 0

    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND marco_atual BETWEEN 6 AND 7", sql_args)
    f3_qtd = cursor.fetchone()['qtd'] or 0

    cursor.execute(f"SELECT COUNT(*) as qtd FROM processos {where_sql} AND marco_atual BETWEEN 8 AND 10", sql_args)
    f4_qtd = cursor.fetchone()['qtd'] or 0

    den = total_processos if total_processos > 0 else 1

    funil = {
        "total_distribuidos": total_processos,
        "fase1_qtd": f1_qtd,
        "fase1_pct": round((f1_qtd / den * 100), 1),
        "fase2_qtd": f2_qtd,
        "fase2_pct": round((f2_qtd / den * 100), 1),
        "fase3_qtd": f3_qtd,
        "fase3_pct": round((f3_qtd / den * 100), 1),
        "fase4_qtd": f4_qtd,
        "fase4_pct": round((f4_qtd / den * 100), 1),
    }

    # -------------------------------------------------------------------------
    # RANQUEAMENTO 360º DE ASSESSORIAS & BENCHMARK
    # -------------------------------------------------------------------------
    col_ass = "COALESCE(NULLIF(assessoria, ''), 'Jurídico Interno')" if 'assessoria' in colunas_proc else "'Jurídico Interno'"
    col_score = "AVG(score_recuperacao)" if 'score_recuperacao' in colunas_proc else "7.5"

    cursor.execute(f"""
        SELECT 
            {col_ass} as nome,
            COUNT(*) as total_casos,
            COALESCE(ROUND({col_score} * 10, 1), 75.0) as score_360
        FROM processos
        {where_sql}
        GROUP BY {col_ass}
        ORDER BY score_360 DESC, total_casos DESC
    """, sql_args)
    assessorias_rows = cursor.fetchall()

    assessorias_ranking = []
    medals = ["🥇 1º", "🥈 2º", "🥉 3º"]

    for idx, r in enumerate(assessorias_rows):
        pos = medals[idx] if idx < 3 else f"{idx+1}º"
        sc = r['score_360']
        st_sla = "Acima da Mediana" if sc >= 70.0 else "Abaixo da Mediana"
        st_clr = "text-emerald-400" if sc >= 70.0 else "text-amber-400"

        # Cálculo da Velocidade nos Êxitos dos Atos (Lead Time Médio do Escritório)
        try:
            cursor.execute("""
                SELECT AVG(h.tempo_permanencia_dias) as media_dias
                FROM processo_marcos_historico h
                JOIN processos p ON p.npu = h.npu OR REPLACE(REPLACE(REPLACE(h.npu, '.', ''), '-', ''), '/', '') = REPLACE(REPLACE(REPLACE(p.npu, '.', ''), '-', ''), '/', '')
                WHERE p.assessoria = ? AND h.tempo_permanencia_dias > 0
            """, (r['nome'],))
            row_v = cursor.fetchone()
            vel_dias = int(row_v['media_dias']) if row_v and row_v['media_dias'] else 35
        except Exception:
            vel_dias = 35

        assessorias_ranking.append({
            "posicao": pos,
            "nome": r['nome'],
            "score_360": f"{sc:.1f}",
            "velocidade_exitos": f"{vel_dias} dias méd.",
            "sucesso_bloqueio": f"{min(98.0, round(sc * 0.85, 1))}%",
            "passivos_perdas": "Baixo Risco" if sc >= 70.0 else "Alerta Revisional",
            "status_sla": st_sla,
            "status_class": st_clr
        })

    # -------------------------------------------------------------------------
    # PRONTUÁRIOS & DIAGNÓSTICO IA
    # -------------------------------------------------------------------------
    cursor.execute(f"SELECT * FROM processos {where_sql} ORDER BY rowid DESC", sql_args)
    processos_lista = cursor.fetchall()

    processos_prontuario = []
    for proc in processos_lista:
        p_dict = dict(proc)
        processos_prontuario.append({
            "npu": p_dict.get('npu', 'Sem NPU'),
            "credor": p_dict.get('nome_autor') or "Cresol",
            "devedor": p_dict.get('nome_reu') or "Devedor não informado",
            "comarca": p_dict.get('juizo') or "Não informada",
            "fase": p_dict.get('situacao_processo') or f"Marco M{p_dict.get('marco_atual', 1)}",
            "scoring": f"{p_dict.get('score_recuperacao', 7.5):.1f}",
            "marco_atual": p_dict.get('marco_atual', 1),
            "assessoria": p_dict.get('assessoria') or "Jurídico Interno"
        })

    alertas_ia = [
        {
            "id": "diagnostico_base",
            "tipo": "Operação Regular",
            "tipo_class": "text-emerald-400",
            "border_class": "border-emerald-500/30 bg-emerald-500/5",
            "icon": "fa-circle-check",
            "titulo": f"Base de dados analisada ({total_processos} processos monitorados).",
            "descricao": "Clique para visualizar a relação de processos mapeados pela IA."
        }
    ]

    conn.close()

    return {
        "kpis": kpis,
        "funil": funil,
        "assessorias_ranking": assessorias_ranking,
        "processos_prontuario": processos_prontuario,
        "alertas_ia": alertas_ia
    }


@app.route('/')
def index():
    dados = obter_dados_filtrados(request.args)
    return render_template('index.html', dados=dados)


@app.route('/api/dados', methods=['GET'])
def api_dados():
    dados = obter_dados_filtrados(request.args)
    return jsonify(dados)


@app.route('/api/processo/<path:npu>', methods=['GET'])
def api_detalhe_processo(npu):
    conn = get_db_connection()
    cursor = conn.cursor()
    npu_limpo = re.sub(r'\D', '', str(npu))

    cursor.execute("""
        SELECT * FROM processos 
        WHERE npu = ? OR REPLACE(REPLACE(REPLACE(npu, '.', ''), '-', ''), '/', '') = ?
    """, (npu, npu_limpo))
    proc = cursor.fetchone()

    if not proc:
        conn.close()
        return jsonify({"erro": f"Processo {npu} não encontrado."}), 404

    npu_banco = proc['npu']

    try:
        cursor.execute("SELECT * FROM movimentos WHERE npu = ? ORDER BY id DESC", (npu_banco,))
        movs = cursor.fetchall()
    except Exception:
        movs = []

    conn.close()
    return jsonify({"processo": dict(proc), "movimentos": [dict(m) for m in movs]})


@app.route('/api/diagnostico_processos/<path:tipo_alerta>', methods=['GET'])
def api_diagnostico_processos(tipo_alerta):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processos ORDER BY rowid DESC")
    processos = cursor.fetchall()
    conn.close()

    lista = []
    for p in processos:
        p_dict = dict(p)
        lista.append({
            "npu": p_dict.get('npu', 'Sem NPU'),
            "credor": p_dict.get('nome_autor') or "Cresol",
            "devedor": p_dict.get('nome_reu') or "Devedor não informado",
            "assessoria": p_dict.get('assessoria') or "Jurídico Interno",
            "atraso_dias": f"Marco M{p_dict.get('marco_atual', 1)}",
            "recomendacao": p_dict.get('situacao_processo') or "Monitoramento Ativo"
        })

    return jsonify({"alerta": tipo_alerta, "processos": lista})


@app.route('/downloads/<path:filename>')
def servir_download_pdf(filename):
    return send_from_directory(DIR_DOWNLOADS, filename)


# ---> COLE A NOVA ROTA AQUI <---
@app.route('/api/corrigir-ia', methods=['POST'])
def corrigir_ia():
    dados = request.json
    processo_numero = dados.get("numero_processo")
    correcao_usuario = dados.get("correcao") # Ex: "Confundiu despacho inicial com citação"
    regra_derivada = dados.get("regra")      # Ex: "Despachos com 'cite-se e após' tratam-se de citação..."
    
    if not processo_numero:
        return jsonify({"erro": "Número do processo não informado."}), 400
        
    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO aprendizados_ia (processo_numero, erro_apontado, regra_aprendida)
               VALUES (?, ?, ?)""",
            (processo_numero, correcao_usuario, regra_derivada)
        )
        conn.commit()
        return jsonify({"sucesso": True, "mensagem": "Feedback e aprendizado registados com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)