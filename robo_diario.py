# robo_diario.py
import json
import sqlite3
from datetime import datetime
from services import classificador
from services.fontes_processuais import normalizar_movimento
import database


def extrair_descricao_movimento(movimento):
    """Preserva a descrição textual do evento e seus complementos do DataJud."""
    descricao = movimento.get("descricao") or movimento.get("descricaoMovimento")
    if descricao:
        return str(descricao)

    complementos = movimento.get("complementosTabelados") or []
    partes = []
    for complemento in complementos:
        nome = complemento.get("nome")
        tipo = complemento.get("descricao")
        valor = complemento.get("valor")
        texto = nome or valor
        if texto:
            partes.append(f"{tipo}: {texto}" if tipo else str(texto))
    return "; ".join(partes) or None


def extrair_campo_evento(movimento, *nomes):
    """Aceita nomes usados por exportações do eproc e pelo DataJud."""
    for nome in nomes:
        valor = movimento.get(nome)
        if valor not in (None, "", []):
            return valor
    return None


def processar_json_datajud(caminho_arquivo):
    """Lê o arquivo JSON gerado pelo DataJud e insere os dados no banco."""
    
    print(f"\n--- Iniciando processamento do arquivo: {caminho_arquivo} ---")
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return

    npu = dados.get('numeroProcesso')
    classe_judicial = dados.get('classe', {}).get('nome', 'N/A')
    
    # Exemplo estático para testar o Benchmark. Numa situação real, viria de uma planilha sua.
    assessoria_responsavel = "Assessoria Alpha" 
    
    conn = database.conectar()
    cursor = conn.cursor()

    # 1. Inserir ou atualizar o processo
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO processos (npu, tribunal, classe_judicial, assessoria, data_ultima_atualizacao)
        VALUES (?, 'TJSC', ?, ?, ?)
        ON CONFLICT(npu) DO UPDATE SET 
            data_ultima_atualizacao=excluded.data_ultima_atualizacao
    ''', (npu, classe_judicial, assessoria_responsavel, hoje))
    
    # 2. Inserir os movimentos
    movimentos = dados.get('movimentos', [])
    linhas_para_resumo = [] # Usado para o resumo de frequencia do classificador
    
    print(f"Encontrados {len(movimentos)} movimentos para o NPU {npu}.")

    # O DataJud nao traz o numero do evento do eproc. No processo TJSC,
    # a numeracao corresponde a ordem cronologica dos andamentos.
    ordem_cronologica = sorted(
        range(len(movimentos)),
        key=lambda indice: movimentos[indice].get("dataHora") or "",
    )
    numero_evento_por_indice = {
        indice: numero for numero, indice in enumerate(ordem_cronologica, start=1)
    }
    
    for indice, mov in enumerate(movimentos):
        mov = normalizar_movimento(mov, "DataJud")
        # A estrutura do JSON do DataJud pode variar, ajustamos conforme o padrão retornado
        codigo = mov.get('codigo_movimento')
        nome = mov.get('nome_movimento') or classificador.classificar_marco(codigo) or (
            f"Movimento CNJ {codigo}" if codigo else "Movimento sem código"
        )
        descricao = extrair_descricao_movimento(mov)
        data_mov = mov.get('data_movimento', 'N/A')
        numero_evento = extrair_campo_evento(
            mov, "numeroEvento", "numero_evento", "evento", "sequencia"
        )
        if numero_evento is None:
            numero_evento = numero_evento_por_indice[indice]
        usuario = extrair_campo_evento(
            mov, "usuario", "usuarioNome", "responsavel", "user"
        )
        documentos = extrair_campo_evento(
            mov, "documentos", "documento", "linksDocumentos"
        )
        if isinstance(documentos, (list, dict)):
            documentos = json.dumps(documentos, ensure_ascii=False)
        
        if codigo:
            # Salva no banco de dados
            database.inserir_movimento(
                conn,
                npu,
                data_mov,
                nome,
                codigo,
                descricao,
                numero_evento,
                usuario,
                documentos,
                "DataJud",
                "oficial para código e data",
            )
            
            # Adiciona na lista para o classificador
            linhas_para_resumo.append({"codigo_movimento": codigo, "nome_movimento": nome})

    conn.commit()
    conn.close()
    
    # 3. Usa o seu classificador.py para gerar a lista de frequências e atualizar os MARCOS
    print("\n--- Resumo de Movimentos Distintos (Para atualizar MARCOS) ---")
    frequencias = classificador.resumo_movimentos_distintos(linhas_para_resumo)
    
    for codigo, nome, qtd in frequencias:
        marco = classificador.classificar_marco(codigo)
        if marco is None:
            print(f"⚠️ AINDA SEM MARCO: Código {codigo} - {nome} (Apareceu {qtd} vezes)")
        else:
            print(f"✅ Classificado no Marco {marco}: Código {codigo} - {nome} (Apareceu {qtd} vezes)")
            
    print("--- Processamento Concluído! ---\n")

if __name__ == "__main__":
    # Garante que as tabelas existem antes de rodar
    database.criar_tabelas()
    
    # Coloque o nome EXATO do arquivo JSON que o datajud.py gerou na sua pasta
    # Exemplo: processo_50271539220268240930.json
    NOME_ARQUIVO_JSON = "processo_50271539220268240930.json"
    processar_json_datajud(NOME_ARQUIVO_JSON)