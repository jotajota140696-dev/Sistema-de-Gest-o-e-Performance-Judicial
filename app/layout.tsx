export const metadata = {
  title: 'LegalTech Recovery SaaS',
  description: 'Painel de Controle e Gestão de Recuperação de Crédito',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, fontFamily: 'sans-serif', backgroundColor: '#0f172a', color: '#f8fafc' }}>
        {children}
      </body>
    </html>
  )
}
