"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, AlertCircle, Menu, Settings, Plus, File, X, Brain } from "lucide-react";
import ConversationSidebar from "@/components/ConversationSidebar";
import FileUploadButton from "@/components/FileUploadButton";
import SettingsModal from "@/components/SettingsModal";

type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  thoughts?: string;
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
  const [showThoughts, setShowThoughts] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [currentThoughts, setCurrentThoughts] = useState("");
  const [memoryModalOpen, setMemoryModalOpen] = useState(false);
  const [memoryInput, setMemoryInput] = useState("");
  const [personaToggle, setPersonaToggle] = useState(false);
  const [personaModalOpen, setPersonaModalOpen] = useState(false);
  const [personaInput, setPersonaInput] = useState("");
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
  
    useEffect(() => {
    const savedFiles = localStorage.getItem('rag_uploaded_files');
    if (savedFiles) {
      try {
        const parsedFiles = JSON.parse(savedFiles);
        
        // Only keep valid file objects with required properties
        const validFiles: UploadedFile[] = parsedFiles.filter((f: any) => 
          f.id && typeof f.name === 'string' && typeof f.url === 'string'
        );

        if (validFiles.length > 0) {
          setUploadedFiles(validFiles);
          
          // Add initial system message with file references for RAG context
          const now = new Date().toISOString();
          const initialMessage: Message = {
            id: crypto.randomUUID(),
            role: "system",
            content: `RAG Context Files:\n- ${validFiles.map(f => f.name).join(', ')}\n\nThese files are available for RAG retrieval.`,
            timestamp: now,
          };

          setMessages((prev) => [initialMessage, ...prev]);
        } else {
          localStorage.removeItem('rag_uploaded_files');
        }
      } catch (error) {
        console.error("Failed to parse saved files:", error);
        localStorage.removeItem('rag_uploaded_files');
      }
    }

    // Save uploaded files whenever they change
    if (uploadedFiles.length > 0) {
      try {
        const fileData = JSON.stringify(uploadedFiles.map(f => ({
          id: f.id,
          name: f.name,
          url: f.url,
          size: typeof f.size === 'number' ? f.size : undefined,
          type: typeof f.type === 'string' ? f.type : undefined,
        })));
        
        localStorage.setItem('rag_uploaded_files', fileData);
      } catch (error) {
        console.error("Failed to save uploaded files:", error);
      }
    } else if (!uploadedFiles.length && savedFiles !== null) {
      // Clear storage when no files are being tracked anymore
      localStorage.removeItem('rag_uploaded_files');
    }

  }, [uploadedFiles]);

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
    setIsThinking(true); // Set thinking state
    setCurrentThoughts(""); // Clear previous thoughts

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      if (showThoughts) {
        // Use streaming endpoint to show thoughts while loading
        const response = await fetch(`${apiUrl}/api/v1/chat/stream?message=${encodeURIComponent(userMessage.content)}&conversation_id=${currentConversationId || ''}&use_rag=true&use_persona=${personaToggle}`);
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        let botMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "",
          thoughts: "",
        };

        while (true) {
          const { value, done } = await reader!.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'thought') {
                botMessage.thoughts = data.content;
                setMessages((prev) => [...prev, { ...botMessage }]);
              } else if (data.type === 'answer') {
                botMessage.content = data.content;
                setMessages((prev) => [...prev, { ...botMessage }]);
              }
            }
          }
        }
        // Remove the temporary messages and add the final one
        setMessages((prev) => {
          const filtered = prev.filter(m => m.id !== botMessage.id);
          return [...filtered, { ...botMessage }];
        });
      } else {
        // Standard non-streaming request
        const res = await fetch(`${apiUrl}/api/v1/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage.content,
            conversation_id: currentConversationId,
            document_ids: uploadedFiles.map(f => f.id),
            use_rag: true,
            use_persona: personaToggle,
          }),
        });

        if (!res.ok) throw new Error('Failed to get response');

        const data = await res.json();
        const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response,
          thoughts: data.thoughts,
        };
        setMessages((prev) => [...prev, botResponse]);
        
        // Update conversation ID if this was a new conversation
        if (data.conversation_id && !currentConversationId) {
          setCurrentConversationId(data.conversation_id);
        }
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
      setIsThinking(false); // End thinking state
    }
  };

  const handleRefinePrompt = async () => {
    if (!input.trim() || isLoading) return;
    
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/chat/refine?message=${encodeURIComponent(input)}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to refine prompt');
      const data = await res.json();
      setInput(data.refined_message);
    } catch (error) {
      console.error("Error refining prompt:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateMemory = async () => {
    if (!currentConversationId) {
      alert("Please start a conversation first.");
      return;
    }
    setMemoryModalOpen(true);
  };

  const closeMemoryModal = () => {
    setMemoryModalOpen(false);
    setMemoryInput("");
  };

  const saveMemory = async () => {
    if (!memoryInput.trim()) return;
    
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/chat/memory?conversation_id=${currentConversationId}&memory=${encodeURIComponent(memoryInput)}`, {
        method: 'POST',
      });
      if (res.ok) {
        alert("Memory updated!");
        closeMemoryModal();
      }
    } catch (error) {
      console.error("Error updating memory:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenPersonaModal = () => {
    // Load current persona if exists
    const savedPersona = localStorage.getItem('userPersona') || '';
    setPersonaInput(savedPersona);
    setPersonaModalOpen(true);
  };

  const closePersonaModal = () => {
    setPersonaModalOpen(false);
  };

  const savePersona = async () => {
    if (!personaInput.trim()) {
      // Clear persona if empty
      localStorage.removeItem('userPersona');
      setPersonaModalOpen(false);
      setPersonaInput("");
      return;
    }
    
    try {
      // Save to localStorage for persistence
      localStorage.setItem('userPersona', personaInput);
      
      // TODO: Also save to backend if we had a user endpoint
      // For now, we'll just use localStorage
      
      setPersonaModalOpen(false);
      alert("Persona saved!");
    } catch (error) {
      console.error("Error saving persona:", error);
    } finally {
      setPersonaInput("");
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
              onClick={handleUpdateMemory}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Add to Memory"
            >
              <Brain className="w-5 h-5" />
            </button>
            <button
              onClick={handleOpenPersonaModal}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Edit Persona"
            >
              <User className="w-5 h-5" />
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
                {/* Show thinking state for the most recent assistant message if currently thinking */}
                {message.role === "assistant" && isThinking && message.id === messages[messages.length - 1]?.id && (
                  <div className="mb-3 p-3 bg-muted/50 rounded-lg text-xs italic text-muted-foreground border-l-2 border-primary/30">
                    <div className="font-bold mb-1 flex items-center gap-1">
                      <Bot className="w-3 h-3" /> AI Thought Process:
                    </div>
                    {currentThoughts || "Thinking..."}
                  </div>
                )}
                
                {/* Show thoughts if toggle is on and thoughts exist */}
                {message.thoughts && showThoughts && !isThinking && (
                  <div className="mb-3 p-3 bg-muted/50 rounded-lg text-xs italic text-muted-foreground border-l-2 border-primary/30">
                    <div className="font-bold mb-1 flex items-center gap-1">
                      <Bot className="w-3 h-3" /> AI Thought Process:
                    </div>
                    {message.thoughts}
                  </div>
                )}
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              </div>
            </div>
          ))}

          {/* Thinking Indicator */}
          {isLoading && isThinking && (
            <div className="flex gap-4 flex-row animate-in fade-in duration-300">
              <div className="flex-none w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <div className="bg-card border px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-1.5">
                <span className="text-xs italic text-muted-foreground">AI is thinking...</span>
              </div>
            </div>
          )}
          
          {/* Standard Loading Indicator (when not thinking) */}
          {isLoading && !isThinking && (
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
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${target.scrollHeight}px`;
              }}
            />
            <div className="flex items-center gap-1 mb-1 mr-1">
              <button
                type="button"
                onClick={handleRefinePrompt}
                disabled={!input.trim() || isLoading}
                className="p-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50 transition-colors"
                title="Refine Prompt"
              >
                <Sparkles className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setShowThoughts(!showThoughts)}
                className={`p-2 rounded-lg transition-colors ${
                  showThoughts ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                }`}
                title="Toggle AI Thoughts"
              >
                <div className="text-[10px] font-bold uppercase">Thoughts</div>
              </button>
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex-none w-10 h-10 mb-1 rounded-xl bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-s-colors shadow-sm active:scale-95"
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

      {/* Memory Modal */}
      {memoryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-card border rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary" />
                <h3 className="font-semibold">Add to Conversation Memory</h3>
              </div>
              <button onClick={closeMemoryModal} className="p-1 hover:bg-accent rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Tell the AI something about you or your preferences that it should remember for this specific conversation.
              </p>
              <textarea
                value={memoryInput}
                onChange={(e) => setMemoryInput(e.target.value)}
                placeholder="e.g., I prefer concise answers and I am a senior developer..."
                className="w-full h-32 p-3 rounded-xl border bg-background outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
            </div>
            <div className="p-6 border-t flex justify-end gap-3">
              <button
                onClick={closeMemoryModal}
                className="px-4 py-2 text-sm font-medium hover:bg-accent rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveMemory}
                disabled={!memoryInput.trim() || isLoading}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                Save Memory
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Persona Modal */}
      {personaModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-card border rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                <h3 className="font-semibold">Edit Your Persona</h3>
              </div>
              <button onClick={closePersonaModal} className="p-1 hover:bg-accent rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Describe yourself, your preferences, expertise, or anything that would help the AI provide more personalized responses.
              </p>
              <textarea
                value={personaInput}
                onChange={(e) => setPersonaInput(e.target.value)}
                placeholder="e.g., I'm a senior software engineer who prefers concise, technical answers. I enjoy hiking and photography."
                className="w-full h-32 p-3 rounded-xl border bg-background outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
            </div>
            <div className="p-6 border-t flex justify-end gap-3">
              <button
                onClick={closePersonaModal}
                className="px-4 py-2 text-sm font-medium hover:bg-accent rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={savePersona}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                Save Persona
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        apiUrl={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
      />

      {/* Persona Modal */}
      {personaModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-card border rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                <h3 className="font-semibold">Edit Your Persona</h3>
              </div>
              <button onClick={closePersonaModal} className="p-1 hover:bg-accent rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-muted-foreground mb-4">
                Describe yourself, your preferences, expertise, or anything that would help the AI provide more personalized responses.
              </p>
              <textarea
                value={personaInput}
                onChange={(e) => setPersonaInput(e.target.value)}
                placeholder="e.g., I'm a senior software engineer who prefers concise, technical answers. I enjoy hiking and photography."
                className="w-full h-32 p-3 rounded-xl border bg-background outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
            </div>
            <div className="p-6 border-t flex justify-end gap-3">
              <button
                onClick={closePersonaModal}
                className="px-4 py-2 text-sm font-medium hover:bg-accent rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={savePersona}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                Save Persona
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

