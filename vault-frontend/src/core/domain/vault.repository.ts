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
  password: string;           // Password to unlock signing key
}

export interface DecryptionParams {
  vaultFile: Uint8Array;
  userId: string;
  userKeystoreJson: string;    // Encrypted encryption keystore JSON
  password: string;            // Password to unlock encryption key
  signerPublicKeyPem: string;  // Ed25519 public key in PEM
}

export interface IdentityKeys {
  encryption: {
    private: string;   // Raw base64
    public: string;    // Raw base64
    publicPem: string; // PEM format
  };
  signing: {
    private: string;
    public: string;
    publicPem: string;
  };
}

export interface IVaultRepository {
  // Core crypto operations (password-based, key never leaves Pyodide)
  encrypt(params: EncryptionParams): Promise<Uint8Array>;
  decrypt(params: DecryptionParams): Promise<Uint8Array>;

  // Identity generation (raw keys — used only during registration, then protected)
  generateIdentity(): Promise<IdentityKeys>;

  // Keystore protection (takes raw keys + password → returns JSON string of encrypted keystores)
  protectKeys(
    password: string,
    privXB64: string,
    privEdB64: string,
    userId: string
  ): Promise<string>;

  // Challenge signing via keystore (key never leaves Pyodide scope)
  signChallengeWithKeystore(
    challenge: string,
    signKeystoreJson: string,
    password: string
  ): Promise<string>;

  // Engine readiness
  isReady(): Promise<boolean>;
}
