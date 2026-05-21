"use client";

import styles from "./TopBar.module.css";
import { Search, Bell, Settings } from "lucide-react";
import ThemeToggle from "@/app/components/theme/ThemeToggle";

export default function TopBar() {
  return (
    <header className={styles.topbar}>
      <div style={{ width: "100%" }}></div>
      <ThemeToggle />
    </header>
  );
}
