"use client";

import { useState, useCallback } from "react";
import { Upload as UploadIcon, FileText, X } from "lucide-react";
import styles from "./page.module.css";

interface FileItem {
  id: string;
  name: string;
  size: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles((prev) => [
      ...prev,
      ...droppedFiles.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        size: (f.size / 1024 / 1024).toFixed(1) + " MB",
      })),
    ]);
  }, []);

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div>
      <h1 className={styles.title}>Upload</h1>
      <div
        className={`${styles.dropzone} ${dragOver ? styles.active : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <UploadIcon size={32} />
        <p>Drag & drop files here</p>
      </div>
      {files.length > 0 && (
        <div className={styles.list}>
          {files.map((file) => (
            <div key={file.id} className={styles.file}>
              <FileText size={18} />
              <span>{file.name}</span>
              <span>{file.size}</span>
              <button onClick={() => removeFile(file.id)}>
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}