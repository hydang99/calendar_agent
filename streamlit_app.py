import streamlit as st
import json
import os
import platform
from datetime import datetime
from event_agent import EventAgent
import pandas as pd
from dotenv import load_dotenv

# CRITICAL: Load .env file before any environment variable access
# Use override=True to ensure .env values take precedence over existing environment variables
load_dotenv(override=True)

# Handle Google Cloud authentication for Streamlit Cloud deployment
try:
    # Force Google Cloud to NOT use metadata service in Streamlit Cloud
    # This prevents the 503 metadata service error  
    if '/mount/src/' in os.getcwd():
        # We're in Streamlit Cloud - disable metadata service
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""
        os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv('VERTEX_PROJECT_ID', '')
        print("🔧 Streamlit Cloud detected - disabled metadata service")
        
except Exception as auth_error:
    # Log but don't fail - will fall back to environment variables
    print(f"Note: Auth setup note: {auth_error}")

# Set page config
st.set_page_config(
    page_title="Event Agent Demo",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .email-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_agent():
    """Initialize the EventAgent with API credentials."""
    # For production deployment, use environment variables only
    vertex_project_id = os.getenv('VERTEX_PROJECT_ID')
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # In development mode, also check Streamlit secrets
    if not vertex_project_id:
        vertex_project_id = st.secrets.get('VERTEX_PROJECT_ID', '')
    if not google_maps_api_key:
        google_maps_api_key = st.secrets.get('GOOGLE_MAPS_API_KEY', '')
    
    if not vertex_project_id or not google_maps_api_key:
        st.error("🔐 **Configuration Required**")
        st.error("API credentials are not properly configured. Please contact the administrator.")
        st.info("💡 **For administrators**: Set VERTEX_PROJECT_ID and GOOGLE_MAPS_API_KEY in your deployment environment.")
        return None
    
    try:
        agent = EventAgent(
            vertex_project_id=vertex_project_id,
            vertex_location='us-east1',  # Use supported region
            google_maps_api_key=google_maps_api_key
        )
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

def display_event_info(event_info):
    """Display extracted event information in a nice format."""
    st.markdown('<div class="sub-header">📅 Event Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Event Details:**")
        if event_info.get('title'):
            st.write(f"🎯 **Title:** {event_info['title']}")
        if event_info.get('date'):
            st.write(f"📅 **Date:** {event_info['date']}")
        if event_info.get('start_time') or event_info.get('end_time'):
            start = event_info.get('start_time', 'TBD')
            end = event_info.get('end_time', 'TBD')
            st.write(f"⏰ **Time:** {start} - {end}")
    
    with col2:
        st.markdown("**Location Details:**")
        if event_info.get('venue_name'):
            st.write(f"🏢 **Venue:** {event_info['venue_name']}")
        if event_info.get('address'):
            st.write(f"📍 **Address:** {event_info['address']}")
        if event_info.get('city'):
            st.write(f"🏙️ **City:** {event_info['city']}")
    
    if event_info.get('agenda'):
        st.markdown("**📋 Agenda:**")
        for i, item in enumerate(event_info['agenda'], 1):
            st.write(f"{i}. {item}")
    
    if event_info.get('description'):
        st.markdown("**📝 Description:**")
        st.write(event_info['description'])

def display_restaurants(restaurants):
    """Display restaurant search results."""
    st.markdown('<div class="sub-header">🍽️ Nearby Restaurants</div>', unsafe_allow_html=True)
    
    if not restaurants:
        st.warning("No restaurants found in the area.")
        return
    
    # Create a DataFrame for better display
    restaurant_data = []
    emails_found = 0
    
    for i, restaurant in enumerate(restaurants):
        # Check if email was found
        email_status = ""
        if restaurant.get('email'):
            email_status = "📧 Email available"
            emails_found += 1
        elif restaurant.get('website'):
            email_status = "🌐 Website available"
        
        restaurant_data.append({
            'Name': restaurant.get('name', 'Unknown'),
            'Rating': f"⭐ {restaurant.get('rating', 'N/A')}",
            'Price Level': '💰' * (restaurant.get('price_level') or 1),
            'Address': restaurant.get('address', 'N/A'),
            'Phone': restaurant.get('phone', 'N/A'),
            'Email Status': email_status,
            'Website': restaurant.get('website', 'N/A')
        })
    
    df = pd.DataFrame(restaurant_data)
    st.dataframe(df, use_container_width=True)
    
    # Show summary of email availability
    if emails_found > 0:
        st.success(f"✅ Found {emails_found} restaurant(s) with email addresses - these will be pre-filled below!")
    else:
        st.info("💡 No restaurant emails found automatically. You can enter them manually in the email section below.")

def display_draft_emails(draft_emails, event_info):
    """Display drafted booking emails with email sending functionality."""
    st.markdown('<div class="sub-header">📧 Draft Booking Emails</div>', unsafe_allow_html=True)
    
    if not draft_emails:
        st.warning("No draft emails generated.")
        return
    
    # Email configuration section
    with st.expander("📮 Email Configuration", expanded=False):
        st.markdown('<div class="email-section">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            sender_email = st.text_input(
                "Your Email Address",
                value=st.session_state.get('sender_email', ''),
                placeholder="your.email@gmail.com",
                help="The email address you want to send from"
            )
            st.session_state['sender_email'] = sender_email
            
            email_provider = st.selectbox(
                "Email Provider",
                options=['gmail', 'outlook', 'yahoo'],
                index=0,
                help="Select your email provider"
            )
            st.session_state['email_provider'] = email_provider
        
        with col2:
            sender_password = st.text_input(
                "Email Password / App Password",
                type="password",
                value=st.session_state.get('sender_password', ''),
                help="Use app password for Gmail (recommended for security)"
            )
            st.session_state['sender_password'] = sender_password
            
            # Test email configuration
            if st.button("🔐 Test Email Configuration"):
                if sender_email and sender_password:
                    agent = initialize_agent()
                    if agent:
                        with st.spinner("Testing email configuration..."):
                            validation = agent.validate_email_config(
                                sender_email, sender_password, email_provider
                            )
                        
                        if validation['valid']:
                            st.success(f"✅ {validation['message']}")
                        else:
                            st.error(f"❌ {validation['error']}")
                    else:
                        st.error("Failed to initialize agent")
                else:
                    st.warning("Please enter email and password first")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Email provider help
        if email_provider == 'gmail':
            st.info("""
            **Gmail Setup:**
            1. Enable 2-Factor Authentication
            2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
            3. Use the app password (not your regular password)
            """)
        elif email_provider == 'outlook':
            st.info("""
            **Outlook/Hotmail Setup:**
            1. Enable 2-Factor Authentication
            2. Generate an App Password in Security settings
            3. Use the app password for authentication
            """)
    
    # Individual email sending
    st.markdown("### 📧 Individual Emails")
    
    for i, draft in enumerate(draft_emails):
        restaurant = draft['restaurant']
        email_content = draft['email']
        
        with st.expander(f"📧 Email for {restaurant.get('name', f'Restaurant {i+1}')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Display email content
                st.text_area(
                    f"Draft email for {restaurant.get('name', 'Restaurant')}:",
                    value=email_content,
                    height=300,
                    key=f"email_{i}"
                )
                
                # Restaurant contact info
                if restaurant.get('phone'):
                    st.write(f"📞 **Phone:** {restaurant['phone']}")
                if restaurant.get('website'):
                    st.write(f"🌐 **Website:** [Visit Website]({restaurant['website']})")
            
            with col2:
                # Get extracted restaurant email as default
                extracted_email = restaurant.get('email', '')
                if not extracted_email:
                    # Try to find email using the agent's method
                    agent = initialize_agent()
                    if agent:
                        extracted_email = agent._find_restaurant_email(restaurant) or ''
                
                # Manual email input with extracted email as default
                restaurant_email = st.text_input(
                    "Restaurant Email",
                    value=extracted_email,
                    placeholder="restaurant@example.com" if not extracted_email else "",
                    key=f"restaurant_email_{i}",
                    help="Restaurant email address (auto-extracted if available)"
                )
                
                # Show if email was auto-extracted
                if extracted_email and extracted_email == restaurant_email:
                    st.caption("✅ Auto-extracted from restaurant data")
                elif extracted_email:
                    st.caption("💡 Suggested email (you can edit if needed)")
                
                # Send individual email button
                send_individual = st.button(
                    f"📤 Send Email",
                    key=f"send_{i}",
                    type="primary",
                    disabled=not all([sender_email, sender_password, restaurant_email])
                )
                
                if send_individual:
                    if not restaurant_email:
                        st.error("Please enter restaurant email address")
                    else:
                        agent = initialize_agent()
                        if agent:
                            with st.spinner(f"Sending email to {restaurant.get('name', 'restaurant')}..."):
                                # Get the edited email content from the text area widget
                                edited_email_content = st.session_state.get(f"email_{i}", email_content)
                                
                                # Extract subject and body from edited email content
                                lines = edited_email_content.split('\n')
                                subject_line = None
                                body_lines = []
                                
                                for line in lines:
                                    if line.startswith('Subject:'):
                                        subject_line = line.replace('Subject:', '').strip()
                                    elif subject_line is not None:
                                        body_lines.append(line)
                                
                                if not subject_line:
                                    subject_line = f"Table Reservation Request - {restaurant.get('name', 'Restaurant')}"
                                
                                body = '\n'.join(body_lines).strip()
                                
                                result = agent.send_email(
                                    sender_email=sender_email,
                                    sender_password=sender_password,
                                    recipient_email=restaurant_email,
                                    subject=subject_line,
                                    body=body,
                                    email_provider=email_provider
                                )
                                
                                if result['success']:
                                    st.success(f"✅ {result['message']}")
                                else:
                                    st.error(f"❌ {result['error']}")
                        else:
                            st.error("Failed to initialize agent")
    
    # Bulk email sending section
    st.markdown("### 📮 Bulk Email Sending")
    
    # Check which emails have restaurant addresses (including extracted ones)
    emails_with_addresses = []
    emails_needing_addresses = []
    
    for i, draft in enumerate(draft_emails):
        restaurant = draft['restaurant']
        
        # Check for manually entered email first
        restaurant_email = st.session_state.get(f'restaurant_email_{i}')
        
        # If no manual email, try to get extracted email
        if not restaurant_email:
            extracted_email = restaurant.get('email', '')
            if not extracted_email:
                agent = initialize_agent()
                if agent:
                    extracted_email = agent._find_restaurant_email(restaurant) or ''
            restaurant_email = extracted_email
        
        if restaurant_email:
            emails_with_addresses.append({
                'index': i,
                'restaurant': restaurant,
                'email': draft['email'],
                'restaurant_email': restaurant_email,
                'is_extracted': restaurant_email == restaurant.get('email', '') or 
                               (not st.session_state.get(f'restaurant_email_{i}') and restaurant_email)
            })
        else:
            emails_needing_addresses.append({
                'index': i,
                'restaurant': restaurant,
                'email': draft['email']
            })
    
    # Show status of email addresses
    col1, col2 = st.columns(2)
    
    with col1:
        if emails_with_addresses:
            st.markdown("**✅ Ready to Send:**")
            for email_info in emails_with_addresses:
                restaurant = email_info['restaurant']
                status_icon = "🤖" if email_info['is_extracted'] else "✏️"
                st.write(f"{status_icon} {restaurant.get('name', 'Restaurant')} → `{email_info['restaurant_email']}`")
    
    with col2:
        if emails_needing_addresses:
            st.markdown("**⚠️ Need Email Addresses:**")
            for email_info in emails_needing_addresses:
                restaurant = email_info['restaurant']
                st.write(f"❌ {restaurant.get('name', 'Restaurant')} - Enter email above")
    
    if emails_with_addresses:
        st.info(f"💡 Found {len(emails_with_addresses)} restaurants with email addresses (🤖 = auto-extracted, ✏️ = manually entered)")
        
        send_all = st.button(
            f"📤 Send All {len(emails_with_addresses)} Emails",
            type="primary",
            disabled=not all([sender_email, sender_password])
        )
        
        if send_all:
            agent = initialize_agent()
            if agent:
                with st.spinner("Sending all emails..."):
                    progress_bar = st.progress(0)
                    results = []
                    
                    for i, email_info in enumerate(emails_with_addresses):
                        # Get the edited email content from the text area widget
                        original_index = email_info['index']
                        edited_email_content = st.session_state.get(f"email_{original_index}", email_info['email'])
                        
                        # Extract subject and body from edited content
                        lines = edited_email_content.split('\n')
                        subject_line = None
                        body_lines = []
                        
                        for line in lines:
                            if line.startswith('Subject:'):
                                subject_line = line.replace('Subject:', '').strip()
                            elif subject_line is not None:
                                body_lines.append(line)
                        
                        if not subject_line:
                            subject_line = f"Table Reservation Request - {email_info['restaurant'].get('name', 'Restaurant')}"
                        
                        body = '\n'.join(body_lines).strip()
                        
                        result = agent.send_email(
                            sender_email=sender_email,
                            sender_password=sender_password,
                            recipient_email=email_info['restaurant_email'],
                            subject=subject_line,
                            body=body,
                            email_provider=email_provider
                        )
                        
                        results.append({
                            'restaurant': email_info['restaurant'].get('name', f'Restaurant {i+1}'),
                            'email': email_info['restaurant_email'],
                            'success': result['success'],
                            'message': result.get('message'),
                            'error': result.get('error')
                        })
                        
                        progress_bar.progress((i + 1) / len(emails_with_addresses))
                    
                    # Display results
                    st.markdown("#### 📊 Email Sending Results")
                    
                    success_count = sum(1 for r in results if r['success'])
                    
                    if success_count == len(results):
                        st.success(f"🎉 All {len(results)} emails sent successfully!")
                    elif success_count > 0:
                        st.warning(f"⚠️ {success_count} out of {len(results)} emails sent successfully")
                    else:
                        st.error("❌ No emails were sent successfully")
                    
                    # Detailed results
                    for result in results:
                        if result['success']:
                            st.success(f"✅ {result['restaurant']}: {result['message']}")
                        else:
                            st.error(f"❌ {result['restaurant']}: {result['error']}")
            else:
                st.error("Failed to initialize agent")
    else:
        st.info("💡 Enter restaurant email addresses above to enable bulk sending")

def main():
    """Main Streamlit application."""
    # Ensure os is available in function scope to prevent UnboundLocalError
    import os as _os
    
    # Header
    st.markdown('<div class="main-header">🎉 Event Agent Demo</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem; color: #666;">
        Extract event information, find nearby restaurants, and draft booking emails automatically!
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Check API status
        vertex_project_id = _os.getenv('VERTEX_PROJECT_ID') or st.secrets.get('VERTEX_PROJECT_ID', '')
        google_maps_api_key = _os.getenv('GOOGLE_MAPS_API_KEY') or st.secrets.get('GOOGLE_MAPS_API_KEY', '')
        
        # API Status
        st.markdown("### 🔑 API Status")
        if vertex_project_id and google_maps_api_key:
            st.success("✅ API credentials configured")
            st.caption(f"📍 Project: {vertex_project_id[:20]}...")
        else:
            st.error("❌ API credentials missing")
            st.caption("Contact administrator for setup")
        
        # Settings
        st.markdown("### ⚙️ Settings")
        party_size = st.number_input("Party Size", min_value=1, max_value=20, value=4)
        search_radius = st.slider("Restaurant Search Radius (km)", 0.5, 5.0, 2.0, 0.5)
        
        # Agent Status
        st.markdown("### 📊 Agent Status")
        if vertex_project_id and google_maps_api_key:
            st.success("✅ Ready to process events")
        else:
            st.error("❌ Agent unavailable - check API keys")
        
        # Email status
        st.markdown("### 📧 Email Status")
        sender_email = st.session_state.get('sender_email', '')
        if sender_email:
            st.success(f"✅ Email: {sender_email}")
        else:
            st.info("💡 Configure email to send booking requests")
        
        # Deployment info
        st.markdown("### ℹ️ Deployment Info")
        st.caption("🚀 Production Mode")
        st.caption("🔐 Secure API handling")
        
        # Help section
        with st.expander("❓ Need Help?"):
            st.markdown("""
            **How to use:**
            1. Enter an event URL above
            2. Click 'Process Event' 
            3. Review found restaurants
            4. Configure email settings
            5. Send booking requests
            
            **Issues?** Contact support
            """)
    
    # Main content area
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🌐 Event URL Input")
        event_url = st.text_input(
            "Enter Event URL",
            placeholder="https://example.com/event-page",
            help="Paste the URL of the event you want to analyze"
        )
        
        # Validate URL format
        if event_url:
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(event_url):
                st.warning("⚠️ Please enter a valid URL starting with http:// or https://")
                event_url = None
        
        # Check if API keys are available for button state
        api_keys_available = bool(
            (_os.getenv('VERTEX_PROJECT_ID') or st.secrets.get('VERTEX_PROJECT_ID', '')) and
            (_os.getenv('GOOGLE_MAPS_API_KEY') or st.secrets.get('GOOGLE_MAPS_API_KEY', ''))
        )
        
        process_button = st.button(
            "🚀 Process Event",
            type="primary",
            use_container_width=True,
            disabled=not (event_url and api_keys_available),
            help="Enter an event URL above to start processing" if not event_url else "Click to analyze the event and find restaurants"
        )
    
    # Process event when button is clicked
    if process_button and event_url:
        # Initialize agent
        agent = initialize_agent()
        print(agent)
        if not agent:
            st.error("Failed to initialize agent. Please check your API credentials.")
            return
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Extract event information
            status_text.text("🔍 Extracting event information...")
            progress_bar.progress(25)
            
            with st.spinner("Analyzing event page..."):
                event_info = agent.extract_event_info(event_url)
            
            if 'error' in event_info:
                st.error(f"Failed to extract event information: {event_info['error']}")
                return
            
            # Step 2: Search restaurants
            status_text.text("🍽️ Searching for nearby restaurants...")
            progress_bar.progress(50)
            
            with st.spinner("Finding restaurants..."):
                restaurants = agent.search_restaurants(event_info, radius=int(search_radius * 1000))
            
            # Step 2.5: Extract restaurant emails
            if restaurants:
                status_text.text("📧 Extracting restaurant contact information...")
                progress_bar.progress(60)
                
                with st.spinner("Finding restaurant emails..."):
                    for restaurant in restaurants:
                        if not restaurant.get('email'):
                            email = agent._find_restaurant_email(restaurant)
                            if email:
                                restaurant['email'] = email
            
            # Step 3: Draft emails
            status_text.text("📧 Drafting booking emails...")
            progress_bar.progress(75)
            
            draft_emails = []
            with st.spinner("Generating emails..."):
                for restaurant in restaurants[:5]:  # Top 5 restaurants
                    email = agent.draft_booking_email(event_info, restaurant, party_size)
                    draft_emails.append({
                        'restaurant': restaurant,
                        'email': email
                    })
            
            # Complete
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            
            # Store results in session state for email functionality
            st.session_state['event_info'] = event_info
            st.session_state['restaurants'] = restaurants
            st.session_state['draft_emails'] = draft_emails
            
            # Display results
            st.markdown('<div class="success-box">🎉 Event processing completed successfully!</div>', unsafe_allow_html=True)
            
            # Display event information
            display_event_info(event_info)
            
            # Display restaurants
            display_restaurants(restaurants)
            
            # Display draft emails with sending functionality
            display_draft_emails(draft_emails, event_info)
            
            # Summary
            st.markdown('<div class="sub-header">📊 Summary</div>', unsafe_allow_html=True)
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("Event Found", "✅" if event_info.get('title') else "❌")
            
            with summary_col2:
                st.metric("Restaurants Found", len(restaurants))
            
            with summary_col3:
                st.metric("Emails Drafted", len(draft_emails))
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)
        finally:
            progress_bar.empty()
            status_text.empty()
    
    # Display existing results if available (for when user returns to configure email)
    elif st.session_state.get('draft_emails'):
        st.markdown('<div class="info-box">📧 Previous results available - configure email settings to send booking requests</div>', unsafe_allow_html=True)
        
        event_info = st.session_state.get('event_info', {})
        restaurants = st.session_state.get('restaurants', [])
        draft_emails = st.session_state.get('draft_emails', [])
        
        display_event_info(event_info)
        display_restaurants(restaurants)
        display_draft_emails(draft_emails, event_info)
    
            # Sample URLs for testing
    with st.expander("🧪 Sample Event URLs for Testing"):
        st.markdown("""
        Try these sample URLs to test the agent:
        
        - **Tech Conferences:** 
          - `https://events.google.com/...`
          - `https://www.meetup.com/...`
          - `https://eventbrite.com/...`
        
        - **Academic Events:**
          - University conference pages
          - Academic symposium websites
        
        - **Public Events:**
          - City government event pages
          - Cultural center websites
          - Museum exhibition pages
        
        **⚠️ Privacy Notice:** Only use publicly available event URLs. Do not use private or restricted event pages.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666; margin-top: 2rem;">
        Built with ❤️ using Streamlit, Vertex AI, and Google Maps API<br>
        🤖 Intelligent Event Agent v2.0 | 📧 Email Integration | 🔐 Secure Deployment
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Privacy and usage notice
    with st.expander("🛡️ Privacy & Usage Policy"):
        st.markdown("""
        **Privacy Notice:**
        - This app processes event URLs you provide
        - Restaurant data is fetched from Google Places API
        - Email functionality uses your credentials securely
        - No personal data is stored permanently
        
        **Usage Guidelines:**
        - Use only publicly available event URLs
        - Respect website terms of service
        - Don't spam restaurants with booking requests
        - Use the tool responsibly and ethically
        
        **Data Security:**
        - API keys are handled securely via environment variables
        - Email credentials are processed locally
        - No sensitive data is logged or stored
        
        **Disclaimer:**
        This tool is for informational purposes. Always verify event details and restaurant availability independently.
        """)

if __name__ == "__main__":
    main() 