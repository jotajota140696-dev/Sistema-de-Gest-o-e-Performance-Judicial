'use client';

import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  TrendingUp, 
  AlertTriangle, 
  Search, 
  Filter, 
  DollarSign, 
  Users, 
  Scale, 
  ArrowUpRight, 
  ShieldCheck,
  ChevronRight,
  Download
} from 'lucide-react';

// Dados simulados de exemplo para a visao analitica (caso a caso)
const mockCasos = [
  { id: 1, contrato: "CC-98234", devedor: "Agropecuária Santa Rita Ltda", valor: "R$ 145.800,00", status: "Em Andamento", fase: "Judicial - Execução", assessor: "Equipe Alfa", diasAtraso: 340 },
  { id: 2, contrato: "CC-87122", devedor: "João Carlos de Souza", valor: "R$ 38.450,00", status: "Acordo Firmado", fase: "Homologação de Acordo", assessor: "Equipe Beta", diasAtraso: 180 },
  { id: 3, contrato: "CC-76541", devedor: "Cooperativa de Transporte 3 Irmãos", valor: "R$ 210.900,00", status: "Crítico", fase: "Localização de Bens", assessor: "Equipe Alfa", diasAtraso: 510 },
  { id: 4, contrato: "CC-65432", devedor: "Mariana da Silva Me", valor: "R$ 24.100,00", status: "Em Andamento", fase: "Cobrança Extrajudicial", assessor: "Equipe Gama", diasAtraso: 95 },
  { id: 5, contrato: "CC-54321", devedor: "Comércio de Alimentos Chapecó", valor: "R$ 89.300,00", status: "Liquidado", fase: "Baixa Definitiva", assessor: "Equipe Beta", diasAtraso: 210 },
];

export default function DashboardPage() {
  const [abaAtiva, setAbaAtiva] = useState<'gerencial' | 'analitico'>('gerencial');
  const [busca, setBusca] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('Todos');

  const casosFiltrados = mockCasos.filter(caso => {
    const matchBusca = caso.devedor.toLowerCase().includes(busca.toLowerCase()) || 
                       caso.contrato.toLowerCase().includes(busca.toLowerCase());
    const matchStatus = filtroStatus === 'Todos' || caso.status === filtroStatus;
    return matchBusca && matchStatus;
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}>
      
      {/* Top Bar / Header */}
      <header style={{ borderBottom: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#2563eb', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Scale size={24} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>LegalTech Recovery SaaS</h1>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Gestão Estratégica de Recuperação de Crédito e Contencioso</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <span style={{ fontSize: '12px', backgroundColor: '#1e293b', padding: '6px 12px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '6px', border: '1px solid #334155' }}>
            <ShieldCheck size={14} color="#22c55e" /> Ambiente Seguro de Produção
          </span>
        </div>
      </header>

      {/* Navegação por Abas */}
      <div style={{ backgroundColor: '#0f172a', padding: '0 32px', borderBottom: '1px solid #1e293b', display: 'flex', gap: '24px' }}>
        <button
          onClick={() => setAbaAtiva('gerencial')}
          style={{
            background: 'none',
            border: 'none',
            color: abaAtiva === 'gerencial' ? '#60a5fa' : '#94a3b8',
            padding: '14px 4px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: abaAtiva === 'gerencial' ? '2px solid #60a5fa' : '2px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <LayoutDashboard size={16} /> Visão Gerencial (Executiva)
        </button>

        <button
          onClick={() => setAbaAtiva('analitico')}
          style={{
            background: 'none',
            border: 'none',
            color: abaAtiva === 'analitico' ? '#60a5fa' : '#94a3b8',
            padding: '14px 4px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: abaAtiva === 'analitico' ? '2px solid #60a5fa' : '2px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <FileText size={16} /> Painel Analítico (Caso a Caso)
        </button>
      </div>

      {/* Conteúdo Principal */}
      <main style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>

        {/* ABA 1: VISÃO GERENCIAL */}
        {abaAtiva === 'gerencial' && (
          <div>
            {/* Cards de Métricas Principais */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Recuperação Total (Mês)</span>
                  <DollarSign size={20} color="#3b82f6" />
                </div>
                <div style={{ fontSize: '26px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>R$ 1.482.900</div>
                <span style={{ fontSize: '12px', color: '#22c55e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ArrowUpRight size={14} /> +12.4% vs mês anterior
                </span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Taxa Média de Conversão</span>
                  <TrendingUp size={20} color="#22c55e" />
                </div>
                <div style={{ fontSize: '26px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>34.8%</div>
                <span style={{ fontSize: '12px', color: '#22c55e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ArrowUpRight size={14} /> Meta batida (30%)
                </span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Casos Ativos em Carteira</span>
                  <Users size={20} color="#a855f7" />
                </div>
                <div style={{ fontSize: '26px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>1.240</div>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>Distribuídos em 4 equipes</span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Gargalos Críticos</span>
                  <AlertTriangle size={20} color="#ef4444" />
                </div>
                <div style={{ fontSize: '26px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>42</div>
                <span style={{ fontSize: '12px', color: '#ef4444' }}>Requer atenção jurídica</span>
              </div>
            </div>

            {/* Seção Secundária: Ranking e Alertas */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
              
              {/* Ranking de Assessorias / Equipes */}
              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', marginTop: 0 }}>Desempenho por Equipe / Assessorias</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#1f2937', borderRadius: '8px' }}>
                    <span>Escritório Alpha</span>
                    <span style={{ fontWeight: 'bold', color: '#60a5fa' }}>R$ 620.000,00 (68% eficiência)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#1f2937', borderRadius: '8px' }}>
                    <span>Advocacia Beta</span>
                    <span style={{ fontWeight: 'bold', color: '#60a5fa' }}>R$ 410.000,00 (54% eficiência)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#1f2937', borderRadius: '8px' }}>
                    <span>Consultoria Gama</span>
                    <span style={{ fontWeight: 'bold', color: '#60a5fa' }}>R$ 452.900,00 (61% eficiência)</span>
                  </div>
                </div>
              </div>

              {/* Alertas e Prazos Processuais */}
              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', marginTop: 0 }}>Próximos Prazos / Alertas</h3>
                <div style={{ fontSize: '13px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ borderLeft: '3px solid #f59e0b', paddingLeft: '10px' }}>
                    <p style={{ margin: 0, fontWeight: '600', color: '#f1f5f9' }}>Impugnação de Execução</p>
                    <span style={{ fontSize: '11px' }}>Vencimento em 2 dias úteis (Contrato CC-98234)</span>
                  </div>
                  <div style={{ borderLeft: '3px solid #22c55e', paddingLeft: '10px' }}>
                    <p style={{ margin: 0, fontWeight: '600', color: '#f1f5f9' }}>Homologação de Acordo</p>
                    <span style={{ fontSize: '11px' }}>Audiência marcada para amanhã</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ABA 2: PAINEL ANALÍTICO (CASO A CASO) */}
        {abaAtiva === 'analitico' && (
          <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
              
              {/* Barra de Busca */}
              <div style={{ position: 'relative', flex: '1', minWidth: '280px' }}>
                <Search size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Buscar por devedor ou número de contrato..."
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    padding: '10px 12px 10px 40px',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Filtros */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#1f2937', padding: '8px 12px', borderRadius: '8px', border: '1px solid #374151' }}>
                  <Filter size={16} color="#94a3b8" />
                  <span style={{ fontSize: '13px', color: '#94a3b8' }}>Status:</span>
                  <select
                    value={filtroStatus}
                    onChange={(e) => setFiltroStatus(e.target.value)}
                    style={{ background: 'transparent', border: 'none', color: '#f1f5f9', fontSize: '13px', outline: 'none', cursor: 'pointer' }}
                  >
                    <option value="Todos" style={{ backgroundColor: '#1f2937' }}>Todos</option>
                    <option value="Em Andamento" style={{ backgroundColor: '#1f2937' }}>Em Andamento</option>
                    <option value="Acordo Firmado" style={{ backgroundColor: '#1f2937' }}>Acordo Firmado</option>
                    <option value="Crítico" style={{ backgroundColor: '#1f2937' }}>Crítico</option>
                    <option value="Liquidado" style={{ backgroundColor: '#1f2937' }}>Liquidado</option>
                  </select>
                </div>

                <button style={{ backgroundColor: '#2563eb', color: '#ffffff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Download size={16} /> Exportar Relatório
                </button>
              </div>

            </div>

            {/* Tabela de Casos */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #374151', color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px' }}>Contrato</th>
                    <th style={{ padding: '12px' }}>Devedor / Mutuário</th>
                    <th style={{ padding: '12px' }}>Valor em Aberto</th>
                    <th style={{ padding: '12px' }}>Fase Processual</th>
                    <th style={{ padding: '12px' }}>Status</th>
                    <th style={{ padding: '12px' }}>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {casosFiltrados.length > 0 ? (
                    casosFiltrados.map((caso) => (
                      <tr key={caso.id} style={{ borderBottom: '1px solid #1f2937', transition: 'background 0.2s' }}>
                        <td style={{ padding: '14px 12px', fontWeight: '500', color: '#60a5fa' }}>{caso.contrato}</td>
                        <td style={{ padding: '14px 12px' }}>{caso.devedor}</td>
                        <td style={{ padding: '14px 12px', fontWeight: '600' }}>{caso.valor}</td>
                        <td style={{ padding: '14px 12px', color: '#94a3b8' }}>{caso.fase}</td>
                        <td style={{ padding: '14px 12px' }}>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: '500',
                            backgroundColor: caso.status === 'Liquidado' ? 'rgba(34, 197, 94, 0.1)' :
                                           caso.status === 'Crítico' ? 'rgba(239, 68, 68, 0.1)' :
                                           caso.status === 'Acordo Firmado' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: caso.status === 'Liquidado' ? '#22c55e' :
                                   caso.status === 'Crítico' ? '#ef4444' :
                                   caso.status === 'Acordo Firmado' ? '#60a5fa' : '#f59e0b'
                          }}>
                            {caso.status}
                          </span>
                        </td>
                        <td style={{ padding: '14px 12px' }}>
                          <button style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: '500' }}>
                            Detalhes <ChevronRight size={14} />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                        Nenhum caso encontrado com os filtros atuais.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

          </div>
        )}

      </main>

    </div>
  );
}
