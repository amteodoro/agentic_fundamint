import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MainNav } from "./components/MainNav";
import { ChatContextProvider } from "./context/ChatContext";
import { AuthProvider } from "./context/AuthContext";
import ChatSidebar from "./components/ChatSidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fundamint - AI Stock Analysis",
  description: "Deep fundamental analysis powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ChatContextProvider>
            <div className="flex h-screen overflow-hidden">
              <div className="flex-1 flex flex-col overflow-hidden">
                <MainNav />
                <div className="flex-1 overflow-auto">
                  {children}
                </div>
              </div>
              <ChatSidebar />
            </div>
          </ChatContextProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
