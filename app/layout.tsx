import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Global Market Morning Brief",
  description: "Admin panel for daily market newsletter"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
