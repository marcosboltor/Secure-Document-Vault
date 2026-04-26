"use client";

import { Search, Bell } from "lucide-react";
import styles from "./SearchBar.module.css";

export default function SearchBar() {
  return (
    <div className={styles.bar}>
      <div className={styles.search}>
        <Search size={18} />
        <input type="text" placeholder="Search..." />
      </div>
      <button className={styles.icon}>
        <Bell size={18} />
      </button>
    </div>
  );
}