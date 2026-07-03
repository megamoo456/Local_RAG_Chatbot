"use client";

import { useState, useEffect } from "react";
import { Settings, Globe, Key, Plus, Trash2, X, Save } from "lucide-react";

type APIConfig = {
  id: string;
  name: string;
  provider: string;
  base_url: string | null;
  model: string | null;
  is_active: boolean;
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiUrl?: string;
}

export default function SettingsModal({ isOpen, onClose, apiUrl = "http://localhost:8000" }: SettingsModalProps) {
  const [enableInternetSearch, setEnableInternetSearch] = useState(false);
  const [apiConfigs, setApiConfigs] = useState<APIConfig[]>([]);
  const [showAddAPI, setShowAddAPI] = useState(false);
  const [newAPI, setNewAPI] = useState({
    name: "",
    provider: "openai",
    api_key: "",
    base_url: "",
    model: "",
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
      fetchAPIConfigs();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/settings/system`);
      if (res.ok) {
        const data = await res.json();
        setEnableInternetSearch(data.enable_internet_search);
      }
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    }
  };

  const fetchAPIConfigs = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/settings/api-configs`);
      if (res.ok) {
        const data = await res.json();
        setApiConfigs(data || []);
      }
    } catch (error) {
      console.error("Failed to fetch API configs:", error);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      const res = await fetch(`${apiUrl}/api/v1/settings/system`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enable_internet_search: enableInternetSearch,
          enable_rag: true,
          max_conversation_history: 50,
          default_temperature: 0.7,
          default_top_p: 0.9,
        }),
      });
      if (res.ok) {
        onClose();
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddAPI = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/settings/api-configs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newAPI),
      });
      if (res.ok) {
        await fetchAPIConfigs();
        setNewAPI({
          name: "",
          provider: "openai",
          api_key: "",
          base_url: "",
          model: "",
        });
        setShowAddAPI(false);
      }
    } catch (error) {
      console.error("Failed to add API config:", error);
    }
  };

  const handleDeleteAPI = async (id: string) => {
    if (!confirm("Are you sure you want to delete this API configuration?")) return;

    try {
      const res = await fetch(`${apiUrl}/api/v1/settings/api-configs/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setApiConfigs((prev) => prev.filter((c) => c.id !== id));
      }
    } catch (error) {
      console.error("Failed to delete API config:", error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Settings className="w-5 h-5 text-primary" />
            </div>
            <h2 className="text-xl font-semibold">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)] space-y-6">
          {/* Internet Search Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary" />
              <h3 className="font-semibold">Internet Search</h3>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent rounded-xl">
              <div>
                <p className="font-medium">Enable Internet Search</p>
                <p className="text-sm text-muted-foreground">Allow the AI to search the web for current information</p>
              </div>
              <button
                onClick={() => setEnableInternetSearch(!enableInternetSearch)}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  enableInternetSearch ? "bg-primary" : "bg-muted"
                }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                    enableInternetSearch ? "translate-x-7" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>

          {/* API Configurations Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-5 h-5 text-primary" />
                <h3 className="font-semibold">API Configurations</h3>
              </div>
              <button
                onClick={() => setShowAddAPI(!showAddAPI)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add API
              </button>
            </div>

            {showAddAPI && (
              <div className="p-4 bg-accent rounded-xl space-y-3 animate-in fade-in slide-in-from-top-2">
                <input
                  type="text"
                  placeholder="Name (e.g., OpenAI GPT-4)"
                  value={newAPI.name}
                  onChange={(e) => setNewAPI({ ...newAPI, name: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                />
                <select
                  value={newAPI.provider}
                  onChange={(e) => setNewAPI({ ...newAPI, provider: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
                <input
                  type="password"
                  placeholder="API Key"
                  value={newAPI.api_key}
                  onChange={(e) => setNewAPI({ ...newAPI, api_key: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                />
                <input
                  type="text"
                  placeholder="Base URL (optional)"
                  value={newAPI.base_url}
                  onChange={(e) => setNewAPI({ ...newAPI, base_url: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                />
                <input
                  type="text"
                  placeholder="Model (optional)"
                  value={newAPI.model}
                  onChange={(e) => setNewAPI({ ...newAPI, model: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg text-sm"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddAPI}
                    className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setShowAddAPI(false)}
                    className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {apiConfigs.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No API configurations added</p>
              ) : (
                apiConfigs.map((config) => (
                  <div
                    key={config.id}
                    className="flex items-center justify-between p-4 bg-accent rounded-xl"
                  >
                    <div>
                      <p className="font-medium">{config.name}</p>
                      <p className="text-sm text-muted-foreground">{config.provider}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteAPI(config.id)}
                      className="p-2 hover:bg-background rounded-lg transition-colors text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-muted/30">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSaveSettings}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
