"use client";

import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

// Conectando com o seu banco de dados
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

export default function GestaoProcessos() {
  const [processos, setProcessos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [mensagem, setMensagem] = useState("");

  // Função para buscar os processos já cadastrados no banco
  const carregarProcessos = async () => {
    const { data, error } = await supabase
      .from("processos")
      .select("*")
      .order("created_at", { ascending: false });

    if (data) setProcessos(data);
  };

  useEffect(() => {
    carregarProcessos();
  }, []);

  // Função para processar o arquivo CSV
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setMensagem("Lendo arquivo e salvando no banco de dados...");

    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      
      // Quebra o CSV em linhas (ignorando a primeira linha de cabeçalho)
      const linhas = text.split("\n").slice(1);
      const processosParaSalvar = [];

      for (const linha of linhas) {
        if (!linha.trim()) continue;
        
        // Supondo que as colunas do CSV sejam: NPU, Tribunal, Esfera
        const [npu, tribunal, esfera] = linha.split(",");

        processosParaSalvar.push({
          npu: npu?.trim(),
          tribunal: tribunal?.trim(),
          esfera: esfera?.trim(),
          status_atual: "Ativo"
        });
      }

      // Envia os dados em massa para o Supabase
      const { error } = await supabase
        .from("processos")
        .insert(processosParaSalvar);

      if (error) {
        setMensagem(`Erro ao salvar: ${error.message}`);
      } else {
        setMensagem(`${processosParaSalvar.length} processos importados com sucesso!`);
        carregarProcessos(); // Atualiza a tabela na tela
      }
      setLoading(false);
    };

    reader.readAsText(file);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto bg-gray-50 min-h-screen text-gray-800">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Gestão de Processos e Upload</h1>
        <p className="text-slate-600 mt-2">Faça o upload de bases (CSV) para que o robô inicie o monitoramento diário.</p>
      </header>

      {/* Área de Upload */}
      <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <h2 className="text-xl font-semibold mb-4">Importar Base (Arquivo .csv)</h2>
        <div className="flex items-center gap-4">
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileUpload}
            disabled={loading}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
          />
        </div>
        {mensagem && (
          <div className={`mt-4 p-3 rounded text-sm ${mensagem.includes('Erro') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {mensagem}
          </div>
        )}
      </section>

      {/* Tabela de Processos */}
      <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NPU (Número do Processo)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tribunal</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Esfera</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {processos.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">Nenhum processo cadastrado ainda.</td>
              </tr>
            ) : (
              processos.map((proc, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">{proc.npu}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{proc.tribunal}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{proc.esfera}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      {proc.status_atual}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
