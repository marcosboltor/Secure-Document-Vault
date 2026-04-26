"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Fingerprint, Lock } from "lucide-react";
import Image from "next/image";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/files");
  };

  return (
    <main className={styles.container}>
      <div className={styles.card}>
        <div className={styles.logoSection}>
          <div className={styles.logoWrapper}>
            <Image
              src="/logo.png"
              alt="Vault Logo"
              width={80}
              height={80}
              className={styles.logoImg}
              priority
              quality={100}
            />
          </div>
          <h1 className={styles.title}>VAULT</h1>
          <div className={styles.badge}>Level 4 Authorization</div>
        </div>

        <form className={styles.form} onSubmit={handleLogin}>
          <div className={styles.inputGroup}>
            <label>Authorized Identifier</label>
            <input type="email" placeholder="officer@fortress.sys" className={styles.input} />
          </div>
          <div className={styles.inputGroup}>
            <label>Secure Protocol Key</label>
            <input type="password" placeholder="••••••••••••" className={styles.input} />
          </div>

          <button type="submit" className={styles.primaryButton}>
            Initialize Access <ArrowRight size={18} />
          </button>
        </form>

        <div className={styles.divider}>
          <span>OR SECURE WITH</span>
        </div>

        <div className={styles.secondaryActions}>
          <button className={styles.biometricButton} disabled title="Coming soon">
            <Fingerprint size={20} /> Biometric
          </button>
          <button className={styles.biometricButton} disabled title="Coming soon">
            <Lock size={20} /> Hardware Key
          </button>
        </div>
      </div>
    </main>
  );
}