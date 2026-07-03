"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";

interface FileUploadButtonProps {
  onFileUpload?: (fileData: { id: string; name: string; size: number; type: string }) => void;
  apiUrl?: string;
}

export default function FileUploadButton({ onFileUpload, apiUrl = "http://localhost:8000" }: FileUploadButtonProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus("idle");
    setUploadedFileName(file.name);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${apiUrl}/api/v1/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadStatus("success");
        if (onFileUpload) {
          onFileUpload({
            id: data.id,
            name: data.filename,
            size: data.file_size,
            type: data.file_type,
          });
        }
      } else {
        setUploadStatus("error");
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("error");
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.pptx,.txt,.md,.html"
        onChange={handleFileSelect}
        className="hidden"
      />
      
      <button
        onClick={handleClick}
        disabled={isUploading}
        className="p-2 hover:bg-accent rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Upload file"
      >
        {isUploading ? (
          <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        ) : (
          <Upload className="w-5 h-5" />
        )}
      </button>

      {/* Upload Status Popup */}
      {uploadStatus !== "idle" && uploadedFileName && (
        <div className="absolute bottom-full left-0 mb-2 w-64 bg-card border rounded-lg shadow-lg p-3 animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-start gap-3">
            <div className="flex-none">
              {uploadStatus === "success" ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-500" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{uploadedFileName}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {uploadStatus === "success" ? "Upload successful" : "Upload failed"}
              </p>
            </div>
            <button
              onClick={() => {
                setUploadStatus("idle");
                setUploadedFileName(null);
              }}
              className="flex-none p-1 hover:bg-accent rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
