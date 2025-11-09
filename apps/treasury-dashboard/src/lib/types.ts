export interface User {
  user_id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  entity_access: string[];
  permissions: string[];
  is_active: boolean;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiError {
  error: string;
  message: string;
  details?: any;
}

export interface AnalyticsData {
  cash_balance: number;
  working_capital: number;
  liquidity_ratio: number;
  forecast_accuracy: number;
  payments_pending: number;
  risk_score: number;
}

export interface PaymentTransaction {
  id: string;
  amount: number;
  currency: string;
  description: string;
  status: "pending" | "approved" | "rejected" | "completed";
  created_at: string;
  approver?: string;
  entity_id: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ForecastData {
  date: string;
  predicted_balance: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
}

export type UserRole = 
  | "viewer"
  | "treasury_analyst" 
  | "treasury_manager"
  | "payment_approver"
  | "risk_officer"
  | "cfo"
  | "auditor";

export interface RolePermissions {
  canApprovePayments: boolean;
  canViewAllEntities: boolean;
  canManageUsers: boolean;
  canViewAnalytics: boolean;
  canExportData: boolean;
  canAccessAuditLogs: boolean;
}