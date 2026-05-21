"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import {
  Upload as UploadIcon,
  FileCheck,
  ShieldCheck,
  Settings,
  Lock,
  Loader2,
  CheckCircle2,
  Circle,
  AlertTriangle,
  X,
} from "lucide-react";
import { vaultRepository } from "@/infrastructure/repositories/pyodide-vault.repository";
import { userRepository } from "@/infrastructure/repositories/api-user.repository";
import { fileRepository } from "@/infrastructure/repositories/api-file.repository";
import { User } from "@/core/domain/user.repository";
import { useRouter } from "next/navigation";
import PasswordModal from "@/app/components/PasswordModal/PasswordModal";

interface Toast {
  id: string;
  message: string;
}

export default function UploadPage() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isEngineReady, setIsEngineReady] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);

  // Password modal state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordModalLoading, setPasswordModalLoading] = useState(false);
  const [passwordModalError, setPasswordModalError] = useState<string | null>(null);

  const addToast = (message: string) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  };

  useEffect(() => {
    vaultRepository.isReady().then(() => {
      setIsEngineReady(true);
    });

    userRepository.getAllUsers().then(users => {
      setAvailableUsers(users);
      setIsLoadingUsers(false);
      setSelectedRecipients([]);
    });
  }, []);

  const handleFile = (newFiles: FileList | null) => {
    if (newFiles) {
      setFiles(prev => [...prev, ...Array.from(newFiles)]);
    }
  };

  const toggleRecipient = (id: string) => {
    setSelectedRecipients(prev =>
      prev.includes(id)
        ? prev.filter(uid => uid !== id)
        : [...prev, id]
    );
  };

  // Step 1: User clicks encrypt → show password modal
  const handleEncrypt = () => {
    if (files.length === 0) return;
    setPasswordModalError(null);
    setShowPasswordModal(true);
  };

  // Step 2: User submits password → perform encryption
  const handlePasswordSubmit = async (password: string) => {
    setPasswordModalLoading(true);
    setPasswordModalError(null);

    try {
      const currentUserStr = localStorage.getItem("vault_user");
      if (!currentUserStr) throw new Error("No active session found.");
      const currentUser = JSON.parse(currentUserStr);

      const file = files[0];
      const arrayBuffer = await file.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      const recipientsData = availableUsers
        .filter(u => selectedRecipients.includes(u.id))
        .map(u => ({ id: u.id, publicKeyPem: u.publicKeyBase64 }));

      // ALWAYS add the author to recipients so they can decrypt their own file
      if (!recipientsData.find(r => r.id === currentUser.id)) {
        recipientsData.push({
          id: currentUser.id,
          publicKeyPem: currentUser.publicKeys.encryption,
        });
      }

      const finalRecipientIds = [...new Set([...selectedRecipients, currentUser.id])];

      // Get encrypted signing keystore from session
      const keystoresStr = sessionStorage.getItem("vault_keystores");
      if (!keystoresStr) throw new Error("Session expired. Please log in again.");
      const keystores = JSON.parse(keystoresStr);
      const signKeystoreJson = JSON.stringify(keystores.signing);

      const encrypted = await vaultRepository.encrypt({
        file: uint8Array,
        fileName: file.name,
        recipients: recipientsData,
        signerId: currentUser.id,
        signerKeystoreJson: signKeystoreJson,
        password: password,
      });

      // Close modal on success
      setShowPasswordModal(false);

      // Save to vault storage
      await fileRepository.saveFile({
        id: crypto.randomUUID(),
        name: file.name,
        ownerId: currentUser.id,
        ownerName: currentUser.username,
        recipients: finalRecipientIds,
        createdAt: new Date().toISOString(),
        size: encrypted.length,
        encryptedContent: encrypted,
        signerPublicKeyBase64: keystores.signing?.publicPem || currentUser.publicKeys.signing,
      });

      router.push("/files");
    } catch (error: any) {
      console.error("Encryption failed:", error);
      const msg = error.message || "";

      if (msg.includes("CONTRASEÑA INCORRECTA") || msg.includes("KEYSTORE CORRUPTO")) {
        setPasswordModalError("Incorrect password. Please try again.");
      } else {
        setPasswordModalError(msg || "Encryption failed.");
      }
    } finally {
      setPasswordModalLoading(false);
    }
  };

  const handlePasswordCancel = () => {
    setShowPasswordModal(false);
    setPasswordModalError(null);
  };

  return (
    <div className={styles.container}>
      {/* Password Modal for encryption */}
      <PasswordModal
        isOpen={showPasswordModal}
        title="Sign & Encrypt"
        description="Enter your vault password to unlock your signing key and encrypt the payload."
        onSubmit={handlePasswordSubmit}
        onCancel={handlePasswordCancel}
        isLoading={passwordModalLoading}
        error={passwordModalError}
      />

      {/* Toast notifications */}
      <div className={styles.toastContainer}>
        {toasts.map((toast) => (
          <div key={toast.id} className={styles.toast}>
            <AlertTriangle size={16} />
            <span>{toast.message}</span>
            <button onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}>
              <X size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className={styles.header}>
        <h1 className={styles.title}>Secure Staging</h1>
        <p className={styles.subtitle}>
          Prepare, classify, and authorize payloads prior to encrypting and committing them to the institutional vault.
        </p>
        <div className={styles.headerBadge}>
          <ShieldCheck size={14} /> E2E Encryption Active
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.dropzoneCard}>
          <div
            className={`${styles.dropzone} ${isDragging ? styles.dragging : ""}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFile(e.dataTransfer.files); }}
            onClick={() => document.getElementById("fileInput")?.click()}
          >
            <input
              type="file"
              id="fileInput"
              hidden
              onChange={(e) => handleFile(e.target.files)}
            />
            <div className={styles.dropzoneIcon}>
              <UploadIcon size={32} />
            </div>
            <h3>Drag & Drop Payloads Here</h3>
            <p>or click to browse local secure storage.</p>
            <div className={styles.limitInfo}>
              <span>MAX SIZE: 50GB</span>
              <span>SUPPORTED: ALL FORMATS</span>
            </div>
          </div>

          <div className={styles.paramsCard}>
            <div className={styles.paramsHeader}>
              <Settings size={16} /> TRANSMISSION PARAMETERS
            </div>
            <div className={styles.paramsGrid}>
              <div className={styles.paramItem}>
                <label>PERSONNEL ACCESS CONTROL</label>
                <div className={styles.userList}>
                  {isLoadingUsers ? (
                    <div className={styles.loadingUsers}>Loading personnel...</div>
                  ) : (
                    availableUsers.map(user => (
                      <div
                        key={user.id}
                        className={`${styles.userRow} ${selectedRecipients.includes(user.id) ? styles.selectedUser : ""}`}
                        onClick={() => toggleRecipient(user.id)}
                      >
                        {selectedRecipients.includes(user.id)
                          ? <CheckCircle2 size={16} className={styles.checkIcon} />
                          : <Circle size={16} className={styles.uncheckIcon} />
                        }
                        <div className={styles.userInfo}>
                          <span className={styles.userName}>{user.username}</span>
                          <span className={styles.userEmail}>{user.id.substring(0, 8)}...</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <div className={styles.paramItem}>
                <label>SET PERMISSION LEVEL</label>
                <div className={styles.toggleGroup}>
                  <button className={styles.activeToggle}><Lock size={14} /> Encrypted</button>
                </div>
                <div className={styles.hint}>
                  Recipients will be able to decrypt using their private keys.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.queueCard}>
          <div className={styles.queueHeader}>
            <FileCheck size={18} /> STAGING QUEUE
            <span className={styles.itemCount}>{files.length} Items</span>
          </div>

          <div className={styles.queueList}>
            {files.length === 0 ? (
              <div className={styles.emptyQueue}>
                No files staged for transmission
              </div>
            ) : (
              files.map((file, i) => (
                <div key={i} className={styles.fileItem}>
                  <div className={styles.fileIcon}><FileCheck size={16} /></div>
                  <div className={styles.fileInfo}>
                    <div className={styles.fileName}>{file.name}</div>
                    <div className={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className={styles.queueFooter}>
            <div className={styles.totalInfo}>
              <span>TOTAL PAYLOAD</span>
              <strong>{(files.reduce((acc, f) => acc + f.size, 0) / (1024 * 1024)).toFixed(2)} MB</strong>
            </div>
            <button
              className={styles.commenceBtn}
              disabled={files.length === 0 || isProcessing || !isEngineReady}
              onClick={handleEncrypt}
            >
              {isProcessing ? (
                <><Loader2 className={styles.spinner} size={18} /> PROCESSING...</>
              ) : !isEngineReady ? (
                <><Loader2 className={styles.spinner} size={18} /> INITIALIZING ENGINE...</>
              ) : (
                <>
                  <ShieldCheck size={18} />
                  {selectedRecipients.length === 0 ? "PRIVATE TRANSFER" : "COMMENCE TRANSFER"}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}