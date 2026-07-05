"use client";

import { useState, useEffect, useRef } from "react";
import { Plus, Trash2, MessageSquare, X, ChevronLeft, Edit2, Zap } from "lucide-react";

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
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const swipeRef = useRef<HTMLDivElement>(null);
  const [swipeStartX, setSwipeStartX] = useState(0);
  const [swipeEndX, setSwipeEndX] = useState(0);

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

  const handleEditConversation = (id: string, title: string) => {
    setEditingConversationId(id);
    setEditTitle(title);
  };

  const saveEditedConversation = async () => {
    if (!editingConversationId || !editTitle.trim()) return;

    try {
      const res = await fetch(`${apiUrl}/api/v1/conversations/${editingConversationId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editTitle }),
      });
      if (res.ok) {
        const updatedConversation = await res.json();
        setConversations((prev) =>
          prev.map((c) => (c.id === editingConversationId ? updatedConversation : c))
        );
        setEditingConversationId(null);
        setEditTitle("");
      }
    } catch (error) {
      console.error("Failed to update conversation:", error);
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

  const handleSwipeStart = (e: React.TouchEvent) => {
    setSwipeStartX(e.touches[0].clientX);
  };

  const handleSwipeEnd = (e: React.TouchEvent) => {
    setSwipeEndX(e.changedTouches[0].clientX);
    const diff = swipeStartX - swipeEndX;

    // Swipe left (next conversation)
    if (diff > 50) {
      const currentIndex = conversations.findIndex((c) => c.id === currentConversationId);
      if (currentIndex !== -1 && currentIndex < conversations.length - 1) {
        const nextConversation = conversations[currentIndex + 1];
        onConversationSelect(nextConversation.id);
        onClose();
      }
    }
    // Swipe right (previous conversation)
    else if (diff < -50) {
      const currentIndex = conversations.findIndex((c) => c.id === currentConversationId);
      if (currentIndex !== -1 && currentIndex > 0) {
        const prevConversation = conversations[currentIndex - 1];
        onConversationSelect(prevConversation.id);
        onClose();
      }
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
        ref={swipeRef}
        onTouchStart={handleSwipeStart}
        onTouchEnd={handleSwipeEnd}
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
                        {editingConversationId === conversation.id ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              onBlur={saveEditedConversation}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  saveEditedConversation();
                                } else if (e.key === "Escape") {
                                  setEditingConversationId(null);
                                  setEditTitle("");
                                }
                              }}
                              className="border border-primary/30 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary/20"
                              autoFocus
                            />
                            <button
                              onClick={saveEditedConversation}
                              className="px-2 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => {
                                setEditingConversationId(null);
                                setEditTitle("");
                              }}
                              className="px-2 py-1 text-muted-foreground hover:text-primary transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <>
                            <h3 className="font-medium truncate text-sm">
                              {conversation.title}
                            </h3>
                            <p className="text-xs opacity-70 mt-1">
                              {conversation.message_count} messages
                            </p>
                          </>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {!editingConversationId && (
                          <>
                            <button
                              onClick={() => handleEditConversation(conversation.id, conversation.title)}
                              className="p-1 hover:bg-accent rounded-full transition-colors"
                              title="Edit conversation"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
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
                          </>
                        )}
                      </div>
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
