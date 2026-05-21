import {
  IVaultRepository,
  EncryptionParams,
  DecryptionParams
} from "@/core/domain/vault.repository";

export class PyodideVaultRepository implements IVaultRepository {
  private worker: Worker | null = null;
  private pendingRequests: Map<string, { resolve: (val: any) => void; reject: (err: Error) => void }> = new Map();
  private initializationPromise: Promise<boolean> | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.initializationPromise = this.init();
    }
  }

  private async init(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      // Initialize worker
      this.worker = new Worker(new URL("../pyodide/vault.worker.ts", import.meta.url));

      this.worker.onmessage = (e) => {
        const { id, type, payload, error } = e.data;

        if (type === "READY") {
          resolve(true);
        } else if (type === "RESULT") {
          const request = this.pendingRequests.get(id);
          if (request) {
            request.resolve(payload);
            this.pendingRequests.delete(id);
          }
        } else if (type === "ERROR") {
          const request = this.pendingRequests.get(id);
          if (request) {
            request.reject(new Error(error));
            this.pendingRequests.delete(id);
          } else {
            reject(new Error(error));
          }
        }
      };

      this.worker.postMessage({ type: "INIT", id: "init" });
    });
  }

  async isReady(): Promise<boolean> {
    if (!this.initializationPromise) return false;
    return this.initializationPromise;
  }

  private sendRequest(type: string, payload: unknown): Promise<any> {
    const id = Math.random().toString(36).substring(7);
    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });
      this.worker?.postMessage({ id, type, payload });
    });
  }

  async encrypt(params: EncryptionParams): Promise<Uint8Array> {
    await this.isReady();
    return this.sendRequest("ENCRYPT", {
      file: params.file,
      fileName: params.fileName,
      recipients: params.recipients,
      signerId: params.signerId,
      signerKeystoreJson: params.signerKeystoreJson,
      password: params.password,
    });
  }

  async decrypt(params: DecryptionParams): Promise<Uint8Array> {
    await this.isReady();
    return this.sendRequest("DECRYPT", {
      vaultFile: params.vaultFile,
      userId: params.userId,
      userKeystoreJson: params.userKeystoreJson,
      password: params.password,
      signerPublicKeyPem: params.signerPublicKeyPem,
    });
  }

  async generateIdentity(): Promise<any> {
    await this.isReady();
    return this.sendRequest("GENERATE_IDENTITY", {});
  }

  async protectKeys(password: string, privXB64: string, privEdB64: string, userId: string): Promise<any> {
    await this.isReady();
    return this.sendRequest("PROTECT_KEYS", { password, privXB64, privEdB64, userId });
  }

  async signChallengeWithKeystore(challenge: string, signKeystoreJson: string, password: string): Promise<string> {
    await this.isReady();
    return this.sendRequest("SIGN_CHALLENGE_KEYSTORE", { challenge, signKeystoreJson, password }) as Promise<string>;
  }
}

// Export a singleton instance
export const vaultRepository = new PyodideVaultRepository();
