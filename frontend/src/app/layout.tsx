import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AML Detection System",
  description: "A comprehensive Transactional and AML Detection monitor",
};

import { Sidebar } from "@/components/Sidebar";
import { AppShell } from "@/components/AppShell";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased text-text bg-canvas h-screen flex overflow-hidden`}
      >
        <Sidebar />
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
