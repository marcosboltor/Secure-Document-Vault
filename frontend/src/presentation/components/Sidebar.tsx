"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, FileText, Upload, Users } from "lucide-react";
import styles from "./Sidebar.module.css";

const links = [
  { href: "/dashboard/files", label: "Files", icon: FileText },
  { href: "/dashboard/upload", label: "Upload", icon: Upload },
  { href: "/dashboard/admin", label: "Admin", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <Shield size={24} />
        <span>VAULT</span>
      </div>
      <nav className={styles.nav}>
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`${styles.link} ${isActive ? styles.active : ""}`}
            >
              <Icon size={18} />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}