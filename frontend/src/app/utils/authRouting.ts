export type AppRole = "manager" | "agent";

export function getDashboardPathForRole(role?: string | null): string {
  if (role === "agent") return "/agent";
  if (role === "manager") return "/manager";
  return "/";
}

export function isPathAllowedForRole(pathname: string, role: AppRole): boolean {
  return role === "agent" ? pathname.startsWith("/agent") : pathname.startsWith("/manager");
}
