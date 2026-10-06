import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "Nutrivault — AI Nutrition Knowledge",
  description:
    "Ask nutrition questions and get answers grounded in retrieved nutrition data.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="flex min-h-screen flex-col bg-surface font-sans text-ink antialiased">
        <Header />
        {children}
      </body>
    </html>
  );
}
