import Sidebar from "@/presentation/components/layout/Sidebar";
import TopBar from "@/presentation/components/layout/TopBar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{ flex: 1, marginLeft: "280px", display: "flex", flexDirection: "column" }}>
        <TopBar />
        <main style={{ marginTop: "64px", padding: "2rem", flex: 1 }}>
          {children}
        </main>
      </div>
    </div>
  );
}
