import { User, IUserRepository } from "@/core/domain/user.repository";

export class MockUserRepository implements IUserRepository {
  private users: User[] = [
    { 
      id: "admin-1", 
      name: "Eleanor Vance", 
      email: "e.vance@fortress.sys", 
      publicKeyBase64: "47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=" 
    },
    { 
      id: "user-1", 
      name: "Marcus Chen", 
      email: "m.chen@external.org", 
      publicKeyBase64: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" 
    },
    { 
      id: "user-2", 
      name: "Sarah Jenkins", 
      email: "s.jenkins@fortress.sys", 
      publicKeyBase64: "SGVsbG8gd29ybGQhISEhISEhISEhISEhISEhISEhISE=" 
    },
    { 
      id: "user-3", 
      name: "Arthur Dent", 
      email: "a.dent@galaxy.sys", 
      publicKeyBase64: "TGlmZSwgdGhlIFVuaXZlcnNlLCBhbmQgRXZlcnl0aGluZw==" 
    },
  ];

  async getAllUsers(): Promise<User[]> {
    // Simulate network delay
    return new Promise((resolve) => {
      setTimeout(() => resolve(this.users), 500);
    });
  }

  async getUserById(id: string): Promise<User | null> {
    return this.users.find(u => u.id === id) || null;
  }
}

export const userRepository = new MockUserRepository();
