import { VaultFile, IFileRepository } from "@/core/domain/file.repository";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiFileRepository implements IFileRepository {
  async saveFile(file: VaultFile): Promise<void> {
    const formData = new FormData();
    formData.append("id", file.id);
    formData.append("name", file.name);
    formData.append("ownerId", file.ownerId);
    formData.append("ownerName", file.ownerName);
    formData.append("recipients", JSON.stringify(file.recipients));
    formData.append("createdAt", file.createdAt);
    formData.append("signerPublicKeyBase64", file.signerPublicKeyBase64);
    
    // The encrypted content as a blob
    const blob = new Blob([file.encryptedContent], { type: "application/octet-stream" });
    formData.append("file", blob, `${file.name}.vault`);

    const response = await fetch(`${API_URL}/files`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Failed to save file to server");
  }

  async getAllFiles(): Promise<VaultFile[]> {
    const response = await fetch(`${API_URL}/files`);
    if (!response.ok) throw new Error("Failed to fetch files from server");
    
    const data = await response.json();
    
    // For each file, we might need to fetch the content separately or it might be a link
    // For simplicity, we assume the API returns metadata and we fetch content on demand
    return data.map((f: any) => ({
      ...f,
      encryptedContent: new Uint8Array(0) // Content is lazy-loaded
    }));
  }

  async deleteFile(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/files/${id}`, {
      method: "DELETE"
    });
    if (!response.ok) throw new Error("Failed to delete file");
  }

  async updatePermissions(id: string, recipients: string[]): Promise<void> {
    const response = await fetch(`${API_URL}/files/${id}/permissions`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipients })
    });
    if (!response.ok) throw new Error("Failed to update permissions");
  }

  async getFileContent(id: string): Promise<Uint8Array> {
    const response = await fetch(`${API_URL}/files/${id}/content`);
    if (!response.ok) throw new Error("Failed to fetch file content");
    const buffer = await response.arrayBuffer();
    return new Uint8Array(buffer);
  }
}

export const fileRepository = new ApiFileRepository();
