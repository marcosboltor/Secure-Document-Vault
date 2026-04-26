"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Sidebar.module.css";
import { 
  Shield, 
  Files, 
  Upload as UploadIcon, 
  ShieldCheck, 
  FileText, 
  LogOut 
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "My Files", icon: <Files size={18} />, href: "/dashboard/files" },
    { name: "Upload", icon: <UploadIcon size={18} />, href: "/dashboard/upload" },
    { name: "Security Admin", icon: <ShieldCheck size={18} />, href: "/dashboard/admin" },
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoSection}>
        <div className={styles.logoIcon}>
          <Shield size={20} color="var(--color-tertiary)" />
        </div>
        <div className={styles.logoText}>
          <h2>VAULT ACCESS</h2>
          <p>Level 4 Authorization</p>
        </div>
      </div>

      <nav className={styles.nav}>
        {links.map((link) => (
          <Link 
            key={link.href} 
            href={link.href}
            className={`${styles.navLink} ${pathname === link.href ? styles.active : ""}`}
          >
            {link.icon}
            {link.name}
          </Link>
        ))}
      </nav>

      <div className={styles.bottomNav}>
        <Link href="/dashboard/audit" className={styles.navLink}>
          <FileText size={18} />
          Audit Logs
        </Link>
        <Link href="/login" className={styles.navLink}>
          <LogOut size={18} />
          Logout
        </Link>
      </div>
    </aside>
  );
}
