import Sidebar from "@/presentation/components/Sidebar";
import TopBar from "@/presentation/components/TopBar";
import styles from "./dashboard.module.css";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={styles.layout}>
      <Sidebar />
      <TopBar />
      <main className={styles.main}>{children}</main>
    </div>
  );
}