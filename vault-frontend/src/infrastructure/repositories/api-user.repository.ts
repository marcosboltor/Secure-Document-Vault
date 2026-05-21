import { User, IUserRepository } from "@/core/domain/user.repository";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USERS_URL = `${API_BASE}/api/v1/users`;

/**
 * Lee el access_token almacenado en cookies y devuelve
 * los headers de autorización necesarios para las peticiones autenticadas.
 */
function getAuthHeaders(): HeadersInit {
  const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
  const token = match ? match[1] : "";
  return { Authorization: `Bearer ${token}` };
}

export class ApiUserRepository implements IUserRepository {
  async getAllUsers(): Promise<User[]> {
    const response = await fetch(USERS_URL, {
      headers: { ...getAuthHeaders() },
    });
    if (!response.ok) throw new Error("Failed to fetch users");

    const data = await response.json();

    // Mapear UserPublicResponse del backend → User del frontend
    return data.map((u: any) => ({
      id: u.id,
      username: u.username,
      publicKeyBase64: u.public_encryption_key,
      createdAt: u.created_at,
    }));
  }

  async getUserById(id: string): Promise<User | null> {
    const response = await fetch(`${USERS_URL}/${id}`, {
      headers: { ...getAuthHeaders() },
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
