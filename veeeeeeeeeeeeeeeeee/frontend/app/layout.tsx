import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ResQAI | Emergency Response Command Center",
  description: "AI-Powered Real-Time Emergency Dispatch & Resource Coordination Command Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#F5F1E8] text-[#1F2933]">
        {children}
      </body>
    </html>
  );
}
