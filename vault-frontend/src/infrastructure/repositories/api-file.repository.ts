import { VaultFile, IFileRepository } from "@/core/domain/file.repository";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("vault_token");
  if (!token) throw new Error("No auth token found. Please log in again.");
  return { Authorization: `Bearer ${token}` };
}

export class ApiFileRepository implements IFileRepository {
  async saveFile(file: VaultFile): Promise<void> {
    // Convert Uint8Array to base64 string for the JSON body
    const base64Content = btoa(String.fromCharCode(...file.encryptedContent));

    const response = await fetch(`${API_URL}/api/v1/files/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        name: file.name,
        recipients: file.recipients,
        encrypted_content: base64Content,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to save file to server");
    }
  }

  async getAllFiles(): Promise<VaultFile[]> {
    const response = await fetch(`${API_URL}/api/v1/files/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch files from server");

    const data = await response.json();

    return data.map((f: any) => ({
      id: f.id,
      name: f.name,
      ownerId: f.owner_id,
      ownerName: f.owner_name,
      recipients: f.recipients ?? [],
      createdAt: f.created_at,
      size: f.size ?? 0,
      encryptedContent: new Uint8Array(0), // lazy-loaded on decrypt
      signerPublicKeyBase64: f.signer_public_key_base64 ?? "",
    }));
  }

  async deleteFile(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/v1/files/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete file");
  }

  async updatePermissions(id: string, recipients: string[]): Promise<void> {
    const response = await fetch(`${API_URL}/api/v1/files/${id}/permissions`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ recipients }),
    });
    if (!response.ok) throw new Error("Failed to update permissions");
  }

  async getFileContent(id: string): Promise<Uint8Array> {
    const response = await fetch(`${API_URL}/api/v1/files/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch file content");

    const data = await response.json();
    if (!data.encrypted_content) throw new Error("No encrypted content in response");

    // Decode base64 to Uint8Array
    const binary = atob(data.encrypted_content);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }
}

export const fileRepository = new ApiFileRepository();
