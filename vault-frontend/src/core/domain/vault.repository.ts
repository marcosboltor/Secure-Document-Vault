export interface RecipientInfo {
  id: string;
  publicKeyPem: string; // X25519 public key in PEM
}

export interface EncryptionParams {
  file: Uint8Array;
  fileName: string;
  recipients: RecipientInfo[];
  signerId: string;
  signerKeystoreJson: string; // Encrypted signing keystore JSON
  password: string;           // Password to unlock the keystore
}

export interface DecryptionParams {
  vaultFile: Uint8Array;
  userId: string;
  userKeystoreJson: string;   // Encrypted encryption keystore JSON
  password: string;           // Password to unlock the keystore
  signerPublicKeyPem: string; // Ed25519 public key in PEM
}

export interface IVaultRepository {
  encrypt(params: EncryptionParams): Promise<Uint8Array>;
  decrypt(params: DecryptionParams): Promise<Uint8Array>;
  generateIdentity(): Promise<any>;
  protectKeys(password: string, privXB64: string, privEdB64: string, userId: string): Promise<any>;
  signChallengeWithKeystore(challenge: string, signKeystoreJson: string, password: string): Promise<string>;
  isReady(): Promise<boolean>;
}
