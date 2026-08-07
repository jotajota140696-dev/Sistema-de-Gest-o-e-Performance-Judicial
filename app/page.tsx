'use client';
import { useState } from 'react';
import { Scale, Award, TrendingUp, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function Dashboard() {
  // Dados simulados do ranking
  const assessorias = [
    { nome: 'Escritório Alpha', score: 9.8, tempoMedio: '120 dias' },
    { nome: 'Advocacia Beta', score: 8.5, tempoMedio: '150 dias' },
    { nome: 'Consultoria Gamma', score: 7.2, tempoMedio: '210 dias' },
  ].sort((a, b) => b.score - a.score);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-emerald-400 flex items-center gap-3">
          <Scale className="w-8 h-8" /> LegalTech Recovery SaaS
        </h1>
        <p className="text-slate-400 mt-2">Painel de Performance e Compliance CNJ</p>
      </header>

      {/* Grid de Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-sm">Meta Benchmarking CNJ</div>
            <div className="text-3xl font-bold text-white mt-1">450 Dias</div>
          </div>
          <TrendingUp className="text-emerald-500 w-10 h-10" />
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center justify-between">
           <div>
            <div className="text-slate-400 text-sm">Status do Robô (Varredura)</div>
            <div className="text-3xl font-bold text-emerald-400 mt-1">Ativo</div>
           </div>
           <ShieldCheck className="text-emerald-500 w-10 h-10" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Ranking de Assessorias */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <Award className="text-amber-400" /> Ranking de Assessorias
          </h2>
          <table className="w-full text-left">
            <thead>
              <tr className="text-slate-400 text-xs uppercase border-b border-slate-800">
                <th className="pb-3">Assessoria</th>
                <th className="pb-3 text-center">Score IA</th>
                <th className="pb-3 text-right">Tempo Médio</th>
              </tr>
            </thead>
            <tbody>
              {assessorias.map((firm, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  <td className="py-4 font-medium">{firm.nome}</td>
                  <td className="py-4 text-center text-emerald-400 font-bold">{firm.score}</td>
                  <td className="py-4 text-right text-slate-400">{firm.tempoMedio}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Gargalos */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <AlertTriangle className="text-red-400" /> Gargalos Detectados
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-red-950/20 border border-red-900/50 rounded-xl">
              <p className="text-sm text-red-200">Atraso sistêmico identificado em 14 processos da base de Santa Catarina.</p>
            </div>
            <div className="p-4 bg-emerald-950/20 border border-emerald-900/50 rounded-xl flex items-center gap-3">
              <CheckCircle2 className="text-emerald-400 w-5 h-5" />
              <p className="text-sm text-emerald-200">Todas as petições da semana foram protocoladas.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
