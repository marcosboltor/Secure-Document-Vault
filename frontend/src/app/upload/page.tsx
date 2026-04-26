"use client";

import { useState, useCallback } from "react";
import { Upload, FileText } from "lucide-react";
import styles from "./page.module.css";

export default function UploadPage() {
  const [files, setFiles] = useState<{ id: string; name: string; size: string }[]>([]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files);
    setFiles((prev) => [
      ...prev,
      ...dropped.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        size: (f.size / 1024 / 1024).toFixed(1) + " MB",
      })),
    ]);
  }, []);

  const remove = (id: string) => setFiles((p) => p.filter((f) => f.id !== id));

  return (
    <div>
      <h1 className={styles.title}>Upload</h1>
      <div className={styles.dropzone} onDrop={onDrop} onDragOver={(e) => e.preventDefault()}>
        <Upload size={32} />
        <p>Drag files here</p>
      </div>
      {files.length > 0 && (
        <div className={styles.list}>
          {files.map((f) => (
            <div key={f.id} className={styles.file}>
              <FileText size={16} />
              <span>{f.name}</span>
              <span>{f.size}</span>
              <button onClick={() => remove(f.id)}>×</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}