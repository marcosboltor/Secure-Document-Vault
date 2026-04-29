import { User, IUserRepository } from "@/core/domain/user.repository";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiUserRepository implements IUserRepository {
  async getAllUsers(): Promise<User[]> {
    const response = await fetch(`${API_URL}/users`);
    if (!response.ok) throw new Error("Failed to fetch users");
    return response.json();
  }

  async getUserById(id: string): Promise<User | null> {
    const response = await fetch(`${API_URL}/users/${id}`);
    if (response.status === 404) return null;
    if (!response.ok) throw new Error("Failed to fetch user");
    return response.json();
  }
}

export const userRepository = new ApiUserRepository();
