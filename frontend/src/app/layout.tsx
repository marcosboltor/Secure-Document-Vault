"use client";

import { usePathname } from "next/navigation";
import { Outfit } from "next/font/google";
import "./globals.css";
import Sidebar from "@/app/components/layout/Sidebar";
import TopBar from "@/app/components/layout/TopBar";
import styles from "./layout.module.css";

const outfit = Outfit({ 
  subsets: ["latin"], 
  weight: ['300', '400', '500', '600', '700', '800', '900'],
  variable: "--font-outfit" 
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isLogin = pathname === "/";

  return (
    <html lang="en" className={outfit.variable} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const theme = localStorage.getItem('theme') || 'dark';
                  document.documentElement.setAttribute('data-theme', theme);
                } catch (e) {}
              })()
            `,
          }}
        />
      </head>
      <body className={outfit.className}>
        {isLogin ? (
          <main className={styles.loginMain}>{children}</main>
        ) : (
          <div className={styles.appContainer}>
            <Sidebar />
            <div className={styles.contentWrapper}>
              <TopBar />
              <main className={styles.main}>{children}</main>
            </div>
          </div>
        )}
      </body>
    </html>
  );
}