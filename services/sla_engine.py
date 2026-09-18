import pandas as pd
import database

def calcular_mediana_sla(classe_processual, tribunal, marco_id):
    """Calcula o SLA dinâmico baseado na mediana da carteira e mercado."""
    with database.conectar() as conn:
        query = """
            SELECT pmh.tempo_permanencia_dias 
            FROM processo_marcos_historico pmh
            JOIN processos p ON p.npu = pmh.npu
            WHERE p.classe_judicial = ? 
              AND p.tribunal = ? 
              AND pmh.marco_id = ?
        """
        df = pd.read_sql(query, conn, params=(classe_processual, tribunal, marco_id))
    
    if df.empty or 'tempo_permanencia_dias' not in df.columns:
        return 10  # Fallback padrão seguro de dias
        
    return int(df['tempo_permanencia_dias'].median())