"use client";

import { useState, useEffect } from "react";
import { Plus, Trash2, MessageSquare, X, ChevronLeft } from "lucide-react";

type Conversation = {
  id: string;
  title: string;
  message_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

interface ConversationSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentConversationId: string | null;
  onConversationSelect: (id: string) => void;
  onNewConversation: () => void;
  apiUrl?: string;
}

export default function ConversationSidebar({
  isOpen,
  onClose,
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  apiUrl = "http://localhost:8000",
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchConversations();
    }
  }, [isOpen]);

  const fetchConversations = async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`${apiUrl}/api/v1/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    try {
      setIsDeleting(id);
      const res = await fetch(`${apiUrl}/api/v1/conversations/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (currentConversationId === id) {
          onNewConversation();
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    } finally {
      setIsDeleting(null);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Chat" }),
      });
      if (res.ok) {
        const newConversation = await res.json();
        setConversations((prev) => [newConversation, ...prev]);
        onConversationSelect(newConversation.id);
        onClose();
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-80 bg-card border-r z-50
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0 lg:static lg:z-0
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-lg">Conversations</h2>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={handleCreateConversation}
              className="w-full flex items-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span className="font-medium">New Chat</span>
            </button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto px-3 pb-4">
            {isLoading ? (
              <div className="text-center text-muted-foreground py-8">
                Loading conversations...
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No conversations yet
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    onClick={() => {
                      onConversationSelect(conversation.id);
                      onClose();
                    }}
                    className={`
                      group relative p-3 rounded-xl cursor-pointer transition-all
                      ${
                        currentConversationId === conversation.id
                          ? "bg-primary text-primary-foreground shadow-md"
                          : "bg-accent hover:bg-accent/80"
                      }
                    `}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate text-sm">
                          {conversation.title}
                        </h3>
                        <p className="text-xs opacity-70 mt-1">
                          {conversation.message_count} messages
                        </p>
                      </div>
                      <button
                        onClick={(e) => handleDeleteConversation(e, conversation.id)}
                        disabled={isDeleting === conversation.id}
                        className={`
                          opacity-0 group-hover:opacity-100 transition-opacity
                          p-1.5 hover:bg-black/10 dark:hover:bg-white/10 rounded-lg
                          ${currentConversationId === conversation.id ? "text-primary-foreground" : "text-muted-foreground"}
                        `}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
