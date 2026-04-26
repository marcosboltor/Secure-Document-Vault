import { Users } from "lucide-react";
import styles from "./page.module.css";

export default function AdminPage() {
  const users = [
    { id: "1", name: "John Doe", email: "john@vault.com", role: "admin" },
    { id: "2", name: "Jane Smith", email: "jane@vault.com", role: "user" },
  ];

  return (
    <div>
      <h1 className={styles.title}>Admin</h1>
      <div className={styles.table}>
        <div className={styles.header}>
          <span>User</span>
          <span>Email</span>
          <span>Role</span>
        </div>
        {users.map((u) => (
          <div key={u.id} className={styles.row}>
            <span className={styles.name}>
              <Users size={16} /> {u.name}
            </span>
            <span>{u.email}</span>
            <span className={u.role === "admin" ? styles.admin : styles.user}>{u.role}</span>
          </div>
        ))}
      </div>
    </div>
  );
}