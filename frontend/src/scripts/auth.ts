const AUTH_KEY = "unserious-auth";

export interface AuthUser {
  name: string;
  email: string;
  picture: string;
  token: string;
}

export function getUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setUser(user: AuthUser): void {
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

export function clearUser(): void {
  localStorage.removeItem(AUTH_KEY);
}

export function requireAuth(): void {
  const user = getUser();
  if (user) {
    console.log("[auth] Logged-in user:", user);
  } else {
    console.log("[auth] No user found, redirecting to /login");
    window.location.href = "/login";
  }
}

/** Decode the payload of a JWT without verifying signature (client-side only). */
export function decodeJwtPayload(token: string): Record<string, unknown> {
  const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(base64));
}
