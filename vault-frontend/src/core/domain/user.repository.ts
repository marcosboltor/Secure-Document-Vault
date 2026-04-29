export interface User {
  id: string;
  name: string;
  email: string;
  publicKeyBase64: string; // X25519 public key
}

export interface IUserRepository {
  getAllUsers(): Promise<User[]>;
  getUserById(id: string): Promise<User | null>;
}
