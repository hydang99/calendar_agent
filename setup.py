#!/usr/bin/env python3
"""
Setup script for Event Agent
"""

import os
import subprocess
import sys
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="event-agent-framework",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An intelligent agent framework for event information extraction and restaurant booking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/event-agent-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Communications :: Email",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "event-agent=streamlit run streamlit_app.py",
        ],
    },
    keywords="event extraction, restaurant booking, web scraping, email automation, ai",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/event-agent-framework/issues",
        "Source": "https://github.com/yourusername/event-agent-framework",
        "Documentation": "https://github.com/yourusername/event-agent-framework#readme",
    },
)

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
    """Setup environment file."""
    print("⚙️ Setting up environment...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("🔧 Please edit .env file with your API credentials")
        else:
            print("⚠️ No .env.example found, creating basic .env file")
            with open('.env', 'w') as f:
                f.write("VERTEX_PROJECT_ID=your-google-cloud-project-id\n")
                f.write("GOOGLE_MAPS_API_KEY=your-google-maps-api-key\n")
    else:
        print("ℹ️ .env file already exists")

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