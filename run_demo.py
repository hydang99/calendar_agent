#!/usr/bin/env python3
"""
Simple demo script to test the Event Agent
"""

import os
from event_agent import EventAgent

def demo_basic_functionality():
    """Demo basic agent functionality without real URLs."""
    print("🎉 Event Agent Demo")
    print("=" * 40)
    
    # Initialize agent (API keys optional for this demo)
    print("🤖 Initializing Event Agent...")
    agent = EventAgent()
    
    # Test basic info extraction patterns
    print("\n📋 Testing information extraction patterns...")
    
    # Sample HTML content for testing
    sample_html = """
    <html>
    <head><title>Tech Conference 2024</title></head>
    <body>
        <h1>Annual Tech Conference 2024</h1>
        <p>Date: March 15, 2024</p>
        <p>Time: 9:00 AM - 5:00 PM</p>
        <p>Location: Convention Center, 123 Main St, San Francisco, CA 94102</p>
        <div class="agenda">
            <h2>Agenda</h2>
            <ul>
                <li>9:00 AM - Opening Keynote</li>
                <li>11:00 AM - AI Workshop</li>
                <li>2:00 PM - Panel Discussion</li>
                <li>4:00 PM - Closing Remarks</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_html, 'html.parser')
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Test basic extraction
    basic_info = agent._extract_basic_info(soup, text_content)
    print(f"📊 Extracted basic info: {basic_info}")
    
    # Test restaurant search (if Google Maps API is available)
    if hasattr(agent, 'gmaps') and agent.gmaps:
        print("\n🍽️ Testing restaurant search...")
        sample_event = {
            'address': 'Convention Center, San Francisco, CA',
            'venue_name': 'Convention Center'
        }
        restaurants = agent.search_restaurants(sample_event)
        print(f"📍 Found {len(restaurants)} restaurants nearby")
        
        if restaurants:
            print("🥘 Sample restaurant:")
            restaurant = restaurants[0]
            for key, value in restaurant.items():
                if value:
                    print(f"   {key}: {value}")
    else:
        print("⚠️ Google Maps API not configured - skipping restaurant search")
    
    # Test email generation
    print("\n📧 Testing email generation...")
    sample_event = {
        'title': 'Tech Conference 2024',
        'date': '2024-03-15',
        'start_time': '09:00',
        'end_time': '17:00',
        'venue_name': 'Convention Center'
    }
    
    sample_restaurant = {
        'name': 'Gourmet Bistro',
        'address': '456 Market St, San Francisco, CA',
        'phone': '(555) 123-4567'
    }
    
    email = agent.draft_booking_email(sample_event, sample_restaurant, 4)
    print("📮 Sample booking email:")
    print("-" * 30)
    print(email[:500] + "..." if len(email) > 500 else email)
    
    print("\n✅ Demo completed successfully!")
    print("\n💡 Next steps:")
    print("1. Set up your API keys in .env file")
    print("2. Run: streamlit run streamlit_app.py")
    print("3. Test with real event URLs")

def demo_with_real_url():
    """Demo with a real URL if user provides one."""
    print("\n🌐 Test with Real URL")
    print("=" * 30)
    
    url = input("Enter an event URL to test (or press Enter to skip): ").strip()
    
    if not url:
        print("⏭️ Skipping real URL test")
        return
    
    print(f"🔍 Testing with URL: {url}")
    
    # Initialize agent
    agent = EventAgent()
    
    try:
        # Test extraction
        print("📄 Extracting event information...")
        event_info = agent.extract_event_info(url)
        
        if 'error' in event_info:
            print(f"❌ Extraction failed: {event_info['error']}")
        else:
            print("✅ Extraction successful!")
            print("📋 Event Information:")
            for key, value in event_info.items():
                if value and key != 'ai_response':
                    print(f"   {key}: {value}")
            
            if event_info.get('ai_response'):
                print(f"\n🤖 AI Response: {event_info['ai_response'][:200]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main demo function."""
    try:
        demo_basic_functionality()
        demo_with_real_url()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 