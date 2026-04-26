import styles from "./page.module.css";
import { Shield, Lock, Search, User } from "lucide-react";

export default function Home() {
  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <div className="label" style={{ marginBottom: '-16px' }}>Vault Security</div>
        <Shield size={64} strokeWidth={1.5} color="var(--color-tertiary)" />
        <h1 className={styles.title}>Secure Document Vault</h1>
        <p className={styles.description}>
          A high-performance, secure environment for your most sensitive documents.
          Built with Zero-Knowledge encryption.
        </p>
        
        <div className={styles.actions}>
          <button className={`${styles.button} ${styles.primary}`}>
            Get Started
          </button>
          <button className={`${styles.button} ${styles.secondary}`}>
            Documentation
          </button>
        </div>

        {/* Example of bottom bar from the image */}
        <div style={{ 
          marginTop: '2rem', 
          display: 'flex', 
          gap: '1rem', 
          padding: '1rem', 
          background: 'rgba(255,255,255,0.03)',
          borderRadius: 'var(--radius-lg)'
        }}>
          <Lock size={20} color="var(--text-label)" />
          <Search size={20} color="var(--text-label)" />
          <User size={20} color="var(--text-label)" />
        </div>
      </main>
    </div>
  );
}
