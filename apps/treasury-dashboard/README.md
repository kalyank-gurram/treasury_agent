# Treasury Agent Frontend

A modern Next.js frontend for the Treasury Agent application, providing a comprehensive dashboard for treasury management operations.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication with secure cookie storage
- Role-based access control (CFO, Treasury Manager, Payment Approver, Treasury Analyst, Auditor, Viewer)
- Protected routes and components
- Automatic token refresh and logout on expiry

### 📊 Dashboard & Analytics
- Real-time treasury KPIs and metrics
- Interactive charts and visualizations using Recharts
- Cash flow analysis and forecasting
- Working capital management metrics
- Role-based dashboard customization

### 💳 Payment Management
- Payment transaction listing and filtering
- Approval workflow with role-based permissions
- Payment status tracking and updates
- Bulk operations and export functionality

### 🤖 AI Assistant
- Conversational AI interface for treasury queries
- Context-aware responses with treasury domain knowledge
- Chat history and message persistence
- Suggested questions for common use cases

### 🎨 Modern UI/UX
- Responsive design with Tailwind CSS
- Clean, professional interface
- Accessibility-compliant components
- Dark/light mode support (configurable)

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Authentication**: JWT with js-cookie
- **State Management**: React Context API

## Getting Started

### Prerequisites
- Node.js 18.x or later
- npm or yarn package manager
- Treasury Agent API backend running

### Installation

1. **Clone and navigate to frontend directory**:
   ```bash
   cd treasury_agent/apps/treasury-dashboard
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Configuration**:
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Demo Users

The application includes demo users for testing different roles:

- **Admin**: `admin@treasury.com` / `admin123`
- **Manager**: `manager@treasury.com` / `manager123`
- **Approver**: `approver@treasury.com` / `approver123`
- **Analyst**: `analyst@treasury.com` / `analyst123`

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (redirects to dashboard)
│   ├── login/             # Authentication pages
│   └── dashboard/         # Protected dashboard pages
│       ├── layout.tsx     # Dashboard layout
│       ├── page.tsx       # Main dashboard
│       ├── analytics/     # Analytics page (admin only)
│       ├── payments/      # Payment management
│       └── chat/          # AI assistant
├── components/            # Reusable React components
│   ├── analytics-dashboard.tsx
│   ├── chat-interface.tsx
│   ├── dashboard-layout.tsx
│   ├── login-form.tsx
│   ├── payment-management.tsx
│   ├── protected-component.tsx
│   └── protected-route.tsx
├── contexts/              # React Context providers
│   └── auth-context.tsx   # Authentication state management
├── lib/                   # Utility functions and API client
│   ├── api.ts            # Axios-based API client
│   ├── types.ts          # TypeScript type definitions
│   └── utils.ts          # Helper functions
└── styles/               # Global styles
    └── globals.css       # Tailwind CSS imports
```

## Role-Based Features

### Viewer (Base Role)
- View dashboard overview
- Check account balances
- Generate basic reports

### Treasury Analyst
- All viewer permissions
- Access to detailed analytics
- Transaction analysis tools

### Payment Approver
- Viewer and analyst permissions
- Approve/reject payment transactions
- Access payment approval workflows

### Treasury Manager
- All approver permissions
- Liquidity management tools
- Risk assessment features
- Advanced forecasting

### CFO/Admin
- Full system access
- User management
- System configuration
- Complete analytics suite

## Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Environment Variables
```env
# Production environment
NEXT_PUBLIC_API_URL=https://api.treasury-agent.com
NODE_ENV=production
```

## Security Features

1. **Authentication**: JWT tokens stored in HTTP-only cookies
2. **Route Protection**: Client and server-side route guards
3. **Role-Based Access**: Component-level permission checking
4. **API Security**: Automatic logout on authentication failures
5. **XSS Prevention**: Content Security Policy headers

## Troubleshooting

### Common Issues

1. **API Connection**: Verify `NEXT_PUBLIC_API_URL` environment variable
2. **Authentication**: Clear cookies and localStorage, restart server
3. **Build Errors**: Delete `.next` folder and `node_modules`, reinstall

### Development Tips

1. Use React DevTools for component debugging
2. Check Network tab for API request/response details
3. Use browser's Application tab to inspect stored tokens
