"use client";

import styles from "./page.module.css";

export default function FilesPage() {
  const files = [
    { id: "1", name: "document.pdf", size: "2.4 MB", date: "2024-01-15", status: "encrypted" },
    { id: "2", name: "report.docx", size: "1.2 MB", date: "2024-01-14", status: "encrypted" },
  ];

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Files</h1>
      </div>
      <div className={styles.table}>
        <div className={styles.tableHeader}>
          <span>Name</span>
          <span>Size</span>
          <span>Date</span>
          <span>Status</span>
        </div>
        {files.map((file) => (
          <div key={file.id} className={styles.row}>
            <span className={styles.name}>{file.name}</span>
            <span>{file.size}</span>
            <span>{file.date}</span>
            <span className={styles.status}>{file.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}