// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// RequireRole component guarding staff pages and checking JWT role credentials.

import React, { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { fetchCurrentStaff } from '../api/auth';

interface RequireRoleProps {
  allowedRoles: string[];
}

export const RequireRole: React.FC<RequireRoleProps> = ({ allowedRoles }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [authorized, setAuthorized] = useState<boolean>(false);

  useEffect(() => {
    fetchCurrentStaff()
      .then((user) => {
        if (user && allowedRoles.includes(user.role)) {
          setAuthorized(true);
        } else {
          setAuthorized(false);
        }
      })
      .catch(() => {
        setAuthorized(false);
      })
      .finally(() => setLoading(false));
  }, [allowedRoles]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!authorized) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
