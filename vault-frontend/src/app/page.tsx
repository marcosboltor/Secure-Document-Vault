"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Fingerprint, Lock, Upload, CheckCircle2, ShieldCheck, AlertCircle, Loader2 } from "lucide-react";
import Image from "next/image";
import styles from "./page.module.css";
import { vaultRepository } from "@/infrastructure/repositories/pyodide-vault.repository";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function Home() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [identity, setIdentity] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isEngineReady, setIsEngineReady] = useState(false);

  useEffect(() => {
    vaultRepository.isReady().then(() => setIsEngineReady(true));
  }, []);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);

        if (
          json.identity &&
          json.identity.encryption?.keystore &&
          json.identity.signing?.keystore
        ) {
          setIdentity(json);
          setError(null);
        } else {
          setError("Invalid identity file. Please re-register to generate a password-protected identity.");
        }
      } catch {
        setError("Failed to parse identity file.");
      }
    };
    reader.readAsText(file);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identity) {
      setError("Please upload your identity file to initialize session.");
      return;
    }
    if (!password) {
      setError("Please enter your vault password.");
      return;
    }

    setIsLoggingIn(true);
    setError(null);

    try {
      const userId = identity.institutionalId;
      const signKeystoreJson = JSON.stringify(identity.identity.signing.keystore);


      const challenge = crypto.randomUUID();
      const signature = await vaultRepository.signChallengeWithKeystore(
        challenge,
        signKeystoreJson,
        password
      );

      const loginRes = await fetch(`${API_URL}/api/v1/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          challenge,
          signature,
        }),
      });

      if (!loginRes.ok) {
        const err = await loginRes.json().catch(() => ({}));
        throw new Error(err.detail || "Authentication failed. Check your identity file or password.");
      }

      const { access_token, refresh_token } = await loginRes.json();

      // Store tokens
      document.cookie = `access_token=${access_token}; path=/; max-age=3600; samesite=strict`;
      document.cookie = `refresh_token=${refresh_token}; path=/; max-age=86400; samesite=strict`;
      localStorage.setItem("vault_token", access_token);
      localStorage.setItem("vault_refresh_token", refresh_token);

      // Store user info (public only)
      localStorage.setItem("vault_user", JSON.stringify({
        id: userId,
        username: identity.name,
        name: identity.name,
        email: identity.email,
        publicKeys: {
          encryption: identity.identity.encryption.publicPem,
          signing: identity.identity.signing.publicPem,
        },
      }));

      // Store encrypted keystores in sessionStorage (safe — they are password-encrypted)
      sessionStorage.setItem("vault_keystores", JSON.stringify({
        encryption: identity.identity.encryption.keystore,
        signing: identity.identity.signing.keystore,
      }));

      router.push("/files");
    } catch (err: any) {
      // Check if it's a password error from KeyProtector
      const msg = err.message || "Login failed.";
      if (msg.includes("CONTRASEÑA INCORRECTA") || msg.includes("KEYSTORE CORRUPTO")) {
        setError("Incorrect password or corrupted keystore.");
      } else {
        setError(msg);
      }
    } finally {
      setIsLoggingIn(false);
      // Clear password from state — never persist
      setPassword("");
    }
  };

  return (
    <main className={styles.container}>
      <div className={styles.card}>
        <div className={styles.logoSection}>
          <div className={styles.logoWrapper}>
            <Image
              src="/logo.png"
              alt="Vault Logo"
              width={160}
              height={160}
              className={styles.logoImg}
              priority
              quality={100}
            />
          </div>
          <div className={styles.logoText}>
            <h2>VAULT</h2>
            <p>Institutional Security</p>
          </div>
        </div>

        <form className={styles.form} onSubmit={handleLogin}>
          <div className={styles.inputGroup}>
            <label>Cryptographic Identity File</label>
            <div
              className={`${styles.fileUploadZone} ${identity ? styles.fileUploaded : ""}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".json"
                hidden
              />
              {identity ? (
                <div className={styles.fileSuccess}>
                  <CheckCircle2 size={20} />
                  <span>{identity.name}&apos;s Core Loaded</span>
                </div>
              ) : (
                <div className={styles.filePlaceholder}>
                  <Upload size={20} />
                  <span>Click to upload .json identity</span>
                </div>
              )}
            </div>
          </div>

          {identity && (
            <div className={styles.inputGroup}>
              <label>Vault Password</label>
              <input
                type="password"
                className={styles.input}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your vault password"
                autoComplete="off"
                required
              />
            </div>
          )}

          {error && (
            <div className={styles.errorBox}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className={styles.primaryButton} disabled={!identity || !password || isLoggingIn || !isEngineReady}>
            {!isEngineReady ? (
              <><Loader2 size={18} className={styles.spinner} /> INITIALIZING ENGINE...</>
            ) : isLoggingIn ? (
              <><Loader2 size={18} className={styles.spinner} /> AUTHENTICATING...</>
            ) : identity && password ? (
              <><ShieldCheck size={18} /> INITIALIZE ACCESS <ArrowRight size={18} /></>
            ) : (
              "UPLOAD CORE & ENTER PASSWORD"
            )}

          </button>
        </form>


        <p className={styles.footerText}>
          First time? <span onClick={() => router.push("/register")} className={styles.link}>Initialize Cryptographic Identity</span>
        </p>
      </div>
    </main>
  );
}
