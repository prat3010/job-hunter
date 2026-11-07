import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Hunter Studio — Autonomous Headhunter & Multi-Channel Pitch Engine",
  description: "Executive AI job hunting platform featuring multi-board live scraping, semantic TF-IDF cosine matching, supervised propensity scoring, and BYOK multi-channel pitch synthesis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-slate-100 min-h-screen antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
