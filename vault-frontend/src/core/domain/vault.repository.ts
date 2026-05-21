export interface RecipientInfo {
  id: string;
  publicKeyPem: string; // X25519 public key in PEM
}

export interface EncryptionParams {
  file: Uint8Array;
  fileName: string;
  recipients: RecipientInfo[];
  signerId: string;
  signerPrivateKeyPem: string; // Ed25519 private key in PEM
}

export interface DecryptionParams {
  vaultFile: Uint8Array;
  userId: string;
  userPrivateKeyPem: string; // X25519 private key in PEM
  signerPublicKeyPem: string; // Ed25519 public key in PEM
}

export interface IVaultRepository {
  encrypt(params: EncryptionParams): Promise<Uint8Array>;
  decrypt(params: DecryptionParams): Promise<Uint8Array>;
  generateIdentity(): Promise<any>;
  signChallenge(challenge: string, signerPrivateKeyBase64: string): Promise<string>;
  isReady(): Promise<boolean>;
}
