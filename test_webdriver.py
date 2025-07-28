#!/usr/bin/env python3
"""
Test script to diagnose Chrome WebDriver issues
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_chrome_installation():
    """Test if Chrome is installed."""
    print("🔍 Testing Chrome installation...")
    
    # Common Chrome paths
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
        '/usr/bin/google-chrome',  # Linux
        '/usr/bin/chromium-browser',  # Linux alternative
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'  # Windows 32-bit
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            return True
    
    print("❌ Chrome not found in common locations")
    return False

def test_chromedriver_manager():
    """Test ChromeDriverManager."""
    print("\n🔍 Testing ChromeDriverManager...")
    
    try:
        driver_path = ChromeDriverManager().install()
        print(f"✅ ChromeDriverManager installed driver at: {driver_path}")
        return True
    except Exception as e:
        print(f"❌ ChromeDriverManager failed: {e}")
        return False

def test_basic_webdriver():
    """Test basic WebDriver setup."""
    print("\n🔍 Testing basic WebDriver setup...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        print(f"✅ Basic WebDriver test successful. Page title: {title}")
        return True
    except Exception as e:
        print(f"❌ Basic WebDriver test failed: {e}")
        return False

def test_fallback_webdriver():
    """Test WebDriver without ChromeDriverManager."""
    print("\n🔍 Testing fallback WebDriver (system PATH)...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        print(f"✅ Fallback WebDriver test successful. Page title: {title}")
        return True
    except Exception as e:
        print(f"❌ Fallback WebDriver test failed: {e}")
        return False

def test_event_agent_import():
    """Test importing the EventAgent."""
    print("\n🔍 Testing EventAgent import...")
    
    try:
        from event_agent import EventAgent
        print("✅ EventAgent imported successfully")
        return True
    except Exception as e:
        print(f"❌ EventAgent import failed: {e}")
        return False

def provide_solutions():
    """Provide solutions for common issues."""
    print("\n💡 Solutions for common issues:")
    print("="*50)
    
    print("\n1. If Chrome is not installed:")
    print("   - macOS: Download from https://www.google.com/chrome/")
    print("   - Linux: sudo apt-get install google-chrome-stable")
    print("   - Or use: brew install --cask google-chrome")
    
    print("\n2. If ChromeDriver issues persist:")
    print("   - macOS: brew install chromedriver")
    print("   - Manually download from: https://chromedriver.chromium.org/")
    print("   - Add to PATH: export PATH=$PATH:/path/to/chromedriver")
    
    print("\n3. If you get permission errors:")
    print("   - macOS: xattr -d com.apple.quarantine /path/to/chromedriver")
    print("   - Linux: chmod +x /path/to/chromedriver")
    
    print("\n4. Alternative solutions:")
    print("   - Try using Firefox: pip install geckodriver-autoinstaller")
    print("   - Use the requests fallback (no dynamic content)")
    print("   - Run without headless mode for debugging")

def main():
    """Main test function."""
    print("🧪 Chrome WebDriver Diagnostic Tool")
    print("="*50)
    
    # Run all tests
    tests = [
        test_chrome_installation,
        test_chromedriver_manager,
        test_basic_webdriver,
        test_fallback_webdriver,
        test_event_agent_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 Test Summary:")
    print("="*30)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your setup should work correctly.")
    elif passed >= total - 1:
        print("⚠️ Most tests passed. The agent should work with some limitations.")
    else:
        print("❌ Multiple tests failed. Please check the solutions below.")
        provide_solutions()

if __name__ == "__main__":
    main() 