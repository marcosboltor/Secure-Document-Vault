"use client";

import styles from "./files.module.css";
import { FileText, Shield, MoreVertical, Upload, Filter } from "lucide-react";

export default function MyFiles() {
  const files = [
    { name: "Q3_Financial_Audit.pdf", owner: "J. Smith", date: "Oct 24, 2023", size: "4.2 MB", status: "Encrypted" },
    { name: "Security_Protocols_v2.docx", owner: "A. Kumar", date: "Oct 22, 2023", size: "1.8 MB", status: "Encrypted" },
    { name: "Client_Data_Archive.zip", owner: "J. Smith", date: "Oct 20, 2023", size: "145.6 MB", status: "Standard" },
  ];

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Secure Vault</h1>
          <p className={styles.subtitle}>Manage encrypted assets and permissions.</p>
        </div>
        <div className={styles.actions}>
          <button className={styles.secondaryBtn}>
            <Filter size={16} /> Filter Types
          </button>
          <button className={styles.primaryBtn}>
            <Upload size={16} /> Upload
          </button>
        </div>
      </div>

      <div className={styles.tableCard}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>NAME</th>
              <th>OWNER</th>
              <th>DATE ADDED</th>
              <th>SIZE</th>
              <th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file, i) => (
              <tr key={i}>
                <td>
                  <div className={styles.fileName}>
                    <div className={styles.fileIcon}>
                      <FileText size={18} />
                    </div>
                    <div>
                      <div className={styles.nameText}>{file.name}</div>
                      <div className={styles.statusText}>
                        <Shield size={10} /> {file.status}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <div className={styles.owner}>
                    <div className={styles.avatar}>{file.owner[0]}{file.owner.split(' ')[1][0]}</div>
                    {file.owner}
                  </div>
                </td>
                <td>{file.date}</td>
                <td>{file.size}</td>
                <td>
                  <MoreVertical size={16} className={styles.moreIcon} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className={styles.footer}>
          <span>Showing 1 to 3 of 42 entries</span>
          <div className={styles.pagination}>
            <button disabled>Prev</button>
            <button>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
