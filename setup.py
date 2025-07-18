#!/usr/bin/env python3
"""
Setup script for Market Sector Sentiment Analysis Tool
This script helps set up the development environment
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_prerequisites():
    """Check if prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 11):
        print(f"❌ Python 3.11+ required, found {python_version.major}.{python_version.minor}")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor} found")
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm found: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    # Check Redis (optional)
    try:
        result = subprocess.run(["redis-server", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Redis found: {result.stdout.strip()}")
        else:
            print("⚠️  Redis not found - you'll need to install it later")
    except FileNotFoundError:
        print("⚠️  Redis not found - you'll need to install it later")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_command = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_command = "venv/bin/pip"
    
    if not run_command(f"{pip_command} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_command} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    return True

def setup_node_environment():
    """Set up Node.js environment and install dependencies"""
    print("\n📦 Setting up Node.js environment...")
    
    if not run_command("npm install", "Installing Node.js dependencies"):
        return False
    
    return True

def setup_credentials():
    """Set up credentials file"""
    print("\n🔐 Setting up credentials...")
    
    credentials_path = Path("credentials.yml")
    template_path = Path("credentials.template.yml")
    
    if credentials_path.exists():
        print("✅ credentials.yml already exists")
        return True
    
    if template_path.exists():
        shutil.copy(template_path, credentials_path)
        print("✅ Created credentials.yml from template")
        print("⚠️  Please edit credentials.yml and add your API keys")
        return True
    else:
        print("❌ credentials.template.yml not found")
        return False

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        "data",
        "logs",
        "tests/backend",
        "tests/frontend",
        "src/backend/services",
        "src/backend/mcp",
        "src/backend/agents",
        "src/frontend/src/components",
        "src/frontend/src/pages",
        "src/frontend/src/hooks",
        "src/frontend/src/services",
        "src/frontend/src/types"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified directory: {directory}")
    
    return True

def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")
    
    # Test Python imports
    if os.name == 'nt':  # Windows
        python_command = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_command = "venv/bin/python"
    
    test_command = f"{python_command} -c \"import fastapi, sqlalchemy, redis; print('✅ Python imports successful')\""
    if not run_command(test_command, "Testing Python imports"):
        return False
    
    # Test Node.js
    if not run_command("npm run type-check", "Testing TypeScript compilation"):
        print("⚠️  TypeScript check failed - this is expected for initial setup")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Market Sector Sentiment Analysis Tool - Setup Script")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install the required software.")
        return 1
    
    # Setup Python environment
    if not setup_python_environment():
        print("\n❌ Python environment setup failed.")
        return 1
    
    # Setup Node.js environment
    if not setup_node_environment():
        print("\n❌ Node.js environment setup failed.")
        return 1
    
    # Setup credentials
    if not setup_credentials():
        print("\n❌ Credentials setup failed.")
        return 1
    
    # Setup directories
    if not setup_directories():
        print("\n❌ Directory setup failed.")
        return 1
    
    # Run basic tests
    if not run_tests():
        print("\n⚠️  Some tests failed, but setup may still be functional.")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit credentials.yml and add your API keys")
    print("2. Install Redis locally (if not already installed)")
    print("3. Run the MCP server tests: python test_mcp_servers.py")
    print("4. Start the backend: cd src/backend && python main.py")
    print("5. Start the frontend: npm run dev")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 