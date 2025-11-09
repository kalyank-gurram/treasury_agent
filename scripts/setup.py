import os
import sys
import subprocess

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, "data")
FAISS_DIR = os.path.join(BASE, "rag", "faiss_store")

def run(cmd: str):
    """Run a shell command with error handling."""
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("Treasury Agent setup starting...\n")

    # 1. Check data directory
    if not os.path.exists(os.path.join(DATA_DIR, "accounts.csv")):
        print("No data found - generating mock data...")
        run("poetry run python scripts/generate_mock_data.py")
    else:
        print("Mock data already exists - skipping.")

    # 2. Check vectorstore
    if not os.path.exists(FAISS_DIR) or not os.listdir(FAISS_DIR):
        print("No FAISS store found - building vectorstore...")
        run("poetry run python scripts/build_vectorstore.py")
    else:
        print("FAISS vectorstore already exists - skipping.")

    print("\nSetup complete! You can now run:")
    print("   poetry run uvicorn server.app:app --reload --port 8000")
    print("   poetry run python ui/gradio_app.py")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("Error running setup steps:", e)
        sys.exit(1)
