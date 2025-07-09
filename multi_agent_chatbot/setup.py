#!/usr/bin/env python3
"""
Setup script for multi-agent chatbot
"""
import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_environment():
    """Set up environment file"""
    print("\n🔧 Setting up environment...")
    
    if os.path.exists('.env'):
        print("⚠️ .env file already exists. Skipping environment setup.")
        return True
    
    if os.path.exists('.env.template'):
        try:
            shutil.copy('.env.template', '.env')
            print("✅ .env file created from template")
            print("⚠️ Please edit .env file with your actual API keys")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ .env.template file not found")
        return False

def check_data_files():
    """Check if required data files exist"""
    print("\n📁 Checking data files...")
    
    required_files = [
        'data/sample_database.sqlite',
        'data/documents/sample1.txt',
        'data/documents/sample2.txt'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} found")
        else:
            print(f"❌ {file_path} not found")
            all_files_exist = False
    
    return all_files_exist

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_agents.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print("⚠️ Some tests failed. Check your configuration.")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ Tests timed out. This might be due to network issues.")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Multi-Agent Chatbot Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Setup failed during environment setup")
        sys.exit(1)
    
    # Check data files
    if not check_data_files():
        print("\n⚠️ Some data files are missing. The application might not work correctly.")
    
    # Run tests (optional)
    run_tests()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your actual API keys")
    print("2. Run: streamlit run app.py")
    print("3. Open your browser to the displayed URL")

if __name__ == "__main__":
    main()
