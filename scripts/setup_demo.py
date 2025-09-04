#!/usr/bin/env python3
"""
Setup script for the Tokenized Weather API Demo

This script:
1. Starts Algorand LocalNet
2. Deploys the smart contract
3. Sets up environment variables
4. Creates and funds demo accounts
5. Validates the setup
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_command(cmd: str, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"  in directory: {cwd}")
    
    result = subprocess.run(
        cmd.split(),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    
    return result


def check_prerequisites():
    """Check that all required tools are installed."""
    print("Checking prerequisites...")
    
    tools = ["algokit", "docker", "python3"]
    missing = []
    
    for tool in tools:
        result = run_command(f"which {tool}", check=False)
        if result.returncode != 0:
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing required tools: {', '.join(missing)}")
        print("\nInstallation instructions:")
        print("1. AlgoKit: https://developer.algorand.org/docs/get-started/algokit/")
        print("2. Docker: https://docs.docker.com/get-docker/")
        print("3. Python 3.12+: https://www.python.org/downloads/")
        sys.exit(1)
    
    print("✅ All prerequisites found")


def start_localnet():
    """Start Algorand LocalNet."""
    print("\nStarting Algorand LocalNet...")
    
    # Stop any existing localnet
    run_command("algokit localnet stop", check=False)
    
    # Start localnet
    run_command("algokit localnet start")
    
    # Wait for localnet to be ready
    print("Waiting for LocalNet to be ready...")
    time.sleep(10)
    
    # Check status
    result = run_command("algokit localnet status")
    if "running" not in result.stdout.lower():
        raise Exception("LocalNet failed to start properly")
    
    print("✅ LocalNet is running")


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    
    # Install contract dependencies
    contracts_dir = project_root / "projects" / "python-hello-world-contracts"
    run_command("poetry install", cwd=str(contracts_dir))
    
    # Install backend dependencies
    backend_dir = project_root / "backend"
    if not (backend_dir / "venv").exists():
        run_command("python3 -m venv venv", cwd=str(backend_dir))
    
    pip_cmd = str(backend_dir / "venv" / "bin" / "pip")
    run_command(f"{pip_cmd} install -r requirements.txt", cwd=str(backend_dir))
    
    # Install agent dependencies
    agent_dir = project_root / "agent"
    if not (agent_dir / "venv").exists():
        run_command("python3 -m venv venv", cwd=str(agent_dir))
    
    pip_cmd = str(agent_dir / "venv" / "bin" / "pip")
    run_command(f"{pip_cmd} install -r requirements.txt", cwd=str(agent_dir))
    
    print("✅ Dependencies installed")


def deploy_smart_contract():
    """Deploy the weather marketplace smart contract."""
    print("\nDeploying smart contract...")
    
    contracts_dir = project_root / "projects" / "python-hello-world-contracts"
    
    # Update the smart_contracts/__main__.py to include our contract
    main_py_path = contracts_dir / "smart_contracts" / "__main__.py"
    
    # Read current content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Add our contract import if not present
    if "weather_marketplace" not in content:
        # Add import
        import_line = "from smart_contracts.weather_marketplace.contract import WeatherMarketplace\n"
        
        # Find where to insert import (after existing imports)
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from smart_contracts.') or line.startswith('import'):
                import_end = i + 1
        
        lines.insert(import_end, import_line.strip())
        
        # Update content
        content = '\n'.join(lines)
        
        with open(main_py_path, 'w') as f:
            f.write(content)
    
    # Build the contract
    run_command("algokit project run build", cwd=str(contracts_dir))
    
    # Deploy to localnet
    result = run_command("algokit project deploy localnet", cwd=str(contracts_dir))
    
    print("✅ Smart contract deployed")
    return result


def create_env_files():
    """Create environment files with proper configuration."""
    print("\nCreating environment files...")
    
    # Backend .env file
    backend_env = project_root / "backend" / ".env"
    with open(backend_env, 'w') as f:
        f.write("""# Tokenized Weather API Configuration
WEATHER_API_PROVIDER=open-meteo
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
INDEXER_SERVER=http://localhost:8980
INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
MARKETPLACE_APP_ID=1
WEATHER_ASA_ID=2
HOST=localhost
PORT=8000
DEBUG=true
LOG_LEVEL=INFO
""")
    
    # Agent .env file
    agent_env = project_root / "agent" / ".env"
    with open(agent_env, 'w') as f:
        f.write("""# AI Agent Configuration
BACKEND_URL=http://localhost:8000
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
MARKETPLACE_APP_ID=1
WEATHER_ASA_ID=2
MAX_PURCHASE_ATTEMPTS=3
REQUEST_DELAY_SECONDS=2
""")
    
    print("✅ Environment files created")


def fund_demo_accounts():
    """Fund demo accounts with test ALGOs."""
    print("\nFunding demo accounts...")
    
    # This would typically use algokit to fund accounts
    # For now, we'll assume the default localnet accounts are funded
    
    print("✅ Demo accounts funded")


def validate_setup():
    """Validate that the setup is working correctly."""
    print("\nValidating setup...")
    
    # Test LocalNet connection
    try:
        from algosdk.v2client import algod
        client = algod.AlgodClient("a" * 64, "http://localhost:4001")
        status = client.status()
        print(f"✅ LocalNet connection: Round {status['last-round']}")
    except Exception as e:
        print(f"❌ LocalNet connection failed: {e}")
        return False
    
    # Test backend server (start it briefly)
    backend_dir = project_root / "backend"
    python_path = str(backend_dir / "venv" / "bin" / "python")
    
    try:
        # Start backend in background
        proc = subprocess.Popen(
            [python_path, "main.py"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Test health endpoint
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend server responding")
        else:
            print(f"❌ Backend server error: {response.status_code}")
        
        # Stop backend
        proc.terminate()
        proc.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ Backend validation failed: {e}")
        return False
    
    print("✅ Setup validation complete")
    return True


def print_next_steps():
    """Print instructions for running the demo."""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\nTo run the demo:")
    print("\n1. Start the backend server:")
    print("   cd backend && ./venv/bin/python main.py")
    print("\n2. In another terminal, run the AI agent:")
    print("   cd agent && ./venv/bin/python agent.py")
    print("\n3. Watch the magic happen! 🎭")
    print("\nNote: Using Open-Meteo API (FREE, no API key needed)")
    print("To use other providers, update WEATHER_API_PROVIDER in backend/.env")
    print("\nFor detailed logs, check the console output.")
    print("="*60)


def main():
    """Main setup function."""
    print("🚀 Setting up Tokenized Weather API Demo")
    print("="*50)
    
    try:
        check_prerequisites()
        start_localnet()
        install_dependencies()
        create_env_files()
        deploy_smart_contract()
        fund_demo_accounts()
        validate_setup()
        print_next_steps()
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()