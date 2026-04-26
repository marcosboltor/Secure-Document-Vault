export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "user";
}

export interface Document {
  id: string;
  name: string;
  size: number;
  ownerId: string;
  createdAt: string;
  status: "encrypted" | "decrypted";
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}