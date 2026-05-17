import { User, IUserRepository } from "@/core/domain/user.repository";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("vault_token") : null;
  if (!token) throw new Error("No auth token found. Please log in again.");
  return { Authorization: `Bearer ${token}` };
}

export class ApiUserRepository implements IUserRepository {
  async getAllUsers(): Promise<User[]> {
    const response = await fetch(`${API_URL}/api/v1/users/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch users");

    const data = await response.json();
    return data.map((u: any) => ({
      id: u.id,
      username: u.username,
      publicKeyBase64: u.public_encryption_key,
      createdAt: u.created_at,
    }));
  }

  async getUserById(id: string): Promise<User | null> {
    const response = await fetch(`${API_URL}/api/v1/users/${id}`, {
      headers: getAuthHeaders(),
    });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error("Failed to fetch user");

    const u = await response.json();
    return {
      id: u.id,
      username: u.username,
      publicKeyBase64: u.public_encryption_key,
      createdAt: u.created_at,
    };
  }
}

export const userRepository = new ApiUserRepository();
