#!/usr/bin/env python3
"""
Quick demo script to test the secure deployment locally
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from dotenv import load_dotenv
load_dotenv()
def check_environment():
    """Check if environment is properly configured."""
    print("🔍 Checking environment configuration...")
    
    # Check for environment file
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env file found")
        # Load environment variables

    else:
        print("⚠️ .env file not found. Using system environment variables.")
    
    # Check required environment variables
    vertex_project_id = os.getenv('VERTEX_PROJECT_ID')
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    print(f"📍 Vertex Project ID: {'✅ Set' if vertex_project_id else '❌ Missing'}")
    print(f"🗺️ Google Maps API Key: {'✅ Set' if google_maps_api_key else '❌ Missing'}")
    
    return bool(vertex_project_id and google_maps_api_key)

def run_streamlit():
    """Run the Streamlit app."""
    print("\n🚀 Starting Streamlit app...")
    print("📱 Open your browser to: http://localhost:8501")
    print("⏹️ Press Ctrl+C to stop\n")
    
    import subprocess
    try:
        subprocess.run([
            "streamlit", "run", "streamlit_app.py",
            "--server.address", "localhost",
            "--server.port", "8501"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped")
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: pip install streamlit")

def main():
    """Main demo function."""
    print("🎉 Event Agent - Local Demo")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment not properly configured!")
        print("\n📝 To fix this:")
        print("1. Copy env.template to .env: cp env.template .env")
        print("2. Edit .env with your actual API keys")
        print("3. Run this script again")
        return
    
    print("\n✅ Environment looks good!")
    
    # Ask user if they want to run Streamlit
    response = input("\nRun Streamlit app? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        run_streamlit()
    else:
        print("👋 Demo complete. Run 'streamlit run streamlit_app.py' manually when ready.")

if __name__ == "__main__":
    main()