'use client';

import { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { formatCurrency, formatPercentage } from '../lib/utils';
import { apiClient } from '../lib/api';
import { AnalyticsData, ForecastData } from '../lib/types';

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}

function MetricCard({ title, value, change, changeType = 'neutral', icon }: MetricCardProps) {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }[changeType];

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {icon}
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">{value}</div>
                {change && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${changeColor}`}>
                    {change}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [forecastData, setForecastData] = useState<ForecastData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [analytics, forecast] = await Promise.all([
          apiClient.getAnalytics(),
          apiClient.getForecast(30)
        ]);
        setAnalyticsData(analytics);
        setForecastData(forecast);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analytics data');
        // Mock data for demo purposes
        setAnalyticsData({
          cash_balance: 15678900.50,
          working_capital: 8450600.25,
          liquidity_ratio: 2.34,
          forecast_accuracy: 92.5,
          payments_pending: 23,
          risk_score: 15.2
        });
        setForecastData(generateMockForecastData());
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-200 h-64 rounded-lg"></div>
          <div className="bg-gray-200 h-64 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error || 'No analytics data available'}</div>
        <button 
          onClick={() => window.location.reload()} 
          className="text-blue-600 hover:text-blue-800"
        >
          Retry
        </button>
      </div>
    );
  }

  const riskData = [
    { name: 'Low Risk', value: 65, fill: '#10B981' },
    { name: 'Medium Risk', value: 25, fill: '#F59E0B' },
    { name: 'High Risk', value: 10, fill: '#EF4444' }
  ];

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Key Financial Metrics</h2>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            title="Cash Balance"
            value={formatCurrency(analyticsData.cash_balance)}
            change="+2.4%"
            changeType="positive"
            icon={
              <div className="p-2 bg-green-100 rounded-md">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            }
          />
          <MetricCard
            title="Working Capital"
            value={formatCurrency(analyticsData.working_capital)}
            change="+5.1%"
            changeType="positive"
            icon={
              <div className="p-2 bg-blue-100 rounded-md">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            }
          />
          <MetricCard
            title="Liquidity Ratio"
            value={analyticsData.liquidity_ratio.toFixed(2)}
            change="-0.1"
            changeType="negative"
            icon={
              <div className="p-2 bg-yellow-100 rounded-md">
                <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            }
          />
          <MetricCard
            title="Forecast Accuracy"
            value={formatPercentage(analyticsData.forecast_accuracy)}
            change="+1.2%"
            changeType="positive"
            icon={
              <div className="p-2 bg-purple-100 rounded-md">
                <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 13v-1a4 4 0 014-4 4 4 0 014 4v1m0 0a4 4 0 01-8 0m8 0v6a2 2 0 01-2 2H6a2 2 0 01-2-2v-6a2 2 0 012-2h8a2 2 0 012 2z" />
                </svg>
              </div>
            }
          />
          <MetricCard
            title="Pending Payments"
            value={analyticsData.payments_pending.toString()}
            change="-3"
            changeType="positive"
            icon={
              <div className="p-2 bg-red-100 rounded-md">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            }
          />
          <MetricCard
            title="Risk Score"
            value={`${analyticsData.risk_score}%`}
            change="-2.1%"
            changeType="positive"
            icon={
              <div className="p-2 bg-indigo-100 rounded-md">
                <svg className="h-6 w-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            }
          />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cash Flow Forecast */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">30-Day Cash Flow Forecast</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={(value) => formatCurrency(value, 'USD').slice(0, -3) + 'K'} />
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
              <Legend />
              <Area
                type="monotone"
                dataKey="predicted_balance"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.3}
                name="Predicted Balance"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// Helper function to generate mock forecast data
function generateMockForecastData(): ForecastData[] {
  const data: ForecastData[] = [];
  const startDate = new Date();
  const baseBalance = 15678900;
  
  for (let i = 0; i < 30; i++) {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);
    
    const variation = Math.sin(i / 5) * 500000 + (Math.random() - 0.5) * 200000;
    const predicted_balance = baseBalance + variation;
    
    data.push({
      date: date.toISOString().split('T')[0],
      predicted_balance,
      confidence_interval: {
        lower: predicted_balance * 0.95,
        upper: predicted_balance * 1.05
      }
    });
  }
  
  return data;
}