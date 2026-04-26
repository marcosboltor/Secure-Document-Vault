"use client";

import { useRouter } from "next/navigation";
import { Shield, ArrowRight } from "lucide-react";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();

  const handleLogin = () => {
    router.push("/files");
  };

  return (
    <main className={styles.main}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <Shield size={32} />
        </div>
        <h1 className={styles.title}>VAULT</h1>
        <p className={styles.subtitle}>Secure Document Encryption</p>

        <div className={styles.form}>
          <input type="email" placeholder="Email" className={styles.input} />
          <input type="password" placeholder="Password" className={styles.input} />
          <button className={styles.button} onClick={handleLogin}>
            Access <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </main>
  );
}