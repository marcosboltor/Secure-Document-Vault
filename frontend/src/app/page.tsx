"use client";

import styles from "./page.module.css";
import { Shield, User, Key, ArrowRight, Fingerprint, Info } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/dashboard/files");
  };
  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <header className={styles.header}>
          <div className={styles.logoIcon}>
            <Shield size={24} color="var(--color-tertiary)" fill="var(--color-tertiary)" fillOpacity={0.2} />
          </div>
          <div>
            <h1 className={styles.title}>FORTRESS</h1>
            <div className={styles.status}>
              <span style={{ 
                width: '6px', 
                height: '6px', 
                backgroundColor: 'var(--color-tertiary)', 
                borderRadius: '50%',
                boxShadow: '0 0 8px var(--color-tertiary)'
              }}></span>
              SYSTEM ONLINE
            </div>
          </div>
        </header>

        <form className={styles.form} onSubmit={handleLogin}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Authorized Email</label>
            <div className={styles.inputWrapper}>
              <User size={16} className={styles.inputIcon} />
              <input 
                type="email" 
                className={styles.input} 
                placeholder="officer@fortress.sys" 
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Secure Password</label>
            <div className={styles.inputWrapper}>
              <Key size={16} className={styles.inputIcon} />
              <input 
                type="password" 
                className={styles.input} 
                placeholder="••••••••••••" 
              />
            </div>
          </div>

          <button type="submit" className={styles.primaryButton}>
            Initialize Access <ArrowRight size={18} />
          </button>
        </form>

        <div className={styles.divider}>
          <div className={styles.dividerLine}></div>
          OR
          <div className={styles.dividerLine}></div>
        </div>

        <button className={styles.secondaryButton}>
          <Fingerprint size={20} /> Biometric Unlock
        </button>

        <div className={styles.footerLink}>
          <Info size={14} /> Request Access
        </div>
      </div>

      <footer className={styles.footerNote}>
        Protocol Level 4 Authorization Required
      </footer>
    </div>
  );
}
