import sqlite3
from services.classificador import analisar_processo_com_ia
import time

def executar_forca_tarefa_ia():
    print("=== [COMANDO] INICIANDO REANÁLISE FORÇADA DA IA ===")
    conn = sqlite3.connect("banco_simj.db")
    cursor = conn.cursor()
    
    # Busca todos os processos na base
    cursor.execute("SELECT npu FROM processos")
    processos = [row[0] for row in cursor.fetchall()]
    
    if not processos:
        print("Nenhum processo encontrado na base de dados.")
        conn.close()
        return

    for proc_num in processos:
        print(f"\nProcesso {proc_num}: Carregando histórico e reanalisando...")
        
        # 1. Carrega o histórico de movimentos
        cursor.execute("SELECT data_movimento, nome_movimento FROM movimentos WHERE npu = ? ORDER BY data_movimento ASC", (proc_num,))
        movimentos = [{"dataHora": r[0], "nome": r[1]} for r in cursor.fetchall()]

        # Carrega as decisões (com proteção caso a tabela não exista)
        try:
            cursor.execute("SELECT dataPublicacao, teor FROM decisoes_dje WHERE npu = ? ORDER BY dataPublicacao ASC", (proc_num,))
            decisoes = [{"dataPublicacao": r[0], "teor": r[1]} for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            decisoes = []
        
        # 2. Chama a sua IA atualizada
        resultado_ia = analisar_processo_com_ia(proc_num, movimentos, decisoes)
        
        # 3. Atualiza o banco de dados
        cursor.execute("""
            UPDATE processos 
            SET marco_atual = ?, gargalo = ?, resumo = ?
            WHERE npu = ?
        """, (
            resultado_ia.get("marco", 1), 
            resultado_ia.get("gargalo", ""), 
            resultado_ia.get("resumo", ""), 
            proc_num
        ))
        conn.commit()
        print(f" -> Sucesso! Novo Marco atribuído: {resultado_ia.get('marco')} | Gargalo: {resultado_ia.get('gargalo')}")
        
    conn.close()
    print("\n=== [COMANDO] REANÁLISE DA IA CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    executar_forca_tarefa_ia()