#!/usr/bin/env python3
"""
Treasury Service Startup Script

Enterprise-grade startup script for the Treasury microservice.
"""

import sys
import os
from pathlib import Path

# Add the workspace root to Python path
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

# Set environment variables for proper module resolution  
os.environ.setdefault('PYTHONPATH', str(workspace_root))
os.environ.setdefault('TREASURY_ENV', 'local')

# Import and run the FastAPI application
try:
    import uvicorn
    from services.treasury_service.app import app
    
    if __name__ == "__main__":
        # Enterprise startup configuration
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(workspace_root / "services" / "treasury-service")],
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Please ensure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Startup Error: {e}")
    sys.exit(1)