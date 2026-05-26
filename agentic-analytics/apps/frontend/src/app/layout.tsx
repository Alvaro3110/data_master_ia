import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentic Analytics — Pricing, Margem & Risco",
  description:
    "Plataforma analítica conversacional governada para análise de pricing, margem, safra, risco de crédito e ROAE. Powered by LangGraph + RAG + Text-to-SQL.",
  keywords: ["pricing", "analytics", "risco", "margem", "ROAE", "safra", "IA"],
  authors: [{ name: "Agentic Analytics" }],
  robots: "noindex",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {/* Orbs decorativos */}
        <div className="orb orb-purple" aria-hidden="true" />
        <div className="orb orb-blue" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
