# 🎉 Event Agent - Intelligent Event Processing & Restaurant Booking

An AI-powered agent that extracts event information from URLs, finds nearby restaurants, and drafts booking emails automatically.

## ✨ Features

- 🔍 **Smart Event Extraction**: Extracts event details from any public URL
- 🍽️ **Restaurant Discovery**: Finds nearby restaurants using Google Places API
- 📧 **Email Automation**: Drafts and sends booking emails automatically
- 🌐 **Web Interface**: Beautiful Streamlit interface for easy interaction
- 🔐 **Secure Deployment**: Production-ready with proper API key handling

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd agent_langchain
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy the environment template:
```bash
cp env.template .env
```

Edit `.env` with your actual API keys:
```env
VERTEX_PROJECT_ID=your-google-cloud-project-id
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 4. Run Locally
```bash
streamlit run streamlit_app.py
```

## 🌐 Deploy to Streamlit Cloud

For public deployment, see our detailed [DEPLOYMENT.md](DEPLOYMENT.md) guide.

**Quick Steps:**
1. Push to GitHub
2. Deploy on [Streamlit Cloud](https://share.streamlit.io)
3. Add secrets in app settings:
   ```toml
   VERTEX_PROJECT_ID = "your-project-id"
   GOOGLE_MAPS_API_KEY = "your-api-key"
   ```

## 🔧 API Setup Required

### Google Cloud Vertex AI
1. Create a Google Cloud project
2. Enable Vertex AI API
3. Set up authentication

### Google Maps API
1. Enable Places API, Geocoding API
2. Create an API key
3. Configure restrictions (optional)

## 📱 How to Use

1. **Enter Event URL**: Paste any public event URL
2. **Process Event**: AI extracts event details and location
3. **Review Restaurants**: Browse nearby restaurant options
4. **Configure Email**: Set up your email credentials
5. **Send Bookings**: Draft and send booking requests

## 🛡️ Security Features

- ✅ API keys handled via environment variables
- ✅ No sensitive data in version control
- ✅ Input validation and sanitization
- ✅ Secure email handling
- ✅ Production-ready configuration

## 📋 Requirements

- Python 3.8+
- Google Cloud Project with Vertex AI
- Google Maps API key
- Chrome/Chromium (for web scraping)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Review the troubleshooting section for common issues
- Open an issue for bugs or feature requests

---

**Made with ❤️ using Streamlit, Vertex AI, and Google Maps API**