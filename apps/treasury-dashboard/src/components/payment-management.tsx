'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/auth-context';
import { PaymentTransaction } from '../lib/types';
import { apiClient } from '../lib/api';
import { formatCurrency, formatDate } from '../lib/utils';

export default function PaymentManagement() {
  const [payments, setPayments] = useState<PaymentTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const { hasPermission } = useAuth();

  const canApprovePayments = hasPermission('canApprovePayments');

  useEffect(() => {
    const fetchPayments = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.getPayments();
        setPayments(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch payments');
        // Mock data for demo purposes
        setPayments(generateMockPayments());
      } finally {
        setIsLoading(false);
      }
    };

    fetchPayments();
  }, []);

  const handleApprovePayment = async (paymentId: string) => {
    try {
      await apiClient.approvePayment(paymentId);
      setPayments(prev => prev.map(p => 
        p.id === paymentId 
          ? { ...p, status: 'approved' as const }
          : p
      ));
    } catch (err: any) {
      alert('Failed to approve payment: ' + err.message);
    }
  };

  const handleRejectPayment = async (paymentId: string) => {
    const reason = prompt('Please provide a reason for rejection:');
    if (!reason) return;

    try {
      await apiClient.rejectPayment(paymentId, reason);
      setPayments(prev => prev.map(p => 
        p.id === paymentId 
          ? { ...p, status: 'rejected' as const }
          : p
      ));
    } catch (err: any) {
      alert('Failed to reject payment: ' + err.message);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'Approved' },
      rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'Rejected' },
      completed: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Completed' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="bg-gray-200 h-8 rounded mb-4"></div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-gray-200 h-16 rounded mb-2"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h2 className="text-xl font-semibold text-gray-900">Payment Management</h2>
          <p className="mt-2 text-sm text-gray-700">
            Review and manage payment transactions requiring approval.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul role="list" className="divide-y divide-gray-200">
          {payments.map((payment) => (
            <li key={payment.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {payment.description}
                        </p>
                        <div className="ml-2 flex-shrink-0">
                          {getStatusBadge(payment.status)}
                        </div>
                      </div>
                      <div className="mt-2 flex">
                        <div className="flex items-center text-sm text-gray-500">
                          <p>
                            {formatCurrency(payment.amount, payment.currency)} • 
                            Entity: {payment.entity_id} • 
                            Created: {formatDate(payment.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {payment.status === 'pending' && canApprovePayments && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleApprovePayment(payment.id)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleRejectPayment(payment.id)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {!canApprovePayments && (
        <div className="rounded-md bg-blue-50 p-4">
          <div className="text-sm text-blue-800">
            Your role does not have permission to approve payments. You can view payment status only.
          </div>
        </div>
      )}
    </div>
  );
}

// Helper function to generate mock payment data
function generateMockPayments(): PaymentTransaction[] {
  const descriptions = [
    'Vendor Payment - Office Supplies',
    'Salary Payment - Engineering Team',
    'Utility Bill - Electricity',
    'Software License - Analytics Platform',
    'Insurance Premium - Commercial Property',
    'Marketing Campaign - Q4 Initiative'
  ];

  return descriptions.map((desc, index) => ({
    id: `payment-${index + 1}`,
    amount: Math.floor(Math.random() * 50000) + 1000,
    currency: 'USD',
    description: desc,
    status: ['pending', 'approved', 'rejected'][Math.floor(Math.random() * 3)] as any,
    created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    entity_id: `ENT-0${(index % 3) + 1}`,
    approver: index % 2 === 0 ? 'manager' : undefined
  }));
}