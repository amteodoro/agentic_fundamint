import type { Metadata } from "next";
import "./globals.css";
import { MainNav } from "./components/MainNav";
import ChatSidebar from "./components/ChatSidebar";
import { ChatContextProvider } from "./context/ChatContext";

export const metadata: Metadata = {
  title: "Fundamint",
  description: "Analyze stock fundamentals with AI-enhanced insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ChatContextProvider>
          <div className="border-b">
            <div className="flex h-16 items-center px-4">
              <MainNav />
            </div>
          </div>
          <div className="grid grid-cols-[3fr_1fr] h-[calc(100vh-4rem)]">
            <main className="overflow-y-auto p-4">{children}</main>
            <aside className="h-full">
              <ChatSidebar />
            </aside>
          </div>
        </ChatContextProvider>
      </body>
    </html>
  );
}
