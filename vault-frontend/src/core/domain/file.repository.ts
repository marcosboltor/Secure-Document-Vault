export interface VaultFile {
  id: string;
  name: string;
  ownerId: string;
  ownerName: string;
  recipients: string[]; // List of user IDs
  createdAt: string;
  size: number;
  encryptedContent: Uint8Array;
  signerPublicKeyBase64: string;
}

export interface IFileRepository {
  saveFile(file: VaultFile): Promise<void>;
  getAllFiles(): Promise<VaultFile[]>;
  deleteFile(id: string): Promise<void>;
  updatePermissions(id: string, recipients: string[]): Promise<void>;
  getFileContent(id: string): Promise<Uint8Array>;
}
