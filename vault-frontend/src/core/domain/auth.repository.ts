export interface RegisterRequest {
  email: string;
  username: string;
  public_encryption_key: string;
  public_signing_key: string;
}

export interface RegisterResponse {
  id: string;
  username: string;
  public_encryption_key: string;
  created_at: string;
}

export interface LoginRequest {
  user_id: string;
  challenge: string;
  signature: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface IAuthRepository {
  registerUser(data: RegisterRequest): Promise<RegisterResponse>;
  loginUser(data: LoginRequest): Promise<TokenResponse>;
}
