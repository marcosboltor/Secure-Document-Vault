import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/presentation/components/Sidebar";
import SearchBar from "@/presentation/components/SearchBar";
import styles from "./layout.module.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vault",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className={styles.container}>
          <Sidebar />
          <SearchBar />
          <main className={styles.main}>{children}</main>
        </div>
      </body>
    </html>
  );
}