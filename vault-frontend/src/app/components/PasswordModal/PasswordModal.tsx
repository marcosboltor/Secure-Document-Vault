"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Lock, X, Loader2 } from "lucide-react";
import styles from "./PasswordModal.module.css";

interface PasswordModalProps {
  isOpen: boolean;
  title?: string;
  description?: string;
  onSubmit: (password: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export default function PasswordModal({
  isOpen,
  title = "Authentication Required",
  description = "Enter your vault password to unlock your private key for this operation.",
  onSubmit,
  onCancel,
  isLoading = false,
  error = null,
}: PasswordModalProps) {
  const [password, setPassword] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Clear password when modal closes
  useEffect(() => {
    if (!isOpen) {
      setPassword("");
    }
  }, [isOpen]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!password.trim() || isLoading) return;
      onSubmit(password);
      // Password is cleared when modal closes via the useEffect above
    },
    [password, isLoading, onSubmit]
  );

  const handleCancel = useCallback(() => {
    setPassword("");
    onCancel();
  }, [onCancel]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) handleCancel();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, isLoading, handleCancel]);

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={isLoading ? undefined : handleCancel}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button
          className={styles.closeBtn}
          onClick={handleCancel}
          disabled={isLoading}
          type="button"
        >
          <X size={18} />
        </button>

        <div className={styles.iconWrapper}>
          <Lock size={28} />
        </div>

        <h2 className={styles.title}>{title}</h2>
        <p className={styles.description}>{description}</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label htmlFor="vault-password">VAULT PASSWORD</label>
            <input
              ref={inputRef}
              id="vault-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="off"
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className={styles.errorBox}>
              <span>{error}</span>
            </div>
          )}

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.cancelBtn}
              onClick={handleCancel}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.confirmBtn}
              disabled={!password.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className={styles.spinner} /> Unlocking...
                </>
              ) : (
                <>
                  <Lock size={16} /> Confirm
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
