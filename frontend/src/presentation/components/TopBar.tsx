"use client";

import { useState } from "react";
import { Search, Bell, Sun, Moon } from "lucide-react";
import styles from "./TopBar.module.css";

function getInitialTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("theme") as "dark" | "light" | null;
  return stored || "dark";
}

export default function TopBar() {
  const [theme, setTheme] = useState(getInitialTheme);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };

  return (
    <header className={styles.header}>
      <div className={styles.search}>
        <Search size={18} />
        <input type="text" placeholder="Search..." />
      </div>
      <div className={styles.actions}>
        <button className={styles.iconBtn}>
          <Bell size={18} />
        </button>
        <button className={styles.iconBtn} onClick={toggleTheme}>
          {theme === "dark" ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      </div>
    </header>
  );
}