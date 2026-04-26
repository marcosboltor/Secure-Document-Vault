import Link from "next/link";
import { Shield, FileText, Upload, Users } from "lucide-react";
import styles from "./Sidebar.module.css";

const links = [
  { href: "/files", label: "Files", icon: FileText },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/admin", label: "Admin", icon: Users },
];

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <Shield size={24} />
        <span>VAULT</span>
      </div>
      <nav className={styles.nav}>
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <Link key={link.href} href={link.href} className={styles.link}>
              <Icon size={18} />
              <span>{link.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}