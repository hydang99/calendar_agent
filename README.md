# 🎉 Event Agent Framework

An intelligent agent framework that extracts event information from URLs, finds nearby restaurants, and drafts booking emails automatically - with direct email sending capabilities!

## ✨ Features

### 🔍 **Event Information Extraction**
- Scrapes event websites using Selenium and BeautifulSoup
- AI-powered information extraction using Google Vertex AI
- Extracts venue details, dates, times, agenda, and location information
- Fallback extraction methods for reliability

### 🍽️ **Restaurant Discovery**
- Finds nearby restaurants using Google Maps API
- Multiple search strategies (nearby search, text search, geocoding)
- Restaurant details including ratings, price levels, contact info
- Automatic email extraction from restaurant websites

### 📧 **Email Integration**
- Draft professional booking emails using AI
- Send emails directly from the web interface
- Support for Gmail, Outlook, and Yahoo
- Individual and bulk email sending
- Auto-populated restaurant emails when available

### 🎯 **Smart Web Interface**
- Modern Streamlit-based UI
- Real-time progress tracking
- Email configuration with validation
- Session state management
- Comprehensive error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Account (for Vertex AI)
- Google Maps API Key
- Chrome browser (for web scraping)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/event-agent-framework.git
cd event-agent-framework
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the project root:
```env
VERTEX_PROJECT_ID=your-google-cloud-project-id
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

4. **Run the application**
```bash
streamlit run streamlit_app.py
```

## 🔧 Configuration

### Google Cloud Setup
1. Create a Google Cloud Project
2. Enable Vertex AI API
3. Set up authentication (service account or gcloud CLI)

### Google Maps API Setup
1. Enable Places API and Maps JavaScript API
2. Create an API key with appropriate restrictions
3. Set up billing (required for Places API)

### Email Setup
For Gmail (recommended):
1. Enable 2-Factor Authentication
2. Generate App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use the 16-character app password in the interface

## 📖 Usage

1. **Configure API Keys**: Enter your Vertex AI Project ID and Google Maps API Key in the sidebar
2. **Enter Event URL**: Paste the URL of the event you want to analyze
3. **Process Event**: Click "🚀 Process Event" to extract information and find restaurants
4. **Configure Email**: Set up your email credentials in the Email Configuration section
5. **Send Emails**: Use individual or bulk sending to contact restaurants

### Supported Event Types
- Conferences and tech events
- Music festivals and concerts
- Business summits and networking events
- Sports events and tournaments
- Cultural events and exhibitions

## 🗂️ Project Structure

```
event-agent-framework/
├── event_agent.py          # Core agent functionality
├── streamlit_app.py         # Web interface
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
└── vietnam_school_chatbot/ # Additional chatbot module
```

## 🔌 API Integration

### Event Information Extraction
- **Web Scraping**: Selenium WebDriver with Chrome
- **AI Processing**: Google Vertex AI (Gemini models)
- **Fallback Methods**: BeautifulSoup + regex patterns

### Restaurant Discovery
- **Google Places API**: Nearby search and text search
- **Geocoding**: Location resolution and coordinates
- **Contact Discovery**: Website scraping for emails

### Email Sending
- **SMTP Support**: Gmail, Outlook, Yahoo
- **Security**: App passwords and TLS encryption
- **Error Handling**: Comprehensive validation and feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

See `requirements.txt` for full dependency list. Key dependencies:
- `streamlit>=1.28.0` - Web interface
- `google-cloud-aiplatform>=1.38.0` - AI processing
- `selenium>=4.15.0` - Web scraping
- `googlemaps>=4.10.0` - Maps integration
- `beautifulsoup4>=4.12.0` - HTML parsing

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues**:
```bash
# macOS
brew install chromedriver

# Or let the app auto-install it
```

**Authentication Errors**:
- For Gmail: Use App Password, not regular password
- For Google Cloud: Check service account permissions
- For Maps API: Verify billing is set up

**Email Encoding Errors**:
- Retype credentials manually (don't copy-paste)
- Check for hidden Unicode characters

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Vertex AI for intelligent processing
- Google Maps API for location services
- Streamlit for the amazing web framework
- Selenium for robust web scraping capabilities

---

**Built with ❤️ for automated event planning and restaurant booking** 