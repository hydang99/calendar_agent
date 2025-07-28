#!/usr/bin/env python3
"""
Diagnostic script to test restaurant search functionality
"""

import os
from event_agent import EventAgent

def test_google_maps_setup():
    """Test Google Maps API setup."""
    print("🔍 Testing Google Maps API Setup")
    print("=" * 40)
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not found in environment variables")
        print("💡 Solutions:")
        print("   1. Create .env file with: GOOGLE_MAPS_API_KEY=your-api-key")
        print("   2. Or export GOOGLE_MAPS_API_KEY=your-api-key")
        return False
    
    if len(api_key) < 30:
        print(f"⚠️ API key looks too short: {len(api_key)} characters")
        print("💡 Google Maps API keys are typically 39+ characters")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-5:]} ({len(api_key)} chars)")
    
    # Test API key with a simple request
    try:
        import googlemaps
        gmaps = googlemaps.Client(key=api_key)
        
        # Test with a simple geocoding request
        result = gmaps.geocode("San Francisco, CA")
        if result:
            print("✅ API key is working - geocoding test successful")
            return True
        else:
            print("❌ API key test failed - no results from geocoding")
            return False
            
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        
        if 'API_KEY' in str(e).upper():
            print("💡 API key issue detected. Please check:")
            print("   - Key is correct and not expired")
            print("   - Places API is enabled in Google Cloud Console")
            print("   - Billing is set up for your project")
        
        return False

def test_location_extraction():
    """Test location extraction from sample event data."""
    print("\n🔍 Testing Location Extraction")
    print("=" * 40)
    
    # Sample event data scenarios
    test_cases = [
        {
            "name": "Full address",
            "data": {"address": "123 Main St, San Francisco, CA 94102"}
        },
        {
            "name": "Venue name only",
            "data": {"venue_name": "Convention Center, San Francisco"}
        },
        {
            "name": "City only",
            "data": {"city": "San Francisco, CA"}
        },
        {
            "name": "Addresses list",
            "data": {"addresses": ["456 Market St", "789 Union Square"]}
        },
        {
            "name": "No location info",
            "data": {"title": "Tech Conference", "date": "2024-03-15"}
        }
    ]
    
    agent = EventAgent()
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        # Extract location using the same logic as the agent
        location_candidates = [
            test_case['data'].get('address'),
            test_case['data'].get('full_address'), 
            test_case['data'].get('venue_name'),
            test_case['data'].get('city'),
            test_case['data'].get('addresses', [None])[0] if test_case['data'].get('addresses') else None
        ]
        
        location = None
        for candidate in location_candidates:
            if candidate and len(str(candidate).strip()) > 3:
                location = str(candidate).strip()
                break
        
        if location:
            print(f"   ✅ Extracted location: '{location}'")
        else:
            print(f"   ❌ No location extracted")

def test_restaurant_search_methods():
    """Test different restaurant search methods."""
    print("\n🔍 Testing Restaurant Search Methods")
    print("=" * 40)
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ Skipping - Google Maps API key not configured")
        return
    
    try:
        import googlemaps
        gmaps = googlemaps.Client(key=api_key)
        
        # Test location
        test_location = "San Francisco, CA"
        print(f"📍 Testing with location: {test_location}")
        
        # Method 1: Places nearby
        print("\n1️⃣ Testing Places Nearby Search...")
        try:
            result = gmaps.places_nearby(
                location=test_location,
                radius=2000,
                type='restaurant'
            )
            status = result.get('status')
            results_count = len(result.get('results', []))
            print(f"   Status: {status}")
            print(f"   Results: {results_count} restaurants")
            
            if status == 'OK' and results_count > 0:
                sample = result['results'][0]
                print(f"   Sample: {sample.get('name')} - {sample.get('vicinity')}")
            elif status == 'INVALID_REQUEST':
                print("   ⚠️ Invalid request - trying geocoding first...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 2: Text search
        print("\n2️⃣ Testing Text Search...")
        try:
            query = f"restaurants near {test_location}"
            result = gmaps.places(query=query)
            status = result.get('status')
            results_count = len(result.get('results', []))
            print(f"   Query: {query}")
            print(f"   Status: {status}")
            print(f"   Results: {results_count} restaurants")
            
            if status == 'OK' and results_count > 0:
                sample = result['results'][0]
                print(f"   Sample: {sample.get('name')} - {sample.get('formatted_address')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 3: Geocoding + nearby
        print("\n3️⃣ Testing Geocoding + Nearby Search...")
        try:
            geocode_result = gmaps.geocode(test_location)
            if geocode_result:
                lat_lng = geocode_result[0]['geometry']['location']
                print(f"   Geocoded to: {lat_lng}")
                
                result = gmaps.places_nearby(
                    location=lat_lng,
                    radius=2000,
                    type='restaurant'
                )
                status = result.get('status')
                results_count = len(result.get('results', []))
                print(f"   Status: {status}")
                print(f"   Results: {results_count} restaurants")
                
                if status == 'OK' and results_count > 0:
                    sample = result['results'][0]
                    print(f"   Sample: {sample.get('name')} - {sample.get('vicinity')}")
            else:
                print("   ❌ Geocoding failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    except Exception as e:
        print(f"❌ Restaurant search test failed: {e}")

def test_full_workflow():
    """Test the full workflow with sample event data."""
    print("\n🔍 Testing Full Workflow")
    print("=" * 40)
    
    # Sample event with good location data
    sample_event = {
        "title": "Test Conference",
        "date": "2024-03-15",
        "venue_name": "Moscone Center",
        "address": "747 Howard St, San Francisco, CA 94103",
        "city": "San Francisco, CA"
    }
    
    print(f"📋 Sample event data: {sample_event}")
    
    agent = EventAgent()
    
    print("\n🍽️ Searching for restaurants...")
    restaurants = agent.search_restaurants(sample_event, radius=1000)
    
    print(f"\n📊 Results: {len(restaurants)} restaurants found")
    
    if restaurants:
        print("\n🥘 Sample restaurants:")
        for i, restaurant in enumerate(restaurants[:3], 1):
            print(f"   {i}. {restaurant.get('name', 'Unknown')}")
            print(f"      Rating: {restaurant.get('rating', 'N/A')}")
            print(f"      Address: {restaurant.get('address', 'N/A')}")
    else:
        print("❌ No restaurants found - check the detailed logs above")

def provide_troubleshooting_tips():
    """Provide troubleshooting tips."""
    print("\n💡 Troubleshooting Tips")
    print("=" * 40)
    
    print("\n1️⃣ API Key Issues:")
    print("   - Get API key from: https://console.cloud.google.com/")
    print("   - Enable Places API, Maps JavaScript API, Geocoding API")
    print("   - Set up billing (even for free tier)")
    print("   - Add API restrictions if needed")
    
    print("\n2️⃣ Common Problems:")
    print("   - 'INVALID_REQUEST': Usually bad location format")
    print("   - 'ZERO_RESULTS': Location too remote or rural")
    print("   - 'OVER_QUERY_LIMIT': API quota exceeded")
    print("   - 'REQUEST_DENIED': API key or billing issue")
    
    print("\n3️⃣ Location Extraction:")
    print("   - Event pages need clear address or venue info")
    print("   - Try events with full addresses (street, city, state)")
    print("   - Conference centers and hotels work best")
    
    print("\n4️⃣ Testing Commands:")
    print("   - Set API key: export GOOGLE_MAPS_API_KEY=your-key")
    print("   - Test this script: python test_restaurant_search.py")
    print("   - Check logs in the main app for detailed errors")

def main():
    """Main diagnostic function."""
    print("🧪 Restaurant Search Diagnostic Tool")
    print("=" * 50)
    
    # Run all tests
    api_working = test_google_maps_setup()
    test_location_extraction()
    
    if api_working:
        test_restaurant_search_methods()
        test_full_workflow()
    else:
        print("\n⚠️ Skipping restaurant tests - fix API setup first")
    
    provide_troubleshooting_tips()
    
    print("\n🎯 Summary:")
    if api_working:
        print("✅ API setup looks good - check the workflow results above")
    else:
        print("❌ API setup needs attention - follow the troubleshooting tips")

if __name__ == "__main__":
    main() 