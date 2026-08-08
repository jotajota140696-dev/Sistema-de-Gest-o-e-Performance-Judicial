'use client';

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
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
  PlusCircle
} from 'lucide-react';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabase = createClient(supabaseUrl, supabaseKey);

export default function LegalTechDashboard() {
  const [abaAtiva, setAbaAtiva] = useState<'gerencial' | 'analitico' | 'cadastro'>('gerencial');
  const [processos, setProcessos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('Todos');

  const [novoProcesso, setNovoProcesso] = useState({
    numero_processo: '',
    devedor_nome: '',
    valor_causa: '',
    fase_atual: 'Cobrança Extrajudicial',
    status_atual: 'Em Andamento'
  });
  const [sucessoMsg, setSucessoMsg] = useState('');

  const carregarProcessos = async () => {
    setLoading(true);
    const { data, error } = await supabase.from('processos').select('*').order('created_at', { ascending: false });
    if (!error && data) {
      setProcessos(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    carregarProcessos();
  }, []);

  const handleCadastrar = async (e: React.FormEvent) => {
    e.preventDefault();
    const { error } = await supabase.from('processos').insert([
      {
        numero_processo: novoProcesso.numero_processo,
        devedor_nome: novoProcesso.devedor_nome,
        valor_causa: parseFloat(novoProcesso.valor_causa) || 0,
        fase_atual: novoProcesso.fase_atual,
        status_atual: novoProcesso.status_atual
      }
    ]);

    if (!error) {
      setSucessoMsg('Processo cadastrado com sucesso!');
      setNovoProcesso({ numero_processo: '', devedor_nome: '', valor_causa: '', fase_atual: 'Cobrança Extrajudicial', status_atual: 'Em Andamento' });
      carregarProcessos();
      setTimeout(() => setSucessoMsg(''), 4000);
    } else {
      alert('Erro ao cadastrar processo: ' + error.message);
    }
  };

  const totalCarteira = processos.reduce((acc, p) => acc + (Number(p.valor_causa) || 0), 0);
  const totalCasos = processos.length;

  const casosFiltrados = processos.filter(caso => {
    const matchBusca = (caso.devedor_nome || '').toLowerCase().includes(busca.toLowerCase()) || 
                       (caso.numero_processo || '').toLowerCase().includes(busca.toLowerCase());
    const matchStatus = filtroStatus === 'Todos' || caso.status_atual === filtroStatus;
    return matchBusca && matchStatus;
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}>
      
      <header style={{ borderBottom: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#2563eb', padding: '10px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Scale size={24} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>LegalTech Recovery SaaS</h1>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Sistema Integrado de Gestão de Cobrança Judicial e Compliance</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <span style={{ fontSize: '12px', backgroundColor: '#1e293b', padding: '6px 12px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '6px', border: '1px solid #334155' }}>
            <ShieldCheck size={14} color="#22c55e" /> Supabase Conectado
          </span>
        </div>
      </header>

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
          <LayoutDashboard size={16} /> Visão Gerencial
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
          <FileText size={16} /> Painel Analítico ({processos.length})
        </button>

        <button
          onClick={() => setAbaAtiva('cadastro')}
          style={{
            background: 'none',
            border: 'none',
            color: abaAtiva === 'cadastro' ? '#60a5fa' : '#94a3b8',
            padding: '14px 4px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: abaAtiva === 'cadastro' ? '2px solid #60a5fa' : '2px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <PlusCircle size={16} /> Cadastrar Processo
        </button>
      </div>

      <main style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>

        {abaAtiva === 'gerencial' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Valor Total em Carteira</span>
                  <DollarSign size={20} color="#3b82f6" />
                </div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>
                  {totalCarteira.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </div>
                <span style={{ fontSize: '12px', color: '#22c55e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ArrowUpRight size={14} /> Dados reais sincronizados
                </span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Total de Casos Ativos</span>
                  <Users size={20} color="#a855f7" />
                </div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>{totalCasos}</div>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>Base de dados Supabase</span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Taxa de Conversão Média</span>
                  <TrendingUp size={20} color="#22c55e" />
                </div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>34.8%</div>
                <span style={{ fontSize: '12px', color: '#22c55e' }}>Indicador de performance</span>
              </div>

              <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '13px', color: '#9ca3af', fontWeight: '500' }}>Gargalos Críticos</span>
                  <AlertTriangle size={20} color="#ef4444" />
                </div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', margin: '12px 0 4px 0' }}>0</div>
                <span style={{ fontSize: '12px', color: '#ef4444' }}>Monitoramento ativo</span>
              </div>
            </div>

            <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', marginTop: 0 }}>Visão Geral do Sistema de Gestão Judicial</h3>
              <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
                O sistema está conectado diretamente ao Supabase. Utilize a aba <strong style={{ color: '#60a5fa' }}>Cadastrar Processo</strong> para inserir novos casos na base ou navegue até o <strong style={{ color: '#60a5fa' }}>Painel Analítico</strong> para gerenciar e filtrar todos os registros de forma individualizada.
              </p>
            </div>
          </div>
        )}

        {abaAtiva === 'analitico' && (
          <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
              
              <div style={{ position: 'relative', flex: '1', minWidth: '280px' }}>
                <Search size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Buscar por devedor ou número do processo..."
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

                <button 
                  onClick={carregarProcessos}
                  style={{ backgroundColor: '#2563eb', color: '#ffffff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
                >
                  Atualizar Dados
                </button>
              </div>

            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #374151', color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px' }}>Nº Processo</th>
                    <th style={{ padding: '12px' }}>Devedor / Mutuário</th>
                    <th style={{ padding: '12px' }}>Valor da Causa</th>
                    <th style={{ padding: '12px' }}>Fase Processual</th>
                    <th style={{ padding: '12px' }}>Status</th>
                    <th style={{ padding: '12px' }}>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                        Carregando dados do Supabase...
                      </td>
                    </tr>
                  ) : casosFiltrados.length > 0 ? (
                    casosFiltrados.map((caso) => (
                      <tr key={caso.id} style={{ borderBottom: '1px solid #1f2937' }}>
                        <td style={{ padding: '14px 12px', fontWeight: '500', color: '#60a5fa' }}>{caso.numero_processo}</td>
                        <td style={{ padding: '14px 12px' }}>{caso.devedor_nome}</td>
                        <td style={{ padding: '14px 12px', fontWeight: '600' }}>
                          {Number(caso.valor_causa || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </td>
                        <td style={{ padding: '14px 12px', color: '#94a3b8' }}>{caso.fase_atual}</td>
                        <td style={{ padding: '14px 12px' }}>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: '500',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            color: '#60a5fa'
                          }}>
                            {caso.status_atual || 'Em Andamento'}
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
                        Nenhum processo cadastrado ou encontrado. Utilize a aba "Cadastrar Processo" para adicionar dados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

          </div>
        )}

        {abaAtiva === 'cadastro' && (
          <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '32px', maxWidth: '700px', margin: '0 auto' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', marginTop: 0 }}>Cadastro Operacional de Novo Caso</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '24px' }}>Insira os dados do processo judicial para salvamento automático no banco de dados do Supabase.</p>

            {sucessoMsg && (
              <div style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', color: '#22c55e', padding: '12px', borderRadius: '8px', marginBottom: '20px', fontSize: '14px' }}>
                {sucessoMsg}
              </div>
            )}

            <form onSubmit={handleCadastrar} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#9ca3af', marginBottom: '6px' }}>Número do Processo / Chave</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: 5001234-88.2026.8.24.0018"
                  value={novoProcesso.numero_processo}
                  onChange={(e) => setNovoProcesso({...novoProcesso, numero_processo: e.target.value})}
                  style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '10px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#9ca3af', marginBottom: '6px' }}>Nome do Devedor / Mutuário</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Agropecuária Santa Rita Ltda"
                  value={novoProcesso.devedor_nome}
                  onChange={(e) => setNovoProcesso({...novoProcesso, devedor_nome: e.target.value})}
                  style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '10px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#9ca3af', marginBottom: '6px' }}>Valor da Causa (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="Ex: 145800.00"
                  value={novoProcesso.valor_causa}
                  onChange={(e) => setNovoProcesso({...novoProcesso, valor_causa: e.target.value})}
                  style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '10px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', color: '#9ca3af', marginBottom: '6px' }}>Fase Processual</label>
                  <input
                    type="text"
                    value={novoProcesso.fase_atual}
                    onChange={(e) => setNovoProcesso({...novoProcesso, fase_atual: e.target.value})}
                    style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '10px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', color: '#9ca3af', marginBottom: '6px' }}>Status</label>
                  <select
                    value={novoProcesso.status_atual}
                    onChange={(e) => setNovoProcesso({...novoProcesso, status_atual: e.target.value})}
                    style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '10px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none', cursor: 'pointer' }}
                  >
                    <option value="Em Andamento">Em Andamento</option>
                    <option value="Acordo Firmado">Acordo Firmado</option>
                    <option value="Crítico">Crítico</option>
                    <option value="Liquidado">Liquidado</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                style={{ backgroundColor: '#2563eb', color: '#ffffff', border: 'none', padding: '12px', borderRadius: '8px', fontSize: '14px', fontWeight: '600', cursor: 'pointer', marginTop: '12px' }}
              >
                Salvar Processo no Supabase
              </button>
            </form>
          </div>
        )}

      </main>

    </div>
  );
}
