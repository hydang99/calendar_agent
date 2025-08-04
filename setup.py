#!/usr/bin/env python3
"""
Setup script for Event Agent
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages."""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def setup_environment():
    return None

def check_dependencies():
    """Check if all dependencies are available."""
    print("🔍 Checking dependencies...")
    
    try:
        import selenium
        import streamlit
        import googlemaps
        from google.cloud import aiplatform
        print("✅ All dependencies are available!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Main setup function."""
    print("🎉 Event Agent Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during requirement installation")
        return 1
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Setup completed but some dependencies are missing")
        print("💡 Try: pip install -r requirements.txt")
        return 1
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API credentials")
    print("2. Run: streamlit run streamlit_app.py")
    print("3. Or use the Jupyter notebook: testing.ipynb")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 