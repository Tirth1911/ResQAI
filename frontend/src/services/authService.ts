import { API_BASE_URL } from '@/lib/constants';
import { User, AuthTokenResponse, RoleMeta, UserRole } from '@/types';

class AuthService {
  private baseUrl = `${API_BASE_URL}/auth`;

  async login(email: string, password: string): Promise<AuthTokenResponse> {
    const res = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Login failed (${res.status})`);
    }
    return res.json();
  }

  async quickLogin(role: UserRole): Promise<AuthTokenResponse> {
    const res = await fetch(`${this.baseUrl}/quick-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Quick login failed (${res.status})`);
    }
    return res.json();
  }

  async getMe(token: string): Promise<User> {
    const res = await fetch(`${this.baseUrl}/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch current user profile (${res.status})`);
    }
    return res.json();
  }

  async getRoles(): Promise<{ roles: RoleMeta[] }> {
    const res = await fetch(`${this.baseUrl}/roles`, {
      cache: 'no-store',
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch roles (${res.status})`);
    }
    return res.json();
  }

  async seedUsers(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/seed`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error(`Failed to seed users (${res.status})`);
    }
    return res.json();
  }
}

export const authService = new AuthService();
