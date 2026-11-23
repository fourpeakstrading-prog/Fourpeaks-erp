const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "erp_token";

export type Role = "owner" | "accountant" | "sales" | "stores" | "hr" | "viewer";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
  created_at: string;
}

export interface CompanySettings {
  company_name: string;
  address: string;
  cr_number: string;
  vat_number: string;
  vat_enabled: boolean;
  currency: string;
  currency_decimals: number;
  financial_year_start_month: number;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: session only */
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* no JSON body */
    }
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  async login(email: string, password: string): Promise<void> {
    const body = new URLSearchParams({ username: email, password });
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body,
    });
    setToken(data.access_token);
  },
  logout(): void {
    setToken(null);
  },
  me: () => request<User>("/auth/me"),
  users: {
    list: () => request<User[]>("/users"),
    create: (data: { name: string; email: string; password: string; role: Role }) =>
      request<User>("/users", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<{ name: string; role: Role; active: boolean; password: string }>) =>
      request<User>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  },
  settings: {
    get: () => request<CompanySettings>("/settings"),
    update: (data: Partial<CompanySettings>) =>
      request<CompanySettings>("/settings", { method: "PATCH", body: JSON.stringify(data) }),
  },
};
