import { Navigate, Outlet } from "react-router";
import { useAuth } from "../contexts/AuthContext";
import { getDashboardPathForRole, type AppRole } from "../utils/authRouting";

interface RoleRouteProps {
  requiredRole: AppRole;
}

export function RoleRoute({ requiredRole }: RoleRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (user?.role !== requiredRole) {
    return <Navigate to={getDashboardPathForRole(user?.role)} replace />;
  }

  return <Outlet />;
}
