"use client";

import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import styles from "./ThemeToggle.module.css";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    // Sync theme with document attribute on mount
    const root = document.documentElement;
    const currentTheme = root.getAttribute("data-theme") as "dark" | "light" | null;
    
    if (currentTheme && currentTheme !== theme) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTheme(currentTheme);
    }
  }, [theme]);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  };

  return (
    <button className={styles.toggle} onClick={toggleTheme} aria-label="Toggle Theme">
      {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}
