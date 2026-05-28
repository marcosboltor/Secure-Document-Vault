"use client";

import { useState } from "react";
import styles from "./page.module.css";
import {
  ShieldCheck,
  Key,
  Download,
  CheckCircle2,
  Loader2,
  ArrowRight,
  ShieldAlert,
  AlertCircle,
  Lock,
} from "lucide-react";
import { vaultRepository } from "@/infrastructure/repositories/pyodide-vault.repository";
import { authRepository } from "@/infrastructure/repositories/api-auth.repository";
import Link from "next/link";



export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [identity, setIdentity] = useState<any>(null);
  const [institutionalId, setInstitutionalId] = useState("");
  const [backendId, setBackendId] = useState<string>("");
  const [formData, setFormData] = useState({ name: "", email: "" });
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate passwords
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsGenerating(true);

    try {
      // 1. Generate raw keys in worker
      const rawIdentity = await vaultRepository.generateIdentity();

      // 2. Encrypt private keys with password using KeyProtector
      setIsRegistering(true);
      const keystoresJson = await vaultRepository.protectKeys(
        password,
        rawIdentity.encryption.private,
        rawIdentity.signing.private,
        formData.name
      );
      const keystores = JSON.parse(keystoresJson);

      // 3. Build the protected identity (no raw private keys)
      const protectedIdentity = {
        encryption: {
          keystore: keystores.encryption_keystore,
          public: rawIdentity.encryption.public,
          publicPem: rawIdentity.encryption.publicPem,
        },
        signing: {
          keystore: keystores.signing_keystore,
          public: rawIdentity.signing.public,
          publicPem: rawIdentity.signing.publicPem,
        },
      };

      setIdentity(protectedIdentity);

      // 4. Register public keys with backend
      const user = await authRepository.registerUser({
        email: formData.email,
        username: formData.name,
        public_encryption_key: rawIdentity.encryption.publicPem,
        public_signing_key: rawIdentity.signing.publicPem,
      });

      setInstitutionalId(user.id);
      setStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to generate identity.");
    } finally {
      setIsGenerating(false);
      setIsRegistering(false);
      // Clear password fields — password is no longer needed
      setPassword("");
      setConfirmPassword("");
    }
  };

  const downloadKeyFile = () => {
    if (!identity) return;
    const data = JSON.stringify(
      {
        name: formData.name,
        email: formData.email,
        identity,
        createdAt: new Date().toISOString(),
        institutionalId,
      },
      null,
      2
    );
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Vault_Identity_${formData.name.replace(/\s+/g, "_")}.json`;
    a.click();
  };

  return (
    <div className={styles.container}>
      <div className={styles.authCard}>
        <div className={styles.cardHeader}>
          <div className={styles.logoCircle}>
            <ShieldCheck size={32} />
          </div>
          <h1>Institutional Onboarding</h1>
          <p>Initialize your secure cryptographic identity for the Fortress Vault system.</p>
        </div>

        {step === 1 && (
          <form className={styles.form} onSubmit={handleGenerate}>
            <div className={styles.inputGroup}>
              <label>FULL LEGAL NAME</label>
              <input
                type="text"
                required
                placeholder="e.g. Eleanor Vance"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className={styles.inputGroup}>
              <label>INSTITUTIONAL EMAIL</label>
              <input
                type="email"
                required
                placeholder="e.g. e.vance@fortress.sys"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>

            <div className={styles.inputGroup}>
              <label><Lock size={12} /> VAULT PASSWORD</label>
              <input
                type="password"
                required
                placeholder="Min. 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                minLength={8}
              />
            </div>
            <div className={styles.inputGroup}>
              <label><Lock size={12} /> CONFIRM PASSWORD</label>
              <input
                type="password"
                required
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                minLength={8}
              />
            </div>

            <div className={styles.infoBox}>
              <ShieldAlert size={16} />
              <p>Your private keys will be encrypted with this password using PBKDF2 (600K iterations) + ChaCha20-Poly1305. The password is never transmitted or stored — only you can unlock your keys.</p>
            </div>

            {error && (
              <div className={styles.errorBox}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" className={styles.primaryBtn} disabled={isGenerating || isRegistering}>
              {isGenerating && !isRegistering ? (
                <><Loader2 className={styles.spinner} size={18} /> GENERATING KEYS...</>
              ) : isRegistering ? (
                <><Loader2 className={styles.spinner} size={18} /> ENCRYPTING & REGISTERING...</>
              ) : (
                <><Key size={18} /> INITIALIZE IDENTITY</>
              )}
            </button>

            <p className={styles.footerLink}>
              Already registered? <Link href="/">Access Vault</Link>
            </p>
          </form>
        )}

        {step === 2 && (
          <div className={styles.successView}>
            <div className={styles.successIcon}>
              <CheckCircle2 size={48} />
            </div>
            <h2>Identity Core Generated</h2>
            <p>Your cryptographic pairs have been established and encrypted with your password. You must download and secure your identity file to access the vault.</p>

            <div className={styles.keysPreview}>
              <div className={styles.keyItem}>
                <label>ENCRYPTION PUBLIC KEY (X25519)</label>
                <code>{identity.encryption.public.substring(0, 32)}...</code>
              </div>
              <div className={styles.keyItem}>
                <label>SIGNING PUBLIC KEY (ED25519)</label>
                <code>{identity.signing.public.substring(0, 32)}...</code>
              </div>
              <div className={styles.keyItem}>
                <label>KEY PROTECTION</label>
                <code>PBKDF2-HMAC-SHA256 (600K iterations) + ChaCha20-Poly1305</code>
              </div>
            </div>

            <button className={styles.downloadBtn} onClick={downloadKeyFile}>
              <Download size={18} /> DOWNLOAD IDENTITY FILE (.JSON)
            </button>

            <div className={styles.warningBox}>
              <strong>CRITICAL:</strong> Loss of this file or your password results in permanent loss of access to all encrypted archives. No recovery path exists.
            </div>

            <Link href="/" className={styles.finishBtn}>
              PROCEED TO LOGIN <ArrowRight size={18} />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
