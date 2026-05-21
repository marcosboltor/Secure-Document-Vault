import { VaultFile, IFileRepository } from "@/core/domain/file.repository";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FILES_URL = `${API_BASE}/api/v1/files`;

/**
 * Lee el access_token almacenado en cookies y devuelve
 * los headers de autorización necesarios para las peticiones autenticadas.
 */
function getAuthHeaders(): HeadersInit {
  const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
  const token = match ? match[1] : "";
  return { Authorization: `Bearer ${token}` };
}

export class ApiFileRepository implements IFileRepository {
  async saveFile(file: VaultFile): Promise<void> {
    // El backend espera JSON con encrypted_content en base64 (FileUploadRequest)
    // Usamos Array.from en lugar de spread (...) para evitar RangeError
    // en archivos grandes (el spread pasa cada byte como argumento individual
    // y V8 tiene un límite de ~65k argumentos por llamada a función)
    const encryptedBase64 = btoa(
      Array.from(file.encryptedContent, (b) => String.fromCharCode(b)).join("")
    );

    const response = await fetch(FILES_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        name: file.name,
        recipients: file.recipients,
        encrypted_content: encryptedBase64,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save file to server");
    }
  }

  async getAllFiles(): Promise<VaultFile[]> {
    const response = await fetch(FILES_URL, {
      headers: { ...getAuthHeaders() },
    });
    if (!response.ok) throw new Error("Failed to fetch files from server");

    const data = await response.json();

    // Mapear snake_case del backend → camelCase del frontend
    return data.map((f: any) => ({
      id: f.id,
      name: f.name,
      ownerId: f.owner_id,
      ownerName: f.owner_name,
      recipients: f.recipients ?? [],
      createdAt: f.created_at,
      size: f.size ?? 0,
      encryptedContent: new Uint8Array(0), // Content is lazy-loaded
      signerPublicKeyBase64: f.signer_public_key_base64 ?? "",
    }));
  }

  async deleteFile(id: string): Promise<void> {
    const response = await fetch(`${FILES_URL}/${id}`, {
      method: "DELETE",
      headers: { ...getAuthHeaders() },
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to delete file");
    }
  }

  async updatePermissions(id: string, recipients: string[]): Promise<void> {
    const response = await fetch(`${FILES_URL}/${id}/permissions`, {
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
    // El backend devuelve FileDetailResponse con encrypted_content en base64
    const response = await fetch(`${FILES_URL}/${id}`, {
      headers: { ...getAuthHeaders() },
    });
    if (!response.ok) throw new Error("Failed to fetch file content");

    const data = await response.json();
    if (!data.encrypted_content) return new Uint8Array(0);

    // Decodificar base64 → Uint8Array
    const binaryStr = atob(data.encrypted_content);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    return bytes;
  }
}

export const fileRepository = new ApiFileRepository();
