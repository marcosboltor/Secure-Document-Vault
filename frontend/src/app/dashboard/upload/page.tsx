"use client";

import styles from "./upload.module.css";
import { 
  Upload as UploadIcon, 
  ShieldCheck, 
  FileText, 
  X, 
  ChevronDown, 
  Lock, 
  CheckCircle2 
} from "lucide-react";

export default function SecureStaging() {
  const queue = [
    { name: "Q3_Financial_Audit_R...", size: "14.2 MB / 21.8 MB", progress: 65, icon: <FileText size={18} /> },
    { name: "Employee_Database_...", size: "1.2 GB • Pending Allocation", progress: 0, icon: <div style={{ opacity: 0.5 }}><FileText size={18} /></div> },
    { name: "Master_Encryption_K...", size: "4 KB • Pending Allocation", progress: 0, icon: <Lock size={18} /> },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.mainContent}>
        <div className={styles.header}>
          <h1 className={styles.title}>Secure Staging</h1>
          <p className={styles.subtitle}>Prepare, classify, and authorize payloads prior to encrypting and committing them to the institutional vault.</p>
          <div className={styles.e2eeBadge}>
            <ShieldCheck size={14} /> E2E Encryption Active
          </div>
        </div>

        <div className={styles.dropzone}>
          <div className={styles.dropContent}>
            <div className={styles.uploadCircle}>
              <UploadIcon size={32} />
            </div>
            <h2 className={styles.dropTitle}>Drag & Drop Payloads Here</h2>
            <p className={styles.dropSubtitle}>or click to browse local secure storage.</p>
            <div className={styles.dropInfo}>
              <span>Max Size: 50GB</span>
              <span>Supported: All formats</span>
            </div>
          </div>
        </div>

        <div className={styles.parameters}>
          <div className={styles.paramHeader}>
            <div className={styles.paramIcon}><ShieldCheck size={14} /></div>
            TRANSMISSION PARAMETERS
          </div>
          <div className={styles.paramGrid}>
            <div className={styles.paramGroup}>
              <label>Assign File Owner</label>
              <div className={styles.select}>
                System Administrator (Self) <ChevronDown size={16} />
              </div>
            </div>
            <div className={styles.paramGroup}>
              <label>Set Permission Level</label>
              <div className={styles.permissionToggle}>
                <div className={styles.toggleOption}>Public</div>
                <div className={styles.toggleOption}>Private</div>
                <div className={`${styles.toggleOption} ${styles.active}`}>
                  <Lock size={14} /> Encrypted
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside className={styles.sidebar}>
        <div className={styles.queueHeader}>
          <div className={styles.queueTitle}>
            <FileText size={14} /> STAGING QUEUE
          </div>
          <span className={styles.itemCount}>3 Items</span>
        </div>

        <div className={styles.queueList}>
          {queue.map((item, i) => (
            <div key={i} className={styles.queueItem}>
              <div className={styles.itemMain}>
                <div className={styles.itemIcon}>{item.icon}</div>
                <div className={styles.itemInfo}>
                  <div className={styles.itemName}>{item.name}</div>
                  <div className={styles.itemMeta}>{item.size}</div>
                  {item.progress > 0 && (
                    <div className={styles.progressWrapper}>
                      <div className={styles.progressBar} style={{ width: `${item.progress}%` }}></div>
                      <span className={styles.progressText}>{item.progress}%</span>
                    </div>
                  )}
                </div>
                <X size={16} className={styles.closeIcon} />
              </div>
            </div>
          ))}
        </div>

        <div className={styles.queueFooter}>
          <div className={styles.totalPayload}>
            <span>TOTAL PAYLOAD</span>
            <span className={styles.totalValue}>1.22 GB</span>
          </div>
          <button className={styles.transferBtn}>
            <ShieldCheck size={18} /> Commence Secure Transfer
          </button>
        </div>
      </aside>
    </div>
  );
}
