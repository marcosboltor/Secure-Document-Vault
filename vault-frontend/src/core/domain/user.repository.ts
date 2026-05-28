export interface User {
  id: string;
  username: string;
  publicKeyBase64: string; // X25519 public key
  createdAt: string;
}

export interface IUserRepository {
  getAllUsers(): Promise<User[]>;
  getUserById(id: string): Promise<User | null>;
}
