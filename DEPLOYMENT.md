# 🚀 Event Agent Deployment Guide

This guide will help you deploy the Event Agent to Streamlit Cloud or other platforms securely.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Project** with Vertex AI enabled
2. **Google Maps API Key** with Places API enabled
3. **GitHub Repository** (for Streamlit Cloud deployment)

## 🔑 API Setup

### 1. Google Cloud Vertex AI Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the Vertex AI API:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```
4. Note your **Project ID** (you'll need this)

### 2. Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services > Credentials
3. Create an API key
4. Enable the following APIs:
   - Places API
   - Maps JavaScript API
   - Geocoding API
5. Restrict the API key (recommended):
   - Application restrictions: HTTP referrers
   - API restrictions: Select only the APIs you enabled

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Recommended)

#### Step 1: Prepare Repository
1. Push your code to GitHub
2. Ensure `.gitignore` excludes secrets:
   ```gitignore
   .env
   .streamlit/secrets.toml
   *.json
   ```

#### Step 2: Deploy to Streamlit Cloud
1. Go to [Streamlit Cloud](https://share.streamlit.io)
2. Connect your GitHub account
3. Click "New app"
4. Select your repository and `streamlit_app.py`
5. Click "Deploy"

#### Step 3: Configure Secrets
1. In your Streamlit Cloud app, click "Settings" → "Secrets"
2. Add your API credentials:
   ```toml
   VERTEX_PROJECT_ID = "your-google-cloud-project-id"
   GOOGLE_MAPS_API_KEY = "your-google-maps-api-key"
   ```
3. Click "Save"

#### Step 4: Configure Google Cloud Authentication
For Vertex AI authentication, you have two options:

**Option A: Service Account (Recommended for production)**
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. In Streamlit Cloud secrets, add:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
   client_email = "your-service-account@your-project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
   ```

**Option B: Application Default Credentials**
- This works automatically if your Streamlit Cloud has Google Cloud integration

### Option 2: Other Cloud Platforms

#### Heroku
1. Create `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. Set environment variables in Heroku dashboard
3. Deploy using Git or GitHub integration

#### Google Cloud Run
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   CMD streamlit run streamlit_app.py --server.port=8080 --server.address=0.0.0.0
   ```
2. Build and deploy:
   ```bash
   gcloud run deploy event-agent --source . --platform managed --region us-central1 --allow-unauthenticated
   ```

### Option 3: Local Development

1. Copy environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your API keys:
   ```bash
   VERTEX_PROJECT_ID=your-google-cloud-project-id
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   ```

3. Run locally:
   ```bash
   streamlit run streamlit_app.py
   ```

## 🔒 Security Best Practices

### 1. API Key Security
- ✅ **Never** commit API keys to version control
- ✅ Use environment variables or secrets management
- ✅ Restrict API keys to specific domains/IPs
- ✅ Monitor API usage and set quotas

### 2. Access Control
- Consider adding authentication for sensitive deployments
- Use HTTPS in production
- Monitor access logs

### 3. Error Handling
- The app gracefully handles missing API keys
- Users see helpful error messages without exposing sensitive info

## 🧪 Testing Your Deployment

1. **Test API Configuration**:
   - Check the sidebar shows "✅ API credentials configured"
   - Verify the agent status shows "✅ Ready to process events"

2. **Test Event Processing**:
   - Try a sample event URL
   - Verify event information extraction works
   - Check restaurant search functionality

3. **Test Email Integration**:
   - Configure your email settings
   - Test email validation
   - Try sending a sample booking email

## 🚨 Troubleshooting

### Common Issues

**"API credentials missing"**
- Check environment variables are set correctly
- Verify Streamlit Cloud secrets are saved
- Ensure no typos in variable names

**"Failed to initialize agent"**
- Check Google Cloud Project ID is correct
- Verify Vertex AI is enabled in your project
- Check service account permissions

**"Restaurant search failed"**
- Verify Google Maps API key is correct
- Check Places API is enabled
- Verify API key restrictions allow your domain

**"Email sending failed"**
- Check email provider settings
- For Gmail, use App Passwords, not regular password
- Verify 2FA is enabled for Gmail

### Getting Help

- Check the [Streamlit documentation](https://docs.streamlit.io)
- Review [Google Cloud Vertex AI docs](https://cloud.google.com/vertex-ai/docs)
- Check [Google Maps Platform docs](https://developers.google.com/maps/documentation)

## 📊 Monitoring

- Monitor API usage in Google Cloud Console
- Check Streamlit Cloud logs for errors
- Set up billing alerts for API usage

## 🔄 Updates

To update your deployment:
1. Push changes to your GitHub repository
2. Streamlit Cloud will automatically redeploy
3. Check the deployment logs for any issues

---

**🎉 Congratulations!** Your Event Agent is now securely deployed and ready for public use!