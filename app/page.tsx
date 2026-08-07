'use client';
import { useState, useEffect } from 'react';
import { ShieldCheck, Scale, FileText, AlertTriangle, TrendingUp, Search, Database } from 'lucide-react';

export default function Dashboard() {
  const [processosCount, setProcessosCount] = useState(0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      {/* Cabeçalho do SaaS */}
      <header className="flex justify-between items-center border-b border-slate-800 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-emerald-400">
            <Scale className="w-8 h-8" /> LegalTech Recovery SaaS
          </h1>
          <p className="text-slate-400 text-sm mt-1">Inteligência Jurídica, Recuperação de Crédito & Cruzamento Analítico</p>
        </div>
        <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <span className="text-xs font-medium text-emerald-300">LGPD & Segurança Ativas</span>
        </div>
      </header>

      {/* Grade de Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <span className="text-slate-400 text-sm font-medium">Processos Monitorados</span>
            <Database className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-white">Ativo no Cofre</div>
          <span className="text-xs text-emerald-400 mt-2 inline-block">Sincronizado com Supabase</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <span className="text-slate-400 text-sm font-medium">Foco Principal</span>
            <TrendingUp className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-white">Cobrança & Execução</div>
          <span className="text-xs text-blue-400 mt-2 inline-block">Busca e Apreensão Ativa</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <span className="text-slate-400 text-sm font-medium">Cruzamento (Match)</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-white">Cobrança x Revisão</div>
          <span className="text-xs text-amber-400 mt-2 inline-block">Monitoramento de Conexão</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <span className="text-slate-400 text-sm font-medium">Status do Robô</span>
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-emerald-400">Operacional</div>
          <span className="text-xs text-slate-400 mt-2 inline-block">Varredura Diária Automática</span>
        </div>
      </div>

      {/* Seção Analítica de Casos */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" /> Visão Analítica Individual e Métricas de Condução
          </h2>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input 
              type="text" 
              placeholder="Buscar por número ou devedor..." 
              className="bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-72"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-3 px-4">Número do Processo</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">Devedor / Parte</th>
                <th className="py-3 px-4">Fase Atual</th>
                <th className="py-3 px-4">Tempo Médio</th>
                <th className="py-3 px-4">Cruzamento / Alerta</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors">
                <td className="py-4 px-4 font-mono text-emerald-400">0000000-00.2026.8.24.0000</td>
                <td className="py-4 px-4"><span className="bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-lg text-xs font-semibold">Execução</span></td>
                <td className="py-4 px-4 text-slate-200">Exemplo de Devedor Ltda</td>
                <td className="py-4 px-4 text-slate-300">Citação e Penhora</td>
                <td className="py-4 px-4 text-slate-400">45 dias</td>
                <td className="py-4 px-4"><span className="text-slate-500 text-xs">Nenhum vínculo revisionista</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
