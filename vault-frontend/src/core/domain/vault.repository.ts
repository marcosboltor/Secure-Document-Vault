export interface RecipientInfo {
  id: string;
  publicKeyBase64: string; // X25519 public key in base64
}

export interface EncryptionParams {
  file: Uint8Array;
  fileName: string;
  recipients: RecipientInfo[];
  signerId: string;
  signerPrivateKeyBase64: string; // Ed25519 private key in base64
}

export interface DecryptionParams {
  vaultFile: Uint8Array;
  userId: string;
  userPrivateKeyBase64: string; // X25519 private key in base64
  signerPublicKeyBase64: string; // Ed25519 public key in base64
}

export interface IVaultRepository {
  encrypt(params: EncryptionParams): Promise<Uint8Array>;
  decrypt(params: DecryptionParams): Promise<Uint8Array>;
  generateIdentity(): Promise<any>;
  isReady(): Promise<boolean>;
}
