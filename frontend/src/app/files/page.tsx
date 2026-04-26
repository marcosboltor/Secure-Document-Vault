"use client";

import { FileText } from "lucide-react";
import styles from "./page.module.css";

export default function FilesPage() {
  const files = [
    { id: "1", name: "document.pdf", size: "2.4 MB", date: "2024-01-15" },
    { id: "2", name: "report.docx", size: "1.2 MB", date: "2024-01-14" },
  ];

  return (
    <div>
      <h1 className={styles.title}>Files</h1>
      <div className={styles.table}>
        <div className={styles.header}>
          <span>Name</span>
          <span>Size</span>
          <span>Date</span>
        </div>
        {files.map((file) => (
          <div key={file.id} className={styles.row}>
            <span className={styles.name}>
              <FileText size={16} /> {file.name}
            </span>
            <span>{file.size}</span>
            <span>{file.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
}