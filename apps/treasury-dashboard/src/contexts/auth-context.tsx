'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, UserRole, RolePermissions } from '../lib/types';
import { apiClient } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: keyof RolePermissions) => boolean;
  getUserRole: () => UserRole | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Role-based permissions mapping
const rolePermissions: Record<UserRole, RolePermissions> = {
  viewer: {
    canApprovePayments: false,
    canViewAllEntities: false,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: false,
    canAccessAuditLogs: false,
  },
  treasury_analyst: {
    canApprovePayments: false,
    canViewAllEntities: false,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: false,
  },
  treasury_manager: {
    canApprovePayments: true,
    canViewAllEntities: true,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: false,
  },
  payment_approver: {
    canApprovePayments: true,
    canViewAllEntities: false,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: false,
  },
  risk_officer: {
    canApprovePayments: false,
    canViewAllEntities: true,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: true,
  },
  cfo: {
    canApprovePayments: true,
    canViewAllEntities: true,
    canManageUsers: true,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: true,
  },
  auditor: {
    canApprovePayments: false,
    canViewAllEntities: true,
    canManageUsers: false,
    canViewAnalytics: true,
    canExportData: true,
    canAccessAuditLogs: true,
  },
};

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (apiClient.isAuthenticated()) {
        try {
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to fetch user data:', error);
          apiClient.clearToken();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await apiClient.login({ username, password });
    setUser(response.user);
  };

  const logout = async () => {
    await apiClient.logout();
    setUser(null);
  };

  const getUserRole = (): UserRole | null => {
    return user ? (user.role as UserRole) : null;
  };

  const hasPermission = (permission: keyof RolePermissions): boolean => {
    const role = getUserRole();
    if (!role) return false;
    return rolePermissions[role][permission];
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    hasPermission,
    getUserRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}