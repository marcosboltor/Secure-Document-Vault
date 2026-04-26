import styles from "./TopBar.module.css";
import { Search, Bell, Settings, Shield } from "lucide-react";

export default function TopBar() {
  return (
    <header className={styles.topbar}>
      <div className={styles.title}>FORTRESS</div>
      
      <div className={styles.searchWrapper}>
        <Search size={16} className={styles.searchIcon} />
        <input 
          type="text" 
          placeholder="Search files, logs, or users..." 
          className={styles.searchInput}
        />
      </div>

      <div className={styles.actions}>
        <Bell size={20} className={styles.actionIcon} />
        <Settings size={20} className={styles.actionIcon} />
        <Shield size={20} className={styles.actionIcon} />
        <div className={styles.profile}>
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Officer" alt="User Profile" />
        </div>
      </div>
    </header>
  );
}
