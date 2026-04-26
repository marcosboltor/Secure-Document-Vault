"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Shield, ArrowRight } from "lucide-react";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      router.push("/dashboard/files");
    }, 500);
  };

  return (
    <main className={styles.main}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <Shield size={32} />
        </div>
        <h1 className={styles.title}>VAULT</h1>
        <p className={styles.subtitle}>Secure Document Encryption</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            className={styles.input}
            required
          />
          <input
            type="password"
            placeholder="Password"
            className={styles.input}
            required
          />
          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? "Loading..." : "Access"}
            <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </main>
  );
}