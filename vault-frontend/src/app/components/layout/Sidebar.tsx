"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Sidebar.module.css";
import {
  Files,
  Upload as UploadIcon,
  ShieldCheck,
  FileText,
  LogOut,
  Key
} from "lucide-react";
import Image from "next/image";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Files", icon: <Files size={18} />, href: "/files" },
    { name: "Upload", icon: <UploadIcon size={18} />, href: "/upload" },
    { name: "Keys", icon: <Key size={18} />, href: "/keys" },
    { name: "Admin", icon: <ShieldCheck size={18} />, href: "/admin" },
  ];

  return (
    <aside className={styles.sidebar}>
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

      <nav className={styles.nav}>
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`${styles.link} ${pathname === link.href ? styles.active : ""}`}
          >
            {link.icon}
            {link.name}
          </Link>
        ))}
      </nav>

      <div className={styles.bottomNav}>
        <Link href="/" className={styles.link}>
          <LogOut size={18} />
          Logout
        </Link>
      </div>
    </aside>
  );
}
