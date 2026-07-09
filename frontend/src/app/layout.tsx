import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "ModelGuard AI — Audit Your Financial Models",
  description: "ModelGuard catches formula errors, hidden risks, and suspicious patterns in your Excel models. Like Grammarly for financial models.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} antialiased bg-[#09090b] text-[#fafafa] min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
