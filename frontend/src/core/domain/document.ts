export interface SecureDocument {
  id: string;
  name: string;
  ownerId: string;
  createdAt: Date;
  status: 'signed' | 'unsigned' | 'encrypted';
}
