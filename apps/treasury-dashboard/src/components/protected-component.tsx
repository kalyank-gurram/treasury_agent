'use client';

import { useAuth } from '../contexts/auth-context';

interface ProtectedComponentProps {
  children: React.ReactNode;
  roles?: string[];
  permissions?: string[];
  fallback?: React.ReactNode;
  className?: string;
}

export default function ProtectedComponent({ 
  children, 
  roles = [], 
  permissions = [],
  fallback = null,
  className = ''
}: ProtectedComponentProps) {
  const { user, hasPermission } = useAuth();

  if (!user) {
    return fallback;
  }

  // Check role-based access
  if (roles.length > 0 && !roles.includes(user.role)) {
    return fallback;
  }

  // Check permission-based access
  if (permissions.length > 0) {
    const hasRequiredPermission = permissions.some(permission => 
      hasPermission(permission as any)
    );
    if (!hasRequiredPermission) {
      return fallback;
    }
  }

  return (
    <div className={className}>
      {children}
    </div>
  );
}

// Convenience components for specific roles
export function AdminOnly({ children, fallback = null }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedComponent roles={['admin']} fallback={fallback}>
      {children}
    </ProtectedComponent>
  );
}

export function ManagerOnly({ children, fallback = null }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedComponent roles={['admin', 'treasury_manager']} fallback={fallback}>
      {children}
    </ProtectedComponent>
  );
}

export function ApproverOnly({ children, fallback = null }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedComponent roles={['admin', 'treasury_manager', 'payment_approver']} fallback={fallback}>
      {children}
    </ProtectedComponent>
  );
}