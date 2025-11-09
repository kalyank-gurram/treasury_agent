'use client';

import { useAuth } from '../../contexts/auth-context';
import AnalyticsDashboard from '../../components/analytics-dashboard';
import ProtectedComponent, { AdminOnly, ManagerOnly, ApproverOnly } from '../../components/protected-component';

export default function DashboardPage() {
  const { user } = useAuth();

  const quickStats = [
    { name: 'Available Cash', value: '$2.4M', change: '+12%', changeType: 'increase' },
    { name: 'Pending Payments', value: '23', change: '-4%', changeType: 'decrease' },
    { name: 'Monthly Volume', value: '$18.7M', change: '+8%', changeType: 'increase' },
    { name: 'Risk Score', value: 'Low', change: 'Stable', changeType: 'neutral' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name}
        </h1>
        <p className="text-gray-600">
          Treasury Management Dashboard - {new Date().toLocaleDateString()}
        </p>
      </div>

      {/* Quick Stats - Available to all users */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                    <dd className="text-lg font-medium text-gray-900">{stat.value}</dd>
                  </dl>
                </div>
              </div>
              <div className="mt-2">
                <span className={`inline-flex items-baseline px-2.5 py-0.5 rounded-full text-sm font-medium ${
                  stat.changeType === 'increase' ? 'bg-green-100 text-green-800' :
                  stat.changeType === 'decrease' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {stat.change}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Role-based Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Viewer Actions - All users */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full text-left px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100">
                View Cash Position
              </button>
              <button className="w-full text-left px-3 py-2 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100">
                Check Account Balances
              </button>
              <button className="w-full text-left px-3 py-2 text-sm bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100">
                Generate Reports
              </button>
            </div>
          </div>
        </div>

        {/* Approver Actions */}
        <ApproverOnly>
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Approvals</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-md">
                  <span className="text-sm text-yellow-800">Pending Approvals</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    5 items
                  </span>
                </div>
                <button className="w-full text-left px-3 py-2 text-sm bg-orange-50 text-orange-700 rounded-md hover:bg-orange-100">
                  Review High-Value Payments
                </button>
                <button className="w-full text-left px-3 py-2 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100">
                  Urgent Approvals Required
                </button>
              </div>
            </div>
          </div>
        </ApproverOnly>

        {/* Manager/Admin Actions */}
        <ManagerOnly>
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Management</h3>
              <div className="space-y-3">
                <button className="w-full text-left px-3 py-2 text-sm bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100">
                  Liquidity Management
                </button>
                <button className="w-full text-left px-3 py-2 text-sm bg-teal-50 text-teal-700 rounded-md hover:bg-teal-100">
                  Risk Assessment
                </button>
                <AdminOnly>
                  <button className="w-full text-left px-3 py-2 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100">
                    System Configuration
                  </button>
                </AdminOnly>
              </div>
            </div>
          </div>
        </ManagerOnly>
      </div>

      {/* Analytics Dashboard - Admin Only */}
      <AdminOnly fallback={
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Advanced Analytics</h3>
          <p className="text-sm text-gray-500">Contact your administrator for access to detailed analytics and forecasting tools.</p>
        </div>
      }>
        <AnalyticsDashboard />
      </AdminOnly>

      {/* Recent Activity - All users */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="flow-root">
            <ul role="list" className="-mb-8">
              {[
                { id: 1, type: 'payment', content: 'Payment of $50,000 approved', time: '1 hour ago' },
                { id: 2, type: 'forecast', content: 'Weekly cash flow forecast updated', time: '3 hours ago' },
                { id: 3, type: 'alert', content: 'Low balance alert for Account #1234', time: '5 hours ago' },
                { id: 4, type: 'report', content: 'Monthly treasury report generated', time: '1 day ago' },
              ].map((activity, activityIdx, activities) => (
                <li key={activity.id}>
                  <div className="relative pb-8">
                    {activityIdx !== activities.length - 1 ? (
                      <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
                        <div className="h-2 w-2 rounded-full bg-gray-500" />
                      </div>
                      <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                        <div>
                          <p className="text-sm text-gray-900">{activity.content}</p>
                        </div>
                        <div className="whitespace-nowrap text-right text-sm text-gray-500">
                          <time>{activity.time}</time>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}