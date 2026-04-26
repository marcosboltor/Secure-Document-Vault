import styles from "./page.module.css"; import { Shield } from "lucide-react";

export default function Home() {
  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <Shield size={64} strokeWidth={1.5} />
        <h1 className={styles.title}>Secure Document Vault</h1>
        <p className={styles.description}>
          A high-performance, secure environment for your most sensitive documents.
        </p>
        <div className={styles.actions}>
          <a href="#" className={`${styles.button} ${styles.primary}`}>
            Get Started
          </a>
          <a href="#" className={`${styles.button} ${styles.secondary}`}>
            Documentation
          </a>
        </div>
      </main>
    </div>
  );
}
