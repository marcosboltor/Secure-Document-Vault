"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { 
  File, 
  Download, 
  Trash2, 
  MoreVertical, 
  Shield, 
  Lock, 
  User, 
  Loader2,
  ExternalLink,
  Search,
  Settings2,
  CheckCircle,
  XCircle
} from "lucide-react";
import { fileRepository } from "@/infrastructure/repositories/local-file.repository";
import { vaultRepository } from "@/infrastructure/repositories/pyodide-vault.repository";
import { VaultFile } from "@/core/domain/file.repository";

export default function FilesPage() {
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);

  useEffect(() => {
    const user = localStorage.getItem("vault_user");
    if (user) setCurrentUser(JSON.parse(user));
    
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const allFiles = await fileRepository.getAllFiles();
      setFiles(allFiles.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()));
    } catch (error) {
      console.error("Failed to load files:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadEncrypted = (file: VaultFile) => {
    const blob = new Blob([file.encryptedContent], { type: "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${file.name}.vault`;
    a.click();
  };

  const handleDownloadDecrypted = async (file: VaultFile) => {
    if (!currentUser) return;
    setIsProcessing(file.id);

    try {
      // Get private keys from session
      const privateKeys = JSON.parse(sessionStorage.getItem("vault_private_keys") || "{}");
      const userPrivX = privateKeys.encryption?.private;

      if (!userPrivX) throw new Error("Private key not found in session. Please log in again.");

      const decrypted = await vaultRepository.decrypt({
        vaultFile: file.encryptedContent,
        userId: currentUser.id,
        userPrivateKeyBase64: userPrivX,
        signerPublicKeyBase64: file.signerPublicKeyBase64
      });

      const blob = new Blob([decrypted], { type: "application/octet-stream" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;
      a.click();
    } catch (error: any) {
      console.error("Decryption failed:", error);
      alert(error.message || "Decryption failed. You might not have access to this file.");
    } finally {
      setIsProcessing(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this archive permanently?")) return;
    await fileRepository.deleteFile(id);
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h1 className={styles.title}>Secure Archive</h1>
          <p className={styles.subtitle}>Institutional repository of encrypted payloads and authorized transmissions.</p>
        </div>
        <div className={styles.actions}>
          <div className={styles.searchBox}>
            <Search size={16} />
            <input type="text" placeholder="Search archives..." />
          </div>
          <button className={styles.filterBtn}><Settings2 size={16} /></button>
        </div>
      </div>

      <div className={styles.tableCard}>
        {isLoading ? (
          <div className={styles.loadingState}>
            <Loader2 className={styles.spinner} size={40} />
            <p>Scanning vault sectors...</p>
          </div>
        ) : files.length === 0 ? (
          <div className={styles.emptyState}>
            <Lock size={48} className={styles.emptyIcon} />
            <h3>No Active Transmissions</h3>
            <p>Your institutional vault is currently empty. Upload payloads to begin.</p>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>PAYLOAD NAME</th>
                  <th>ORIGIN / OWNER</th>
                  <th>STAGING DATE</th>
                  <th>SIZE</th>
                  <th>ACCESS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.id}>
                    <td>
                      <div className={styles.fileNameCell}>
                        <div className={styles.fileIcon}><File size={18} /></div>
                        <span>{file.name}</span>
                      </div>
                    </td>
                    <td>
                      <div className={styles.ownerCell}>
                        <User size={14} />
                        <span>{file.ownerName}</span>
                        {file.ownerId === currentUser?.id && <span className={styles.badge}>OWNER</span>}
                      </div>
                    </td>
                    <td>{new Date(file.createdAt).toLocaleDateString()}</td>
                    <td>{(file.size / 1024).toFixed(1)} KB</td>
                    <td>
                      <div className={styles.accessCell}>
                        {file.recipients.includes(currentUser?.id) ? (
                          <CheckCircle size={14} className={styles.authorized} />
                        ) : (
                          <XCircle size={14} className={styles.unauthorized} />
                        )}
                        <span>{file.recipients.length} Personnel</span>
                      </div>
                    </td>
                    <td>
                      <div className={styles.actionGroup}>
                        {isProcessing === file.id ? (
                          <Loader2 className={styles.spinner} size={18} />
                        ) : (
                          <>
                            <button 
                              className={styles.actionBtn} 
                              title="Download Plaintext"
                              onClick={() => handleDownloadDecrypted(file)}
                              disabled={!file.recipients.includes(currentUser?.id)}
                            >
                              <Download size={16} />
                            </button>
                            <button 
                              className={styles.actionBtn} 
                              title="Download Encrypted (.vault)"
                              onClick={() => handleDownloadEncrypted(file)}
                            >
                              <Shield size={16} />
                            </button>
                            {file.ownerId === currentUser?.id && (
                              <button 
                                className={`${styles.actionBtn} ${styles.deleteBtn}`} 
                                title="Delete Archive"
                                onClick={() => handleDelete(file.id)}
                              >
                                <Trash2 size={16} />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}