"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, AlertCircle, Menu, Settings, Plus, File, X } from "lucide-react";
import ConversationSidebar from "@/components/ConversationSidebar";
import FileUploadButton from "@/components/FileUploadButton";
import SettingsModal from "@/components/SettingsModal";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type UploadedFile = {
  id: string;
  name: string;
  size: number;
  type: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I am your Local RAG Chatbot. How can I assist you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"healthy" | "error" | "checking">("checking");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto", block: "end" });
  }, [messages, isLoading]);

  // Check backend health quietly in the background
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/health`);
        if (res.ok) setHealthStatus("healthy");
        else setHealthStatus("error");
      } catch {
        setHealthStatus("error");
      }
    };
    checkHealth();
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: currentConversationId,
          document_ids: uploadedFiles.map(f => f.id),
          use_rag: true,
        }),
      });

      if (!res.ok) throw new Error('Failed to get response');

      const data = await res.json();
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
      };
      setMessages((prev) => [...prev, botResponse]);
      
      // Update conversation ID if this was a new conversation
      if (data.conversation_id && !currentConversationId) {
        setCurrentConversationId(data.conversation_id);
      }
    } catch (error) {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error connecting to the backend. Please try again.",
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewConversation = () => {
    setMessages([
      {
        id: "1",
        role: "assistant",
        content: "Hello! I am your Local RAG Chatbot. How can I assist you today?",
      },
    ]);
    setCurrentConversationId(null);
  };

  const handleFileUpload = (fileData: { id: string; name: string; size: number; type: string }) => {
    setUploadedFiles((prev) => [...prev, fileData]);
  };

  const handleFileDelete = async (fileId: string, fileName: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/documents/${fileId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
      } else {
        console.error("Failed to delete file:", fileName);
      }
    } catch (error) {
      console.error("Error deleting file:", error);
    }
  };

  const handleConversationSelect = (id: string) => {
    setCurrentConversationId(id);
    // TODO: Load conversation messages from backend
    setMessages([
      {
        id: "1",
        role: "assistant",
        content: "Conversation loaded. How can I help you?",
      },
    ]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="flex h-screen min-h-screen overflow-hidden bg-background relative">
      {/* Background Gradient Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-500/10 blur-[120px] pointer-events-none" />

      {/* Conversation Sidebar */}
      <ConversationSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onNewConversation={handleNewConversation}
      />

      {/* Main Content */}
      <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 flex-none flex items-center justify-between px-6 py-4 border-b bg-background/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-accent rounded-lg transition-colors lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-semibold text-lg tracking-tight">RAG Assistant</h1>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                {healthStatus === "checking" && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" /> Checking Backend</span>}
                {healthStatus === "healthy" && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" /> Backend Online</span>}
                {healthStatus === "error" && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-destructive" /> Backend Offline</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleNewConversation}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="New conversation"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={() => setSettingsOpen(true)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </header>

      {/* Messages Area */}
      <main className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 scroll-smooth z-10">
        <div className="max-w-3xl mx-auto flex flex-col gap-6 pb-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              } animate-in fade-in slide-in-from-bottom-4 duration-500`}
            >
              <div
                className={`flex-none w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center shadow-sm ${
                  message.role === "user"
                    ? "bg-secondary text-secondary-foreground"
                    : "bg-primary text-primary-foreground"
                }`}
              >
                {message.role === "user" ? (
                  <User className="w-4 h-4 sm:w-5 sm:h-5" />
                ) : (
                  <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
                )}
              </div>

              <div
                className={`max-w-[85%] sm:max-w-[75%] px-4 sm:px-5 py-3 rounded-2xl text-[15px] leading-relaxed ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground rounded-tr-sm shadow-md shadow-primary/10"
                    : "bg-card text-card-foreground border rounded-tl-sm shadow-sm"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex gap-4 flex-row animate-in fade-in duration-300">
              <div className="flex-none w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <div className="bg-card border px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-1.5">
                <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="flex-none p-4 sm:p-6 bg-gradient-to-t from-background via-background to-transparent z-10 pt-8 mt-auto">
        <div className="max-w-3xl mx-auto relative">
          {/* Uploaded Files Section */}
          {uploadedFiles.length > 0 && (
            <div className="mb-4 p-3 bg-card border rounded-xl">
              <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">Files for RAG Context</p>
              <div className="flex flex-wrap gap-2">
                {uploadedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center gap-2 bg-primary/5 border border-primary/20 rounded-lg px-3 py-2 text-sm hover:bg-primary/10 transition-colors"
                  >
                    <File className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="truncate flex-1 font-medium text-foreground">{file.name}</span>
                    <button
                      onClick={() => handleFileDelete(file.id, file.name)}
                      className="flex-shrink-0 p-1 hover:bg-destructive/20 rounded text-destructive hover:text-destructive/90 transition-colors"
                      title="Delete file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {healthStatus === "error" && (
            <div className="absolute -top-12 left-0 right-0 mx-auto w-max bg-destructive/10 text-destructive text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 border border-destructive/20 shadow-sm backdrop-blur-sm">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Backend is offline. Chat will use mock responses.</span>
            </div>
          )}
          
          <form
            onSubmit={handleSend}
            className="relative flex items-end gap-2 bg-card border shadow-sm focus-within:shadow-md focus-within:ring-1 focus-within:ring-primary/50 rounded-2xl p-2 transition-all duration-300"
          >
            <FileUploadButton apiUrl={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'} onFileUpload={handleFileUpload} />
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything..."
              className="w-full max-h-[200px] min-h-[44px] bg-transparent resize-none outline-none py-3 px-4 text-[15px] placeholder:text-muted-foreground scrollbar-thin scrollbar-thumb-muted"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex-none w-10 h-10 mb-1 mr-1 rounded-xl bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors shadow-sm active:scale-95"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </form>
          <div className="text-center mt-3 text-xs text-muted-foreground/60 font-medium">
            AI can make mistakes. Verify important information.
          </div>
        </div>
      </footer>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        apiUrl={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
      />
    </div>
  );
}

