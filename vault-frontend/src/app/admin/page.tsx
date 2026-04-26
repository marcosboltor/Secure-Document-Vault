"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { UserPlus, Shield, Users, ShieldAlert, ChevronDown, Loader2 } from "lucide-react";
import { userRepository } from "@/infrastructure/repositories/api-user.repository";
import { User } from "@/core/domain/user.repository";

export default function AdminPage() {
  const [personnel, setPersonnel] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPersonnel();
  }, []);

  const loadPersonnel = async () => {
    setIsLoading(true);
    try {
      const users = await userRepository.getAllUsers();
      setPersonnel(users);
    } catch (error) {
      console.error("Failed to load personnel:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const stats = [
    { label: "Total Active Personnel", value: personnel.length.toString(), icon: <Users /> },
    { label: "System Administrators", value: "1", icon: <Shield /> },
    { label: "Pending Access Reviews", value: "0", icon: <ShieldAlert /> },
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
        {isLoading ? (
          <div className={styles.loadingBox}>
            <Loader2 className={styles.spinner} size={24} />
            <span>Fetching personnel data...</span>
          </div>
        ) : personnel.length === 0 ? (
          <div className={styles.emptyRoster}>No personnel registered in the system.</div>
        ) : (
          personnel.map((user) => (
            <div key={user.id} className={styles.userRow}>
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
                <span className={styles.userBadge}>
                  STANDARD USER
                </span>
              </div>
              <div className={styles.userFiles}>
                <div className={styles.fileCount}>Stored Core</div>
                <div className={styles.ownership}>
                  ID: {user.id.substring(0, 8)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}