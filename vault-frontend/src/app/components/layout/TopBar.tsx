"use client";

import styles from "./TopBar.module.css";
import { Search, Bell, Settings } from "lucide-react";
import ThemeToggle from "@/app/components/theme/ThemeToggle";

export default function TopBar() {
  return (
    <header className={styles.topbar}>
      <div className={styles.search}>
        <Search size={18} />
        <input type="text" placeholder="Search archives..." />
      </div>

      <div className={styles.actions}>
        <ThemeToggle />
        <div className={styles.divider}></div>
        <Bell size={20} className={styles.actionIcon} />
        <Settings size={20} className={styles.actionIcon} />
        <div className={styles.profile}>
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Officer" alt="User" />
        </div>
      </div>
    </header>
  );
}
