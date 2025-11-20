# Treasury Service Quick Commands

## ✅ **Working Commands (Fixed)**

### Start Treasury Service
```bash
# From treasury_agent root directory:

# Option 1: Use the convenient startup script (RECOMMENDED)
./scripts/start-treasury.sh

# Option 2: Direct command with full path to virtual environment Python
cd services/treasury_service && .venv/bin/python enhanced_app.py
```

### Test Service is Running
```bash
# Health check
curl http://localhost:8004/health

# MockBankAPI test
curl http://localhost:8004/test/mock-api

# Service info
curl http://localhost:8004/
```

### Start Frontend (Next.js Dashboard)
```bash
cd apps/treasury-dashboard && npm run dev
# Runs on http://localhost:3000
```

## ❌ **Commands That DON'T Work**

```bash
# This fails because 'python' command not found in PATH
cd services/treasury_service && python simple_app.py

# This fails because relative path to venv doesn't work from subdirectory
cd services/treasury_service && ../../.venv/bin/python enhanced_app.py
```

## 💡 **Why the Fix Works**

1. **Startup Script**: Automatically detects paths and uses absolute paths to virtual environment
2. **Full Path Command**: Uses absolute path to the virtual environment's Python interpreter
3. **Enhanced App**: Uses the `enhanced_app.py` which includes MockBankAPI integration

## 🚀 **Enterprise Architecture Status**

- **Backend Service**: ✅ Running on `http://localhost:8004`
- **Health Monitoring**: ✅ Available at `/health`
- **MockBankAPI**: ✅ Integrated and tested
- **Frontend Ready**: ✅ Next.js dashboard in `apps/treasury-dashboard/`
- **Enterprise Compliance**: ✅ Full microservices architecture