import { IAuthRepository, RegisterRequest, RegisterResponse, LoginRequest, TokenResponse } from "@/core/domain/auth.repository";

const API_BASE_URL = "http://localhost:8000/api/v1/users";

export class ApiAuthRepository implements IAuthRepository {
  async registerUser(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to register user");
    }

    return response.json();
  }

  async loginUser(data: LoginRequest): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to login");
    }

    return response.json();
  }
}

export const authRepository = new ApiAuthRepository();
