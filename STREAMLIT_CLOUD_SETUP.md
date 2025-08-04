# Streamlit Cloud Deployment Guide

## 🚀 Quick Deploy to Streamlit Cloud

### Step 1: Prepare Google Cloud Service Account

1. **Create a Service Account:**
   ```bash
   # Go to Google Cloud Console -> IAM & Admin -> Service Accounts
   # Or use CLI:
   gcloud iam service-accounts create event-agent-service \
       --description="Service account for Event Agent Streamlit app" \
       --display-name="Event Agent Service"
   ```

2. **Grant Required Permissions:**
   ```bash
   # Add Vertex AI permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:event-agent-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"
   
   # Add any other needed permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:event-agent-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/storage.objectViewer"
   ```

3. **Download Service Account Key:**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \
       --iam-account=event-agent-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

### Step 2: Set up Streamlit Secrets

1. **Fork/Push your repo to GitHub**
2. **Go to Streamlit Cloud** (https://share.streamlit.io)
3. **Connect your GitHub repo**
4. **Add these secrets in Streamlit Cloud:**

   ```toml
   # In Streamlit Cloud -> Settings -> Secrets
   VERTEX_PROJECT_ID = "your-actual-project-id"
   GOOGLE_MAPS_API_KEY = "your-actual-google-maps-key"
   VERTEX_LOCATION = "us-east1"
   
   # Paste the ENTIRE content of your service-account-key.json here:
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "key-id-here"
   private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
   client_email = "event-agent-service@your-project-id.iam.gserviceaccount.com"
   client_id = "client-id-here"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/event-agent-service%40your-project-id.iam.gserviceaccount.com"
   ```

### Step 3: Update Code for Service Account Authentication

Your app will need a small modification to use the service account:

```python
# In streamlit_app.py, add at the top after load_dotenv():
import json
from google.oauth2 import service_account

# Set up Google Cloud authentication for Streamlit Cloud
if "gcp_service_account" in st.secrets:
    # Running on Streamlit Cloud
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
    
    # Write credentials to a temporary file for Vertex AI
    with open("service-account-key.json", "w") as f:
        json.dump(dict(st.secrets["gcp_service_account"]), f)
```

### Step 4: Deploy!

1. **Push to GitHub**
2. **Deploy on Streamlit Cloud**
3. **Share the URL** - users can access immediately!

## 🎯 **User Experience:**

**For your users:**
- ✅ Visit `https://your-app-name.streamlit.app`
- ✅ Enter event URL
- ✅ Click "Process Event"
- ✅ Get restaurants and email draft instantly!

**No authentication required for users! 🎉**

## 🔒 **Security Notes:**

- ✅ API keys are secure in Streamlit secrets
- ✅ Service account has minimal required permissions
- ✅ Users never see or need credentials
- ✅ All authentication happens server-side

## 📝 **Alternative: Simple API Key Mode**

If you want to avoid service accounts, you can also:

1. Enable Google Cloud APIs with API key authentication
2. Just use the environment variables approach
3. Set `GOOGLE_APPLICATION_CREDENTIALS` to use your downloaded service account key

The service account approach is more secure for production!