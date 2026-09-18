import os
import json
import re
import time
from pathlib import Path
from services.datajud import consultar_processo_datajud
from services.jusbrasil import consultar_jusbrasil_publico, extrair_descricoes_jusbrasil
from services.djen import consultar_djen
from services.classificador import analisar_marco_e_gargalo
import database
import robo_diario

def limpar_npu(npu):
    return re.sub(r'\D', '', str(npu))

def formatar_npu_cnj(npu):
    digitos = limpar_npu(npu)
    if len(digitos) != 20:
        return str(npu)
    return f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.{digitos[16:]}"

def buscar_todos_npus():
    with database.conectar() as conn:
        linhas = conn.execute("SELECT npu FROM processos").fetchall()
    return [linha[0] for linha in linhas]

def atualizar_status_processo(npu, status):
    with database.conectar() as conn:
        conn.execute(
            "UPDATE processos SET status_monitoramento = ? WHERE npu = ?",
            (status, npu),
        )

def main():
    print("=== INICIANDO ROBÔ JURÍDICO (DATAJUD + COMUNICA PJE) ===")

    database.criar_tabelas()
    lista_npus = buscar_todos_npus()

    if not lista_npus:
        print("\n⚠️ Nenhum processo encontrado no banco.")
        return

    print(f"\n[Orquestrador] Processando {len(lista_npus)} processo(s)...")
    print("-" * 50)

    for i, npu_bruto in enumerate(lista_npus, start=1):
        npu_formatado = formatar_npu_cnj(npu_bruto)
        npu_limpo = limpar_npu(npu_bruto)
        print(f"\n⏳ [{i}/{len(lista_npus)}] Processando NPU: {npu_formatado}")

        sucesso_datajud = False
        sucesso_comunica = False

        # 1. BUSCA DATAJUD
        print("🔍 [1/2] Consultando DataJud...")
        try:
            resultado_datajud = consultar_processo_datajud(npu_formatado)
            if resultado_datajud:
                nome_arquivo_json = f"processo_{npu_limpo}.json"
                if Path(nome_arquivo_json).exists():
                    robo_diario.processar_json_datajud(nome_arquivo_json)
                    sucesso_datajud = True
        except Exception as err:
            print(f"⚠️ Erro ao processar DataJud: {err}")

        # 2. BUSCA E DOWNLOAD DIÁRIO CNJ (COMUNICA PJE)
        print("📰 [2/2] Consultando Comunica PJe e baixando arquivos...")
        try:
            publicacoes = consultar_djen(npu_limpo)
            if publicacoes:
                sucesso_comunica = True
                print(f"   -> {len(publicacoes)} publicação(ões) e arquivo(s) processados.")
                with database.conectar() as conn:
                    for idx, pub in enumerate(publicacoes, start=1):
                        texto_pub = pub.get("conteudo") or ""
                        data_pub = pub.get("data") or ""
                        tribunal = pub.get("tribunal") or "CNJ"
                        arquivo_pdf = pub.get("arquivo_local")

                        database.inserir_movimento(
                            conn,
                            npu_bruto,
                            data_pub,
                            f"Publicação Diário ({tribunal})",
                            "DIARIO_PJE",
                            texto_pub,
                            idx,
                            pub.get("orgao"),
                            arquivo_pdf,
                            "Comunica PJe (Diário)",
                            "Oficial Diário"
                        )

                        if texto_pub:
                            analise_ia = analisar_marco_e_gargalo(texto_pub)
                            if analise_ia:
                                conn.execute(
                                    """
                                    INSERT INTO processo_marcos_historico 
                                    (npu, marco_id, data_atingimento, origem_gargalo, observacao_ia)
                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (
                                        npu_bruto,
                                        analise_ia.get("marco_detectado"),
                                        data_pub,
                                        analise_ia.get("gargalo"),
                                        f"Diário PJe: {analise_ia.get('resumo_traduzido')}"
                                    )
                                )
        except Exception as err:
            print(f"⚠️ Erro ao processar Comunica PJe: {err}")

        # Atualização realista do status no banco
        if sucesso_datajud or sucesso_comunica:
            atualizar_status_processo(npu_bruto, 'ATUALIZADO')
            print(f"✅ Processo {npu_formatado} atualizado com sucesso.")
        else:
            atualizar_status_processo(npu_bruto, 'FALHA_CONEXAO')
            print(f"❌ Processo {npu_formatado} não obteve dados (APIs indisponíveis/Timeout).")

        # Pausa de 2 segundos para evitar bloqueio por IP (Rate Limiting)
        time.sleep(2)

    print("\n" + "=" * 50)
    print("🚀 Execução do lote concluída!")

if __name__ == "__main__":
    main()