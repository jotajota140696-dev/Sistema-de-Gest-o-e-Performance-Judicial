import sqlite3
import subprocess
import sys
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import streamlit as st

import database
from main import main as executar_monitoramento
from services import classificador
from services.importador import importar_processos_excel
from services.eproc_importador import extrair_eventos_eproc_html
from services.enriquecedor import fontes_para_processo

st.set_page_config(page_title="RECUPERA-CRED | Dashboard", layout="wide", page_icon="⚖️")
database.criar_tabelas()

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 85% 0%, rgba(14, 116, 144, 0.18), transparent 34%), linear-gradient(135deg, #050914 0%, #08111f 52%, #10172a 100%);
            color: #edf2f7;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, h4, h5, p, div, span, label {
            color: #edf2f7 !important;
        }
        .stTabs [role="tablist"] {
            background: rgba(15, 23, 42, 0.85);
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        }
        .stTabs [role="tab"] {
            color: #cbd5e1;
            font-weight: 600;
            padding: 0.8rem 1rem;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            color: #f87171;
            border-bottom: 2px solid #f87171;
        }
        .stMetric {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(12, 42, 61, 0.72));
            border: 1px solid rgba(45, 212, 191, 0.22);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 0 24px rgba(14, 116, 144, 0.1);
        }
        div[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.98);
        }
        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            border: none;
        }
        .stDataFrame, .stSelectbox, .stTextInput, .stNumberInput {
            background: rgba(15, 23, 42, 0.5);
        }
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMetric"]) {
            transition: transform 180ms ease, filter 180ms ease;
        }
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMetric"]):hover {
            transform: translateY(-2px);
            filter: brightness(1.12);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================
# FUNÇÕES DE BANCO
# ==========================
def carregar_resumo_processos():
    with database.conectar() as conn:
        df = pd.read_sql_query(
            """
            SELECT p.npu, p.tribunal, p.assessoria, p.status_monitoramento,
                   p.data_ultima_atualizacao,
                     p.nome_autor, p.nome_reu, p.papel_cliente, p.relacao_carteira,
                     p.juizo, p.assuntos, p.situacao_processo,
                   c.nome_razasocial AS cliente,
                   pr.nome AS prestador
            FROM processos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN prestadores pr ON pr.id = p.prestador_id
            ORDER BY p.data_ultima_atualizacao DESC
            """,
            conn,
        )
    return df


def carregar_movimentos(npu):
    with database.conectar() as conn:
        df = pd.read_sql_query(
            """
                 SELECT codigo_movimento, nome_movimento, descricao_movimento,
                         numero_evento, usuario_evento, documentos_evento,
                         parte_evento, advogado_evento, origem_evento,
                         fonte_detalhe, confianca_evento, data_movimento
            FROM movimentos
            WHERE npu = ?
            ORDER BY data_movimento DESC
            """,
            conn,
            params=(npu,),
        )
    if df.empty:
        return df

    df["data_movimento"] = pd.to_datetime(df["data_movimento"], errors="coerce")
    df["marco_classificado"] = df["codigo_movimento"].apply(
        lambda codigo: classificador.classificar_marco(codigo) or "Desconhecido"
    )
    return df


def carregar_kpis():
    with database.conectar() as conn:
        total_processos = conn.execute("SELECT COUNT(*) FROM processos").fetchone()[0]
        pendentes = conn.execute(
            "SELECT COUNT(*) FROM processos WHERE status_monitoramento = 'PENDENTE'"
        ).fetchone()[0]
        atualizados = conn.execute(
            "SELECT COUNT(*) FROM processos WHERE status_monitoramento = 'ATUALIZADO'"
        ).fetchone()[0]
        total_movimentos = conn.execute("SELECT COUNT(*) FROM movimentos").fetchone()[0]
    return total_processos, pendentes, atualizados, total_movimentos


def carregar_inteligencia_carteira():
    """Calcula score operacional com base nos eventos realmente capturados."""
    processos = carregar_resumo_processos()
    if processos.empty:
        return processos, pd.DataFrame()

    with database.conectar() as conn:
        movimentos = pd.read_sql_query(
            """SELECT npu, data_movimento, codigo_movimento, descricao_movimento,
            fonte_detalhe FROM movimentos""",
            conn,
        )

    movimentos["data_movimento"] = pd.to_datetime(movimentos["data_movimento"], errors="coerce")
    hoje = pd.Timestamp.now(tz=None).tz_localize(None)
    resumo = movimentos.groupby("npu").agg(
        movimentos=("npu", "size"),
        descricoes=("descricao_movimento", lambda coluna: coluna.notna().sum()),
        fontes=("fonte_detalhe", lambda coluna: coluna.notna().sum()),
        ultimo_movimento=("data_movimento", "max"),
        primeiro_movimento=("data_movimento", "min"),
    ).reset_index()
    resumo["dias_sem_movimento"] = (hoje - resumo["ultimo_movimento"].dt.tz_localize(None)).dt.days.clip(lower=0)
    resumo["cobertura_dados"] = (resumo["descricoes"] / resumo["movimentos"] * 100).round(1)
    resumo["cadencia"] = ((resumo["movimentos"] / ((hoje - resumo["primeiro_movimento"].dt.tz_localize(None)).dt.days.clip(lower=1))) * 30).round(1)
    resumo["saude"] = (100 - resumo["dias_sem_movimento"].clip(upper=60) / 60 * 45 + resumo["cobertura_dados"] * 0.35 + resumo["cadencia"].clip(upper=10) * 2).clip(0, 100).round(1)
    resultado = processos.merge(resumo, on="npu", how="left")
    resultado["saude"] = resultado["saude"].fillna(0)
    resultado["cobertura_dados"] = resultado["cobertura_dados"].fillna(0)
    resultado["dias_sem_movimento"] = resultado["dias_sem_movimento"].fillna(999)
    resultado["faixa_risco"] = pd.cut(
        resultado["saude"], bins=[-1, 40, 70, 101], labels=["Crítico", "Atenção", "Controlado"]
    )
    return resultado, movimentos


def carregar_ranking_real():
    carteira, _ = carregar_inteligencia_carteira()
    if carteira.empty:
        return pd.DataFrame()
    ranking = carteira.groupby(carteira["assessoria"].fillna("Não definida")).agg(
        processos=("npu", "count"),
        saude_media=("saude", "mean"),
        cobertura_media=("cobertura_dados", "mean"),
        processos_controlados=("faixa_risco", lambda serie: (serie == "Controlado").sum()),
    ).reset_index().rename(columns={"assessoria": "Assessoria"})
    ranking["Score"] = (ranking["saude_media"] * 0.55 + ranking["cobertura_media"] * 0.25 + ranking["processos_controlados"] / ranking["processos"] * 100 * 0.20).round(1)
    return ranking.sort_values("Score", ascending=False).reset_index(drop=True)


# ==========================
# SIDEBAR
# ==========================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "dashboard"


def navegar(pagina):
    st.session_state["pagina"] = pagina
    st.session_state["cadastros_abertos"] = pagina == "cadastros"


with st.sidebar:
    st.markdown("### ⚖️ RECUPERA-CRED")
    st.caption("Menu Principal")

    st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state["pagina"] == "dashboard" else "secondary", on_click=navegar, args=("dashboard",))
    st.button("⚖️ Fila de Processos", use_container_width=True, type="primary" if st.session_state["pagina"] == "fila" else "secondary", on_click=navegar, args=("fila",))
    st.button("👥 Assessorias", use_container_width=True, type="primary" if st.session_state["pagina"] == "assessorias" else "secondary", on_click=navegar, args=("assessorias",))
    st.button("💰 Financeiro", use_container_width=True, type="primary" if st.session_state["pagina"] == "financeiro" else "secondary", on_click=navegar, args=("financeiro",))
    st.button("🧩 Cadastros", use_container_width=True, type="primary" if st.session_state["pagina"] == "cadastros" else "secondary", on_click=navegar, args=("cadastros",))

    st.divider()
    st.markdown("### 🤖 Motor de Automação")
    st.caption("Consulta em lote API DataJud CNJ")

    if st.button("▶ Executar Monitoramento", use_container_width=True, type="primary"):
        with st.spinner("Acionando robô de captura..."):
            resultado = subprocess.run(
                [sys.executable, "main.py"],
                capture_output=True,
                text=True,
            )
            if resultado.returncode == 0:
                st.success("Varredura concluída com sucesso!")
            else:
                st.error("Erro na execução. Verifique os logs.")


# ==========================
# CABEÇALHO
# ==========================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Painel de Desempenho Institucional")
with col2:
    st.markdown(
        "<div style='text-align: right; padding-top: 15px;'><span style='background-color: #dbeafe; color: #1d4ed8; padding: 5px 10px; border-radius: 20px; font-weight: bold;'>CA - Gestão Estratégica</span></div>",
        unsafe_allow_html=True,
    )

st.divider()


def render_pagina_operacional(pagina):
    carteira, _ = carregar_inteligencia_carteira()
    if pagina == "fila":
        st.title("Fila de Processos")
        st.caption("Prioridade operacional por saúde, risco e tempo sem movimentação.")
        if carteira.empty:
            st.info("Nenhum processo cadastrado.")
            return
        filtro = st.multiselect("Risco", ["Crítico", "Atenção", "Controlado"], default=["Crítico", "Atenção", "Controlado"])
        fila = carteira[carteira["faixa_risco"].isin(filtro)].sort_values("saude")
        st.dataframe(
            fila[["npu", "cliente", "nome_autor", "nome_reu", "papel_cliente", "relacao_carteira", "assessoria", "saude", "faixa_risco", "dias_sem_movimento"]].rename(
                columns={"npu": "NPU", "cliente": "Cliente", "nome_autor": "Autor", "nome_reu": "Réu", "papel_cliente": "Papel", "relacao_carteira": "Relação", "assessoria": "Assessoria", "saude": "Saúde", "faixa_risco": "Risco", "dias_sem_movimento": "Dias sem movimento"}
            ), hide_index=True, use_container_width=True
        )
    elif pagina == "assessorias":
        st.title("Assessorias")
        st.caption("Comparativo de saúde, cobertura e processos controlados.")
        ranking = carregar_ranking_real()
        if ranking.empty:
            st.info("Cadastre processos para formar o ranking.")
        else:
            st.dataframe(ranking, hide_index=True, use_container_width=True)
            fig = px.bar(ranking, x="Assessoria", y="Score", color="Score", color_continuous_scale=["#fb7185", "#fbbf24", "#34d399"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#e2e8f0"})
            st.plotly_chart(fig, use_container_width=True)
    elif pagina == "financeiro":
        st.title("Financeiro")
        st.caption("Painel preparado para resultados de recuperação e valores por processo.")
        st.info("Ainda não há coluna financeira na planilha importada. O sistema já mantém a carteira e os eventos; ao incluir valor da causa, valor recuperado e saldo, os indicadores financeiros serão calculados aqui.")
        st.metric("Processos na carteira", len(carteira))
    else:
        st.title("Cadastros e carteira")
        st.caption("Área operacional aberta pelo botão Cadastros no menu lateral.")
        clientes_tab, prestadores_tab, processos_tab, import_tab = st.tabs(["Clientes", "Prestadores", "Processos", "Importar Excel"])
        with clientes_tab:
            with st.form("cliente_operacional"):
                nome = st.text_input("Nome ou razão social")
                documento = st.text_input("CPF/CNPJ")
                email = st.text_input("E-mail")
                telefone = st.text_input("Telefone")
                if st.form_submit_button("Cadastrar cliente"):
                    with database.conectar() as conn:
                        conn.execute("INSERT INTO clientes (nome_razasocial, cpf_cnpj, email, telefone) VALUES (?, ?, ?, ?)", (nome.strip(), documento.strip(), email.strip(), telefone.strip()))
                    st.success("Cliente cadastrado.")
        with prestadores_tab:
            with st.form("prestador_operacional"):
                nome = st.text_input("Nome")
                documento = st.text_input("CPF/OAB")
                tipo = st.text_input("Tipo de serviço")
                telefone = st.text_input("Telefone")
                if st.form_submit_button("Cadastrar prestador"):
                    with database.conectar() as conn:
                        conn.execute("INSERT INTO prestadores (nome, cpf_oab, tipo_servico, telefone) VALUES (?, ?, ?, ?)", (nome.strip(), documento.strip(), tipo.strip(), telefone.strip()))
                    st.success("Prestador cadastrado.")
        with processos_tab:
            st.dataframe(carteira[["npu", "cliente", "nome_autor", "nome_reu", "papel_cliente", "relacao_carteira", "assessoria", "status_monitoramento"]], hide_index=True, use_container_width=True)
        with import_tab:
            st.write("Aceita o Excel exportado com Nº Processo, Autor, Réu, Último Evento, Situação e ASSESSORIA.")
            arquivo = st.file_uploader("Selecione um arquivo Excel", type=["xlsx", "xls"], key="carteira_excel")
            if arquivo and st.button("Importar e vincular carteira"):
                resultado = importar_processos_excel(arquivo)
                st.success(f"{resultado['inseridos']} inserido(s) e {resultado.get('atualizados', 0)} atualizado(s).")
                if resultado["erros"]:
                    st.warning("Linhas pendentes de vínculo:\n" + "\n".join(resultado["erros"]))


if st.session_state["pagina"] != "dashboard":
    render_pagina_operacional(st.session_state["pagina"])
    st.stop()

# adaptação para o mockup mais executivo
# ==========================
# TABS
# ==========================
tab_visao, tab_jornada, tab_c3, tab_benchmarks, tab_meritocracia, tab_ranking = st.tabs(
    [
        "📊 Visão Geral",
        "⏳ Linha do Tempo (Jornada de Ouro)",
        "🎛️ Centro de Comando C3",
        "🎯 Indicadores & Benchmarks",
        "⚖️ Meritocracia & Regras",
        "🏆 Ranking de Assessorias",
    ]
)

# ==========================
# ABA 1 - VISÃO GERAL
# ==========================
with tab_visao:
    carteira, movimentos_carteira = carregar_inteligencia_carteira()
    total_processos, pendentes, atualizados, total_movimentos = carregar_kpis()
    media_saude = carteira["saude"].mean() if not carteira.empty else 0
    criticos = int((carteira["faixa_risco"] == "Crítico").sum()) if not carteira.empty else 0
    cobertura = carteira["cobertura_dados"].mean() if not carteira.empty else 0

    st.markdown("## Command center da carteira")
    st.caption("Uma leitura operacional: velocidade, cobertura de informação e risco de estagnação.")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Carteira ativa", total_processos)
    c2.metric("Saúde média", f"{media_saude:.1f}/100")
    c3.metric("Casos críticos", criticos)
    c4.metric("Cobertura de dados", f"{cobertura:.1f}%")
    c5.metric("Movimentos", total_movimentos)
    contra_cliente = int((carteira["relacao_carteira"] == "processo contra o cliente").sum()) if not carteira.empty else 0
    cobrancas_cliente = int((carteira["relacao_carteira"] == "cobrança do cliente").sum()) if not carteira.empty else 0
    alerta_col1, alerta_col2 = st.columns(2)
    alerta_col1.metric("Cobranças do cliente", cobrancas_cliente)
    alerta_col2.metric("Processos contra o cliente", contra_cliente, delta="atenção jurídica" if contra_cliente else None, delta_color="inverse")

    if not carteira.empty:
        st.markdown("### Radar 3D de eficiência")
        radar = carteira.copy()
        radar["cliente_visual"] = radar["cliente"].fillna("Cliente não informado")
        fig_radar = px.scatter_3d(
            radar,
            x="movimentos",
            y="cobertura_dados",
            z="dias_sem_movimento",
            color="saude",
            size="saude",
            hover_name="npu",
            hover_data={"cliente_visual": True, "assessoria": True, "faixa_risco": True, "saude": ":.1f"},
            color_continuous_scale=["#fb7185", "#fbbf24", "#34d399"],
            labels={"movimentos": "Movimentos", "cobertura_dados": "Cobertura (%)", "dias_sem_movimento": "Dias sem movimento"},
        )
        fig_radar.update_layout(
            height=520,
            paper_bgcolor="rgba(0,0,0,0)",
            scene={"bgcolor": "rgba(0,0,0,0)", "xaxis": {"gridcolor": "#223047"}, "yaxis": {"gridcolor": "#223047"}, "zaxis": {"gridcolor": "#223047"}},
            font={"color": "#dbeafe"},
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("### Fila inteligente")
        filtros = st.multiselect("Mostrar faixas", ["Crítico", "Atenção", "Controlado"], default=["Crítico", "Atenção", "Controlado"])
        fila = carteira[carteira["faixa_risco"].isin(filtros)].copy()
        fila["prioridade"] = fila["saude"].rank(method="first", ascending=True).astype(int)
        fila = fila.sort_values("saude")
        st.dataframe(
            fila[["prioridade", "npu", "cliente", "nome_autor", "nome_reu", "papel_cliente", "relacao_carteira", "prestador", "assessoria", "saude", "faixa_risco", "dias_sem_movimento", "cobertura_dados"]].rename(
                columns={"prioridade": "Prioridade", "npu": "NPU", "cliente": "Cliente", "nome_autor": "Autor", "nome_reu": "Réu", "papel_cliente": "Papel do cliente", "relacao_carteira": "Relação", "prestador": "Prestador", "assessoria": "Assessoria", "saude": "Saúde", "faixa_risco": "Risco", "dias_sem_movimento": "Dias sem movimento", "cobertura_dados": "Cobertura (%)"}
            ),
            hide_index=True,
            use_container_width=True,
        )

# ==========================
# ABA 2 - LINHA DO TEMPO
# ==========================
with tab_jornada:
    st.markdown("### ⏳ Jornada de Ouro do Processo")
    st.caption("Selecione um NPU capturado no banco de dados para visualizar sua evolução processual.")

    df_processos = carregar_resumo_processos()
    if not df_processos.empty:
        filtros_col1, filtros_col2 = st.columns(2)
        with filtros_col1:
            assessorias = ["Todas"] + sorted(df_processos["assessoria"].dropna().unique().tolist())
            assessoria_filtro = st.selectbox("Assessoria", assessorias)
        with filtros_col2:
            if assessoria_filtro == "Todas":
                processos_filtrados = df_processos
            else:
                processos_filtrados = df_processos[df_processos["assessoria"] == assessoria_filtro]
            lista_npus = ["Todos"] + processos_filtrados["npu"].tolist()
            npu_selecionado = st.selectbox("NPU", lista_npus)

        npu_final = npu_selecionado if npu_selecionado != "Todos" else (processos_filtrados["npu"].iloc[0] if not processos_filtrados.empty else None)

        if npu_final:
            df_mov = carregar_movimentos(npu_final)
            if not df_mov.empty:
                processo_info = df_processos[df_processos["npu"] == npu_final].iloc[0]
                st.markdown("#### Caso selecionado")
                resumo_col1, resumo_col2, resumo_col3, resumo_col4 = st.columns(4)
                resumo_col1.metric("Cliente", processo_info["cliente"] or "Não informado")
                resumo_col2.metric("Prestador", processo_info["prestador"] or "Não informado")
                resumo_col3.metric("Assessoria", processo_info["assessoria"] or "Não definida")
                resumo_col4.metric("Status", processo_info["status_monitoramento"] or "PENDENTE")
                papel_col1, papel_col2, papel_col3 = st.columns(3)
                papel_col1.info(f"**Autor:** {processo_info['nome_autor'] or 'Não informado'}")
                papel_col2.info(f"**Réu:** {processo_info['nome_reu'] or 'Não informado'}")
                relacao = processo_info["relacao_carteira"] or "Relação não identificada"
                (papel_col3.error if relacao == "processo contra o cliente" else papel_col3.success)(f"**Relação:** {relacao}")

                st.markdown("#### Complementações de informações")
                complemento_col1, complemento_col2, complemento_col3, complemento_col4 = st.columns(4)
                complemento_col1.metric("Descrições complementadas", int(df_mov["descricao_movimento"].notna().sum()))
                complemento_col2.metric("Partes identificadas", int(df_mov["parte_evento"].notna().sum()))
                complemento_col3.metric("Advogados identificados", int(df_mov["advogado_evento"].notna().sum()))
                complemento_col4.metric("Documentos identificados", int(df_mov["documentos_evento"].notna().sum()))

                fontes_visiveis = (
                    df_mov["fonte_detalhe"].fillna("Não informada")
                    .value_counts()
                    .rename_axis("Fonte")
                    .reset_index(name="Eventos")
                )
                st.caption("Fontes efetivamente registradas nos eventos deste processo")
                st.dataframe(fontes_visiveis, hide_index=True, use_container_width=True)

                with database.conectar() as conn:
                    evidencias = pd.read_sql_query(
                        """SELECT numero_evento, fonte, tipo, resumo, url, criado_em
                        FROM evidencias_processo WHERE npu = ?
                        ORDER BY criado_em DESC""",
                        conn,
                        params=(npu_final,),
                    )
                if not evidencias.empty:
                    st.markdown("**Evidências públicas usadas nas complementações**")
                    st.dataframe(
                        evidencias.rename(
                            columns={
                                "numero_evento": "Evento",
                                "fonte": "Fonte",
                                "tipo": "Tipo",
                                "resumo": "Informação encontrada",
                                "url": "Link da fonte",
                                "criado_em": "Registrado em",
                            }
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )

                eventos_complementados = df_mov[df_mov["descricao_movimento"].notna()][
                    ["numero_evento", "data_movimento", "nome_movimento", "descricao_movimento", "fonte_detalhe", "confianca_evento"]
                ].copy()
                if not eventos_complementados.empty:
                    with st.expander("Ver eventos com descrição complementar", expanded=True):
                        st.dataframe(
                            eventos_complementados.rename(
                                columns={
                                    "numero_evento": "Evento",
                                    "data_movimento": "Data/Hora",
                                    "nome_movimento": "Movimento DataJud",
                                    "descricao_movimento": "Complementação",
                                    "fonte_detalhe": "Fonte",
                                    "confianca_evento": "Confiança",
                                }
                            ),
                            hide_index=True,
                            use_container_width=True,
                        )
                else:
                    st.info("Este processo ainda não possui descrição complementar além do nome oficial do DataJud.")

                movimentos_arvore = df_mov.sort_values("data_movimento", ascending=True).reset_index(drop=True)
                st.markdown("#### Árvore de recuperação e conformidade")
                data_anterior = None
                for indice, evento in movimentos_arvore.iterrows():
                    data_evento = evento["data_movimento"]
                    intervalo = None
                    if data_anterior is not None and pd.notna(data_evento):
                        intervalo = (data_evento - data_anterior).days
                    data_anterior = data_evento if pd.notna(data_evento) else data_anterior
                    descricao_evento = evento["nome_movimento"] or f"Movimento CNJ {evento['codigo_movimento']}"
                    if pd.notna(evento["descricao_movimento"]) and evento["descricao_movimento"]:
                        descricao_evento += f" - {evento['descricao_movimento']}"
                    conformidade = "Dentro do acompanhamento" if intervalo is None or intervalo <= 30 else "Atenção: intervalo acima de 30 dias"
                    with st.expander(
                        f"{int(evento['numero_evento']) if pd.notna(evento['numero_evento']) else indice + 1}  |  {data_evento.strftime('%d/%m/%Y %H:%M') if pd.notna(data_evento) else 'Sem data'}  |  {descricao_evento}",
                        expanded=indice == len(movimentos_arvore) - 1,
                    ):
                        detalhe_col1, detalhe_col2 = st.columns([3, 1])
                        detalhe_col1.write(f"**Marco:** {evento['marco_classificado']}")
                        detalhe_col1.write(f"**Usuário:** {evento['usuario_evento'] or 'Não informado pelo DataJud'}")
                        detalhe_col1.write(f"**Documentos:** {evento['documentos_evento'] or 'Não informado pelo DataJud'}")
                        detalhe_col1.write(f"**Parte:** {evento['parte_evento'] or 'Não identificado pela fonte'}")
                        detalhe_col1.write(f"**Advogado:** {evento['advogado_evento'] or 'Não identificado pela fonte'}")
                        detalhe_col1.caption(f"Origem da atribuição: {evento['origem_evento'] or 'DataJud sem identificação de partes'}")
                        with detalhe_col1.popover("🔎 Ver origem da informação"):
                            st.write(f"**Fonte:** {evento['fonte_detalhe'] or 'Não registrada'}")
                            st.write(f"**Confiança:** {evento['confianca_evento'] or 'Não classificada'}")
                            st.write(f"**Origem da atribuição:** {evento['origem_evento'] or 'Não informada'}")
                            st.caption(
                                "O sistema não atribui parte ou advogado quando a fonte consultada não fornece esse vínculo."
                            )
                            st.markdown("**Fontes públicas consultáveis**")
                            for fonte in fontes_para_processo(npu_final):
                                st.markdown(
                                    f"- [{fonte['nome']}]({fonte['url']}) · {fonte['confianca']}"
                                )
                        detalhe_col2.write(f"**SLA:** {conformidade}")
                        if intervalo is not None:
                            detalhe_col2.write(f"{intervalo} dia(s) desde o evento anterior")

                st.markdown("#### Tabela no padrão eproc")
                tabela_eventos = df_mov.sort_values("data_movimento", ascending=False).copy()
                tabela_eventos["numero_evento"] = tabela_eventos["numero_evento"].fillna("-")
                tabela_eventos["descricao_exibicao"] = tabela_eventos.apply(
                    lambda row: (
                        (
                            str(row["nome_movimento"])
                            if pd.notna(row["nome_movimento"]) and row["nome_movimento"] != "N/A"
                            else (classificador.classificar_marco(row["codigo_movimento"]) or f"Movimento CNJ {row['codigo_movimento']}")
                        )
                        + (
                            f" - {row['descricao_movimento']}"
                            if pd.notna(row["descricao_movimento"]) and row["descricao_movimento"]
                            and str(row["descricao_movimento"]) not in str(row["nome_movimento"])
                            else ""
                        )
                    ),
                    axis=1,
                )
                tabela_eventos["data_exibicao"] = tabela_eventos["data_movimento"].dt.strftime(
                    "%d/%m/%Y %H:%M:%S"
                ).fillna("Sem data")
                tabela_eventos["usuario_exibicao"] = tabela_eventos["usuario_evento"].fillna(
                    "Não informado pelo DataJud"
                )
                tabela_eventos["documentos_exibicao"] = tabela_eventos["documentos_evento"].fillna(
                    "Não informado pelo DataJud"
                )
                tabela_eventos["parte_exibicao"] = tabela_eventos["parte_evento"].fillna(
                    "Não identificado pela fonte"
                )
                tabela_eventos["advogado_exibicao"] = tabela_eventos["advogado_evento"].fillna(
                    "Não identificado pela fonte"
                )
                tabela_eventos["fonte_exibicao"] = tabela_eventos["fonte_detalhe"].fillna(
                    "Não registrada"
                )
                tabela_eventos["confianca_exibicao"] = tabela_eventos["confianca_evento"].fillna(
                    "Não classificada"
                )
                st.dataframe(
                    tabela_eventos[
                        [
                            "numero_evento",
                            "data_exibicao",
                            "descricao_exibicao",
                            "usuario_exibicao",
                            "documentos_exibicao",
                            "parte_exibicao",
                            "advogado_exibicao",
                            "fonte_exibicao",
                            "confianca_exibicao",
                        ]
                    ].rename(
                        columns={
                            "numero_evento": "Evento",
                            "data_exibicao": "Data/Hora",
                            "descricao_exibicao": "Descrição",
                            "usuario_exibicao": "Usuário",
                            "documentos_exibicao": "Documentos",
                            "parte_exibicao": "Parte do evento",
                            "advogado_exibicao": "Advogado do evento",
                            "fonte_exibicao": "Fonte",
                            "confianca_exibicao": "Confiança",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                    height=620,
                )
            else:
                st.warning("Nenhum movimento registrado para este NPU.")
        else:
            st.info("Nenhum processo encontrado para o filtro selecionado.")
    else:
        st.info("O banco de dados está vazio. Execute o monitoramento na barra lateral.")


# ==========================
# ABA - CENTRO DE COMANDO C3 (TORRE DE CONTROLE & DRILL-DOWN)
# ==========================
with tab_c3:
    # 1. INJETANDO O ESTILO MODERNO (Tipo Tailwind) DIRETO NO STREAMLIT
    st.markdown("""
        <style>
        .kpi-card {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-left: 5px solid #0ea5e9; /* Azul Cresol/Executivo */
            margin-bottom: 20px;
        }
        .kpi-title {
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        .kpi-value {
            color: #0f172a;
            font-size: 32px;
            font-weight: bold;
        }
        .kpi-sub {
            color: #10b981; /* Verde positivo */
            font-size: 13px;
            font-weight: 500;
            margin-top: 8px;
            display: flex;
            align-items: center;
        }
        .kpi-sub.negative {
            color: #ef4444; /* Vermelho alerta */
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. CABEÇALHO DA ABA
    st.markdown("### 🎛️ Centro de Comando e Controle (C3) - Torre de Controle 360º")
    st.caption("Visão Macro da carteira com capacidade de Drill-down analítico para o Micro (Prontuário Individual).")
    st.divider()

    # 3. CARREGANDO OS DADOS DO SEU SISTEMA
    carteira_c3, _ = carregar_inteligencia_carteira()

    if carteira_c3.empty:
        st.warning("Nenhum processo carregado na base de dados para análise do C3.")
    else:
        st.markdown("#### 📊 Visão Macro: Torre de Controle da Carteira")
        
        # Calculando as métricas baseadas nos seus dados reais
        total_execucoes = len(carteira_c3)
        saude_geral = f"{carteira_c3['saude'].mean():.1f}" if "saude" in carteira_c3.columns else "0.0"
        criticos_count = len(carteira_c3[carteira_c3["saude"] < 50]) if "saude" in carteira_c3.columns else 0
        cobertura_media = f"{carteira_c3['cobertura_dados'].mean():.1f}" if "cobertura_dados" in carteira_c3.columns else "0.0"

        # 4. DESENHANDO OS CARDS MODERNOS COM COLUNAS DO STREAMLIT
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Processos na Torre</div>
                    <div class="kpi-value">{total_execucoes}</div>
                    <div class="kpi-sub">↑ Carteira Ativa e Monitorada</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #10b981;">
                    <div class="kpi-title">Saúde Média da Carteira</div>
                    <div class="kpi-value">{saude_geral}%</div>
                    <div class="kpi-sub">Padrão de Execução Vigente</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #ef4444;">
                    <div class="kpi-title">Casos Críticos (🔴)</div>
                    <div class="kpi-value" style="color: #ef4444;">{criticos_count}</div>
                    <div class="kpi-sub negative">⚠️ Requer Atenção Imediata</div>
                </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #8b5cf6;">
                    <div class="kpi-title">Cobertura de Dados</div>
                    <div class="kpi-value">{cobertura_media}%</div>
                    <div class="kpi-sub">Enriquecimento IA</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("") # Adiciona um respiro na tela

        # 5. BLOCO DE DRILL-DOWN (Onde entram os dados em tabela)
        st.markdown("#### 🔍 Visão Micro: Prontuário Analítico & Drill-down por Processo")
        st.caption("Selecione um NPU abaixo para abrir o raio-x analítico, timeline inteligente e leitura semântica da IA.")

        # Aqui mantemos a lógica nativa do Streamlit para tabelas e filtros, que funciona muito bem
        lista_npus = carteira_c3["npu"].dropna().unique().tolist() if "npu" in carteira_c3.columns else []
        
        if lista_npus:
            npu_selecionado = st.selectbox("Escolha o NPU para Drill-down do Processo:", lista_npus, key="select_drilldown_c3")
            
            # Mostra a tabela de forma expansiva e limpa
            st.dataframe(
                carteira_c3,
                use_container_width=True,
                hide_index=True
            )

# ==========================
# ABA 4 - INDICADORES E BENCHMARKS
# ==========================
with tab_benchmarks:
    st.markdown("### 🎯 Benchmarks operacionais da carteira")
    carteira, _ = carregar_inteligencia_carteira()
    mediana_inatividade = carteira["dias_sem_movimento"].median() if not carteira.empty else 0
    mediana_cobertura = carteira["cobertura_dados"].median() if not carteira.empty else 0
    mediana_saude = carteira["saude"].median() if not carteira.empty else 0
    colA, colB, colC = st.columns(3)
    colA.metric("Mediana sem movimentação", f"{mediana_inatividade:.0f} dias", "menor é melhor", delta_color="inverse")
    colB.metric("Mediana de cobertura", f"{mediana_cobertura:.1f}%", "eventos descritos")
    colC.metric("Mediana de saúde", f"{mediana_saude:.1f}/100", "score operacional")

    st.divider()

    graf1, graf2 = st.columns(2)
    with graf1:
        assessorias = carteira.groupby(carteira["assessoria"].fillna("Não definida"), as_index=False).agg(
            saude=("saude", "mean"), cobertura=("cobertura_dados", "mean")
        )
        fig_ticket = px.bar(
            assessorias,
            x="assessoria",
            y="saude",
            title="Saúde média por assessoria",
            text_auto=True,
            color="assessoria",
        )
        fig_ticket.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
        )
        st.plotly_chart(fig_ticket, use_container_width=True)

    with graf2:
        with database.conectar() as conn:
            movimentos_top = pd.read_sql_query(
                """
                SELECT COALESCE(NULLIF(descricao_movimento, ''), nome_movimento) AS movimento, COUNT(*) AS total
                FROM movimentos
                GROUP BY COALESCE(NULLIF(descricao_movimento, ''), nome_movimento)
                ORDER BY total DESC
                LIMIT 8
                """,
                conn,
            )
        fig_marcos = px.bar(
            movimentos_top,
            x="total",
            y="movimento",
            orientation="h",
            title="Movimentos Mais Frequentes",
            color="total",
            color_continuous_scale="Viridis",
        )
        fig_marcos.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
        )
        st.plotly_chart(fig_marcos, use_container_width=True)


# ==========================
# ABA 5 - MERITOCRACIA & REGRAS
# ==========================
with tab_meritocracia:
    st.markdown("### ⚖️ Configuração de Pesos da Meritocracia")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Pesos Globais do Score (Base 100)**")
        eficiencia = st.number_input("Eficiência Financeira (%)", value=35, max_value=100)
        agilidade = st.number_input("Agilidade Constritiva (%)", value=25, max_value=100)
        prazos = st.number_input("SLA e Prazos Processuais (%)", value=20, max_value=100)
        acordos = st.number_input("Taxa de Acordo / Conciliação (%)", value=20, max_value=100)
        st.info(f"**Total Ponderado:** {eficiencia + agilidade + prazos + acordos}%")

    with c2:
        st.markdown("**Modificadores (Gatilhos)**")
        st.success(
            "**Bônus de Alta Performance (+5%)**\nAplicado quando a assessoria realiza bloqueio efetivo acima do esperado em até 15 dias."
        )
        st.checkbox("Ativar regra de Bônus", value=True)

        st.error(
            "**Penalidade Gravíssima (-10%)**\nDeduz na nota final para cada evento de perda de prazo identificado."
        )
        st.checkbox("Ativar regra de Penalidade", value=True)

    st.button("💾 Salvar Parâmetros", type="primary")


# ==========================
# ABA 6 - RANKING DE ASSESSORIAS
# ==========================
with tab_ranking:
    st.markdown("### 🏆 Ranking de performance")
    st.caption("Score baseado em saúde, cobertura de dados e proporção de processos controlados.")
    ranking = carregar_ranking_real()
    if ranking.empty:
        st.info("Ainda não há processos suficientes para formar o ranking.")
    else:
        ranking["Posição"] = range(1, len(ranking) + 1)
        ranking = ranking[["Posição", "Assessoria", "Score", "processos", "saude_media", "cobertura_media", "processos_controlados"]].rename(
            columns={"processos": "Processos", "saude_media": "Saúde média", "cobertura_media": "Cobertura média", "processos_controlados": "Controlados"}
        )
        st.dataframe(ranking, use_container_width=True, hide_index=True)


# ==========================
# CADASTROS E IMPORTAÇÃO
# ==========================
with st.sidebar:
    st.divider()
    abrir_cadastros = st.button("🧩 Cadastros", use_container_width=True, key="btn_cadastros_sidebar_principal")
    if abrir_cadastros:
        st.session_state["cadastros_abertos"] = True

if st.session_state.get("cadastros_abertos", False):
    st.markdown("## Cadastros e carteira")
    st.caption("Área operacional aberta pelo botão Cadastros no menu lateral.")
    clientes_tab, prestadores_tab, processos_tab, import_tab = st.tabs(
        ["Clientes", "Prestadores", "Processos", "Importar Excel"]
    )

    with clientes_tab:
        st.subheader("Cadastrar cliente")
        with st.form("cliente"):
            nome = st.text_input("Nome ou razão social")
            documento = st.text_input("CPF/CNPJ")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            if st.form_submit_button("Cadastrar cliente"):
                try:
                    with database.conectar() as conn:
                        conn.execute(
                            "INSERT INTO clientes (nome_razasocial, cpf_cnpj, email, telefone) VALUES (?, ?, ?, ?)",
                            (nome.strip(), documento.strip(), email.strip(), telefone.strip()),
                        )
                    st.success("Cliente cadastrado.")
                except Exception as error:
                    st.error(f"Não foi possível cadastrar: {error}")

    with prestadores_tab:
        st.subheader("Cadastrar prestador de serviço")
        with st.form("prestador"):
            nome = st.text_input("Nome", key="prestador_nome")
            documento = st.text_input("CPF/OAB", key="prestador_documento")
            tipo = st.text_input("Tipo de serviço", placeholder="Advogado, correspondente, analista...")
            telefone = st.text_input("Telefone", key="prestador_telefone")
            if st.form_submit_button("Cadastrar prestador"):
                try:
                    with database.conectar() as conn:
                        conn.execute(
                            "INSERT INTO prestadores (nome, cpf_oab, tipo_servico, telefone) VALUES (?, ?, ?, ?)",
                            (nome.strip(), documento.strip(), tipo.strip(), telefone.strip()),
                        )
                    st.success("Prestador cadastrado.")
                except Exception as error:
                    st.error(f"Não foi possível cadastrar: {error}")

    with processos_tab:
        st.subheader("Carteira de processos")
        with database.conectar() as conn:
            processos = pd.read_sql_query(
                """SELECT p.npu, p.nome_autor AS autor, p.nome_reu AS reu,
                p.papel_cliente, p.relacao_carteira, p.assessoria, p.status_monitoramento
                FROM processos p ORDER BY p.npu""", conn
            )
        st.dataframe(processos, use_container_width=True, hide_index=True)

    with import_tab:
        st.subheader("Importar carteira do eproc")
        st.write("Aceita o Excel exportado com Nº Processo, Autor, Réu, Último Evento, Situação e ASSESSORIA.")
        arquivo = st.file_uploader("Selecione um arquivo Excel", type=["xlsx", "xls"])
        if arquivo and st.button("Importar e vincular carteira"):
            try:
                resultado = importar_processos_excel(arquivo)
                st.success(f"{resultado['inseridos']} inserido(s) e {resultado.get('atualizados', 0)} atualizado(s).")
                if resultado["erros"]:
                    st.warning("Linhas pendentes de vínculo:")
                    st.write("\n".join(resultado["erros"]))
            except Exception as error:
                st.error(f"Falha na importação: {error}")
