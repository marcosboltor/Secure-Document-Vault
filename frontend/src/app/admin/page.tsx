"use client";

import styles from "./page.module.css";
import { UserPlus, Shield, Users, ShieldAlert, ChevronDown } from "lucide-react";

export default function AdminPage() {
  const stats = [
    { label: "Total Active Personnel", value: "142", icon: <Users /> },
    { label: "System Administrators", value: "12", icon: <Shield /> },
    { label: "Pending Access Reviews", value: "7", icon: <ShieldAlert /> },
  ];

  const users = [
    { name: "Eleanor Vance", email: "e.vance@fortress.sys", role: "SYSTEM ADMIN", files: "1,024 Files", ownership: "Primary Owner" },
    { name: "Marcus Chen", email: "m.chen@external.org", role: "STANDARD USER", files: "42 Files", ownership: "Read-Only Access" },
    { name: "Sarah Jenkins", email: "s.jenkins@fortress.sys", role: "STANDARD USER", files: "128 Files", ownership: "Contributor Access" },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.headerSection}>
        <div>
          <h1 className={styles.title}>System Administration</h1>
          <p className={styles.subtitle}>Manage user access, roles, and file ownership across the institutional vault.</p>
        </div>
        <button className={styles.primaryBtn}>
          <UserPlus size={16} /> Invite Personnel
        </button>
      </div>

      <div className={styles.statsGrid}>
        {stats.map((stat, i) => (
          <div key={i} className={styles.statCard}>
            <div>
              <div className={styles.statLabel}>{stat.label}</div>
              <div className={styles.statValue}>{stat.value}</div>
            </div>
            <div className={styles.statIcon}>{stat.icon}</div>
          </div>
        ))}
      </div>

      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Access Roster</h2>
        <div className={styles.filter}>
          <Users size={16} /> All Roles <ChevronDown size={14} />
        </div>
      </div>

      <div className={styles.roster}>
        {users.map((user, i) => (
          <div key={i} className={styles.userRow}>
            <div className={styles.userInfo}>
              <div className={styles.userAvatar}>
                <Users size={18} />
              </div>
              <div>
                <div className={styles.userName}>{user.name}</div>
                <div className={styles.userEmail}>{user.email}</div>
              </div>
            </div>
            <div className={styles.userRole}>
              <span className={user.role === "SYSTEM ADMIN" ? styles.adminBadge : styles.userBadge}>
                {user.role}
              </span>
            </div>
            <div className={styles.userFiles}>
              <div className={styles.fileCount}>{user.files}</div>
              <div className={styles.ownership}>{user.ownership}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}