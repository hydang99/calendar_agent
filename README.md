# 🎉 Event Agent Framework

An intelligent agent that extracts event information from URLs, finds nearby restaurants, drafts booking emails, and sends them directly from a web interface.

## ✨ Features

- **🔍 Event Information Extraction**: Automatically scrapes event details from URLs using Selenium and AI
- **🍽️ Restaurant Discovery**: Finds nearby restaurants using Google Maps API
- **📧 Email Generation**: AI-powered email drafting for restaurant reservations
- **📤 Direct Email Sending**: Send emails directly from the web interface
- **🤖 Smart Email Extraction**: Automatically finds restaurant contact emails
- **🎨 Beautiful UI**: Modern Streamlit interface with progress tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud Project (for Vertex AI)
- Google Maps API Key
- Email account with app password (Gmail recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd agent_langchain
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
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
1. Enable Vertex AI API in your Google Cloud Console
2. Set up authentication (service account or local credentials)

### Google Maps API
1. Enable Places API and Geocoding API
2. Generate an API key with appropriate restrictions

### Email Setup
For Gmail (recommended):
1. Enable 2-Factor Authentication
2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use the 16-character app password in the app

## 📖 Usage

1. **Configure API Keys**: Enter your credentials in the sidebar
2. **Enter Event URL**: Paste the URL of the event you want to analyze
3. **Process Event**: Click "🚀 Process Event" to extract information
4. **Review Results**: Check extracted event details and nearby restaurants
5. **Configure Email**: Set up your sending email credentials
6. **Send Emails**: Individual or bulk email sending to restaurants

## 🏗️ Project Structure

```
agent_langchain/
├── event_agent.py          # Main agent logic
├── streamlit_app.py        # Web interface
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
├── testing.ipynb         # Development notebook
├── test_*.py             # Test files
├── run_demo.py           # Demo runner
└── vietnam_school_chatbot/ # Additional chatbot module
```

## 🎯 Core Components

### EventAgent Class
- **Event Extraction**: Scrapes and processes event information
- **Restaurant Search**: Integrates with Google Maps API
- **Email Generation**: AI-powered email drafting
- **Email Sending**: SMTP integration with multiple providers

### Streamlit Interface
- **Modern UI**: Clean, responsive design
- **Real-time Processing**: Progress tracking and status updates
- **Email Management**: Individual and bulk sending capabilities
- **Configuration**: Easy API key and email setup

## 🔒 Security Features

- **Environment Variables**: Sensitive data protected
- **App Passwords**: Secure email authentication
- **Input Sanitization**: Protection against encoding issues
- **Error Handling**: Comprehensive error management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Streamlit**: For the amazing web framework
- **Google Cloud**: For Vertex AI and Maps APIs
- **LangChain**: For AI integration capabilities

## 🆘 Support

For issues and questions:
1. Check the existing issues
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

---

**Built with ❤️ using Python, Streamlit, and AI** 