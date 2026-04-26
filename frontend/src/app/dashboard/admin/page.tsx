"use client";

import styles from "./page.module.css";

export default function AdminPage() {
  const users = [
    { id: "1", name: "John Doe", email: "john@vault.com", role: "admin" },
    { id: "2", name: "Jane Smith", email: "jane@vault.com", role: "user" },
  ];

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Admin</h1>
      </div>
      <div className={styles.table}>
        <div className={styles.tableHeader}>
          <span>User</span>
          <span>Email</span>
          <span>Role</span>
        </div>
        {users.map((user) => (
          <div key={user.id} className={styles.row}>
            <span className={styles.name}>{user.name}</span>
            <span>{user.email}</span>
            <span className={user.role === "admin" ? styles.admin : styles.user}>
              {user.role}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}