import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Local RAG Chatbot",
  description: "A production-grade local RAG chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex h-screen bg-background">
            {/* Sidebar will go here in Phase 5 */}
            <div className="hidden w-64 border-r bg-muted/20 md:block">
              <div className="p-4 font-semibold">Local RAG Chatbot</div>
            </div>
            
            {/* Main content */}
            <main className="flex-1 flex flex-col min-w-0">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
