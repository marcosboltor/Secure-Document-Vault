"use client";

import { useState, useEffect, useRef } from "react";
import styles from "./page.module.css";
import {
  Key,
  Download,
  Upload,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Copy,
  Clock,
  Lock,
  Info,
  X,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  RefreshCw,
  Ban,
  Timer,
} from "lucide-react";
import PasswordModal from "@/app/components/PasswordModal/PasswordModal";
import { vaultRepository } from "@/infrastructure/repositories/pyodide-vault.repository";

interface Toast {
  id: string;
  type: "success" | "error" | "warning";
  message: string;
}

type KeyStatus = "ACTIVE" | "ROTATED" | "REVOKED" | "EXPIRED" | string;

export default function KeysPage() {
  const [keystores, setKeystores] = useState<any>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordModalLoading, setPasswordModalLoading] = useState(false);
  const [passwordModalError, setPasswordModalError] = useState<string | null>(null);
  const [pendingRestore, setPendingRestore] = useState<any>(null);
  const [showSecurityWarnings, setShowSecurityWarnings] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addToast = (type: Toast["type"], message: string) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  };

  useEffect(() => {
    const user = localStorage.getItem("vault_user");
    if (user) setCurrentUser(JSON.parse(user));

    const ks = sessionStorage.getItem("vault_keystores");
    if (ks) setKeystores(JSON.parse(ks));
  }, []);

  const getKeyMetadata = (keyName: string) => {
    if (!keystores || !keystores[keyName]) return null;
    return keystores[keyName].metadata || null;
  };

  const getKeyStatus = (keyName: string): KeyStatus => {
    const meta = getKeyMetadata(keyName);
    return meta?.status || "ACTIVE";
  };

  const getStatusConfig = (status: KeyStatus) => {
    switch (status) {
      case "ACTIVE":
        return { label: "Active", icon: CheckCircle2, className: styles.statusActive };
      case "ROTATED":
        return { label: "Rotated", icon: RefreshCw, className: styles.statusRotated };
      case "REVOKED":
        return { label: "Revoked", icon: Ban, className: styles.statusRevoked };
      case "EXPIRED":
        return { label: "Expired", icon: Timer, className: styles.statusExpired };
      default:
        return { label: "Active", icon: CheckCircle2, className: styles.statusActive };
    }
  };

  const encMeta = getKeyMetadata("encryption");
  const signMeta = getKeyMetadata("signing");

  const handleDownloadBackup = () => {
    if (!keystores || !currentUser) return;

    const bundle = {
      name: currentUser.name || currentUser.username || "",
      email: currentUser.email || "",
      institutionalId: currentUser.id,
      identity: {
        encryption: {
          keystore: keystores.encryption,
          publicPem: currentUser.publicKeys?.encryption || "",
        },
        signing: {
          keystore: keystores.signing,
          publicPem: currentUser.publicKeys?.signing || "",
        },
      },
      createdAt: new Date().toISOString(),
    };

    const data = JSON.stringify(bundle, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Vault_Backup_${(currentUser.name || "user").replace(/\s+/g, "_")}_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);

    localStorage.setItem("vault_last_backup", new Date().toISOString());
    addToast("success", "Encrypted keystore backup downloaded successfully.");
  };

  const handleRestoreUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);

        // Validate structure: must have identity.encryption.keystore and identity.signing.keystore
        if (
          !json.identity?.encryption?.keystore ||
          !json.identity?.signing?.keystore
        ) {
          addToast("error", "Invalid backup: missing encrypted keystores. Please use a valid backup file.");
          return;
        }

        setPendingRestore(json);
        setPasswordModalError(null);
        setShowPasswordModal(true);
      } catch {
        addToast("error", "Failed to parse backup file. Ensure it is a valid .json file and has not been corrupted.");
      }
    };
    reader.readAsText(file);
  };

  const handleRestorePassword = async (password: string) => {
    if (!pendingRestore) return;

    setPasswordModalLoading(true);
    setPasswordModalError(null);

    try {
      // Verify the password by trying to sign a test challenge with the signing keystore
      const signKeystoreJson = JSON.stringify(pendingRestore.identity.signing.keystore);
      await vaultRepository.signChallengeWithKeystore(
        "restore-verification-challenge",
        signKeystoreJson,
        password
      );

      // Password is correct — restore the keystores into session
      const restoredKeystores = {
        encryption: pendingRestore.identity.encryption.keystore,
        signing: pendingRestore.identity.signing.keystore,
      };

      sessionStorage.setItem("vault_keystores", JSON.stringify(restoredKeystores));
      setKeystores(restoredKeystores);

      // Update user info if available
      if (currentUser && pendingRestore.institutionalId) {
        const updatedUser = {
          ...currentUser,
          id: pendingRestore.institutionalId,
          name: pendingRestore.name || currentUser.name,
          email: pendingRestore.email || currentUser.email,
          publicKeys: {
            encryption: pendingRestore.identity.encryption.publicPem || currentUser.publicKeys?.encryption || "",
            signing: pendingRestore.identity.signing.publicPem || currentUser.publicKeys?.signing || "",
          },
        };
        localStorage.setItem("vault_user", JSON.stringify(updatedUser));
        setCurrentUser(updatedUser);
      }

      setPendingRestore(null);
      setShowPasswordModal(false);
      addToast("success", "Keystore restored successfully. Both keys verified.");
    } catch (error: any) {
      const msg = error.message || "";
      if (msg.includes("CONTRASEÑA INCORRECTA") || msg.includes("CORRUPTO")) {
        setPasswordModalError("Incorrect password. Please verify and try again.");
      } else if (msg.includes("REVOCADO")) {
        setPasswordModalError("This keystore has been revoked due to a security compromise. It cannot be restored.");
      } else if (msg.includes("keystore no existe") || msg.includes("Missing")) {
        setPasswordModalError("Missing or corrupted keystore. The backup file may be damaged.");
      } else {
        setPasswordModalError(msg || "Backup restoration failed. The file may be damaged or incompatible.");
      }
    } finally {
      setPasswordModalLoading(false);
    }
  };

  const handlePasswordCancel = () => {
    setShowPasswordModal(false);
    setPendingRestore(null);
    setPasswordModalError(null);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast("success", "Copied to clipboard.");
  };

  const lastBackup = typeof window !== "undefined" ? localStorage.getItem("vault_last_backup") : null;

  const securityWarnings = [
    {
      icon: ShieldAlert,
      title: "Weak Passwords Reduce Security",
      description:
        "A weak or commonly-used password significantly reduces the protection of your keystore. " +
        "Use a strong, unique passphrase with high entropy. The system uses 600,000 PBKDF2 iterations " +
        "to slow down brute-force attacks, but this cannot compensate for the use of extremely weak passwords.",
      severity: "warning" as const,
    },
    {
      icon: Lock,
      title: "Stolen Keystore Cannot Decrypt Data Alone",
      description:
        "Even if an attacker obtains your keystore file, they cannot decrypt your private keys " +
        "without your password. The keystore is encrypted with ChaCha20-Poly1305 using a 256-bit " +
        "key derived via PBKDF2. Without the correct password, the data is cryptographically indistinguishable from noise.",
      severity: "info" as const,
    },
    {
      icon: AlertTriangle,
      title: "Compromised Device May Expose Keys",
      description:
        "If your device is infected with malware, has a keylogger, or an attacker has root access, " +
        "your private keys may be extracted from memory while they are temporarily decrypted during active use. " +
        "The system assumes your execution environment is not fully compromised.",
      severity: "danger" as const,
    },
    {
      icon: Download,
      title: "Backups Must Be Stored Securely",
      description:
        "Your backup files contain password-encrypted private keys. Store them on separate, " +
        "secure media (e.g., encrypted USB drive, offline storage). Never upload backups to " +
        "untrusted cloud services or share them over insecure channels.",
      severity: "warning" as const,
    },
  ];

  return (
    <div className={styles.container}>
      {/* Password Modal for Restore */}
      <PasswordModal
        isOpen={showPasswordModal}
        title="Verify Backup Password"
        description="Enter the password that was used to encrypt this keystore backup."
        onSubmit={handleRestorePassword}
        onCancel={handlePasswordCancel}
        isLoading={passwordModalLoading}
        error={passwordModalError}
      />

      {/* Toast notifications */}
      <div className={styles.toastContainer}>
        {toasts.map((toast) => (
          <div key={toast.id} className={`${styles.toast} ${styles[toast.type]}`}>
            {toast.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            <span>{toast.message}</span>
            <button onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}>
              <X size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h1 className={styles.title}>Key Management</h1>
          <p className={styles.subtitle}>
            View key lifecycle, download encrypted backups, and restore from backup files.
          </p>
        </div>
      </div>

      {/* Status Badge */}
      <div className={styles.statusCard}>
        {keystores ? (
          <div className={styles.statusBadge + " " + styles.statusProtected}>
            <ShieldCheck size={20} />
            <div>
              <strong>Keystore Protected</strong>
              <span>Your private keys are password-encrypted (ChaCha20-Poly1305 + PBKDF2)</span>
            </div>
          </div>
        ) : (
          <div className={styles.statusBadge + " " + styles.statusNone}>
            <Info size={20} />
            <div>
              <strong>No Keystore Loaded</strong>
              <span>Log in with your identity file to view key information.</span>
            </div>
          </div>
        )}
      </div>

      {/* Key Metadata with Lifecycle */}
      {keystores && (
        <div className={styles.cardsGrid}>
          {/* Encryption Key Card */}
          <div className={styles.keyCard}>
            <div className={styles.keyCardHeader}>
              <Key size={18} />
              <h3>Encryption Key</h3>
              <span className={styles.keyTypeBadge}>X25519</span>
            </div>
            {encMeta && (
              <div className={styles.metadataList}>
                <div className={styles.metaItem}>
                  <label>STATUS</label>
                  {(() => {
                    const status = getKeyStatus("encryption");
                    const config = getStatusConfig(status);
                    const StatusIcon = config.icon;
                    return (
                      <div className={`${styles.statusBadgeInline} ${config.className}`}>
                        <StatusIcon size={14} />
                        <span>{config.label}</span>
                      </div>
                    );
                  })()}
                </div>
                <div className={styles.metaItem}>
                  <label>KEY ID</label>
                  <div className={styles.metaValue}>
                    <code>{encMeta.key_id?.substring(0, 18)}...</code>
                    <button className={styles.copyBtn} onClick={() => copyToClipboard(encMeta.key_id)}>
                      <Copy size={12} />
                    </button>
                  </div>
                </div>
                <div className={styles.metaItem}>
                  <label>VERSION</label>
                  <span>v{encMeta.key_version}</span>
                </div>
                <div className={styles.metaItem}>
                  <label>CREATED</label>
                  <span>{encMeta.creation_date ? new Date(encMeta.creation_date).toLocaleDateString() : "—"}</span>
                </div>
                <div className={styles.metaItem}>
                  <label>ALGORITHM</label>
                  <span>{encMeta.encryption_algorithm}</span>
                </div>
                {encMeta.expires_at && (
                  <div className={styles.metaItem}>
                    <label>EXPIRES</label>
                    <span>{new Date(encMeta.expires_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Signing Key Card */}
          <div className={styles.keyCard}>
            <div className={styles.keyCardHeader}>
              <Lock size={18} />
              <h3>Signing Key</h3>
              <span className={styles.keyTypeBadge}>Ed25519</span>
            </div>
            {signMeta && (
              <div className={styles.metadataList}>
                <div className={styles.metaItem}>
                  <label>STATUS</label>
                  {(() => {
                    const status = getKeyStatus("signing");
                    const config = getStatusConfig(status);
                    const StatusIcon = config.icon;
                    return (
                      <div className={`${styles.statusBadgeInline} ${config.className}`}>
                        <StatusIcon size={14} />
                        <span>{config.label}</span>
                      </div>
                    );
                  })()}
                </div>
                <div className={styles.metaItem}>
                  <label>KEY ID</label>
                  <div className={styles.metaValue}>
                    <code>{signMeta.key_id?.substring(0, 18)}...</code>
                    <button className={styles.copyBtn} onClick={() => copyToClipboard(signMeta.key_id)}>
                      <Copy size={12} />
                    </button>
                  </div>
                </div>
                <div className={styles.metaItem}>
                  <label>VERSION</label>
                  <span>v{signMeta.key_version}</span>
                </div>
                <div className={styles.metaItem}>
                  <label>CREATED</label>
                  <span>{signMeta.creation_date ? new Date(signMeta.creation_date).toLocaleDateString() : "—"}</span>
                </div>
                <div className={styles.metaItem}>
                  <label>ALGORITHM</label>
                  <span>{signMeta.encryption_algorithm}</span>
                </div>
                {signMeta.expires_at && (
                  <div className={styles.metaItem}>
                    <label>EXPIRES</label>
                    <span>{new Date(signMeta.expires_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Security Warnings Section */}
      <div className={styles.warningsSection}>
        <button
          className={styles.warningsToggle}
          onClick={() => setShowSecurityWarnings(!showSecurityWarnings)}
        >
          <div className={styles.warningsToggleContent}>
            <ShieldAlert size={18} />
            <span>Security Warnings &amp; Information</span>
          </div>
          {showSecurityWarnings ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {showSecurityWarnings && (
          <div className={styles.warningsList}>
            {securityWarnings.map((warning, index) => {
              const WarningIcon = warning.icon;
              return (
                <div
                  key={index}
                  className={`${styles.warningItem} ${styles[`severity_${warning.severity}`]}`}
                >
                  <div className={styles.warningIcon}>
                    <WarningIcon size={18} />
                  </div>
                  <div className={styles.warningContent}>
                    <strong>{warning.title}</strong>
                    <p>{warning.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className={styles.actionsSection}>
        <h2 className={styles.sectionTitle}>Backup &amp; Restore</h2>

        <div className={styles.actionsGrid}>
          {/* Download Backup */}
          <div className={styles.actionCard}>
            <div className={styles.actionIcon}>
              <Download size={24} />
            </div>
            <h3>Download Backup</h3>
            <p>Export your encrypted keystore bundle as a local file. The backup is password-protected.</p>
            {lastBackup && (
              <div className={styles.lastBackup}>
                <Clock size={12} />
                <span>Last backup: {new Date(lastBackup).toLocaleDateString()}</span>
              </div>
            )}
            <button
              className={styles.actionBtn}
              onClick={handleDownloadBackup}
              disabled={!keystores}
            >
              <Download size={16} /> DOWNLOAD ENCRYPTED BACKUP
            </button>
          </div>

          {/* Restore Backup */}
          <div className={styles.actionCard}>
            <div className={styles.actionIcon}>
              <Upload size={24} />
            </div>
            <h3>Restore from Backup</h3>
            <p>Upload a previously exported identity file. You will need to verify with your password.</p>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleRestoreUpload}
              accept=".json"
              hidden
            />
            <button
              className={styles.actionBtnSecondary}
              onClick={() => fileInputRef.current?.click()}
              disabled={isValidating}
            >
              {isValidating ? (
                <><Loader2 className={styles.spinner} size={16} /> VALIDATING...</>
              ) : (
                <><Upload size={16} /> UPLOAD BACKUP FILE</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Security Info */}
      <div className={styles.infoSection}>
        <div className={styles.infoIcon}>
          <ShieldCheck size={16} />
        </div>
        <div>
          <strong>Security Notice</strong>
          <p>
            Backup files contain encrypted private keys. They cannot be used without
            the correct password. The backup does not weaken security — all
            cryptographic protections remain intact. If you suspect your keystore
            has been compromised, revoke your identity and generate new keys immediately.
          </p>
        </div>
      </div>
    </div>
  );
}
