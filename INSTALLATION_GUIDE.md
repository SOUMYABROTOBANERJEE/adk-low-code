# Google ADK No-Code Platform - Installation Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Google Cloud Service Account** JSON file (`svcacct.json`)
3. **Git** (for cloning the repository)

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd adk-low-code
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Service Account Setup
1. Download your Google Cloud service account JSON file
2. Rename it to `svcacct.json`
3. Place it in the project root directory

### 5. Start the Platform
```bash
python app.py
```

## Common Issues and Solutions

### Issue: "OpenTelemetry not available"
**Cause**: Missing OpenTelemetry dependencies

**Solution**:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-gcp-trace opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests
```

### Issue: "Google ADK not available"
**Cause**: Missing Google ADK package

**Solution**:
```bash
pip install google-adk
```

### Issue: "Google GenAI not available"
**Cause**: Missing Google GenAI package

**Solution**:
```bash
pip install google-genai
```

### Issue: "Langfuse not available"
**Cause**: Missing Langfuse package

**Solution**:
```bash
pip install langfuse
```

### Issue: "Firestore not available"
**Cause**: Missing Google Cloud Firestore dependencies

**Solution**:
```bash
pip install google-cloud-firestore google-auth google-auth-oauthlib google-auth-httplib2
```

## Complete Dependency Installation

If you encounter multiple missing dependencies, run:

```bash
pip install -r requirements.txt
```

If that doesn't work, install each dependency individually:

```bash
# Core dependencies
pip install fastapi uvicorn python-dotenv pydantic

# Google ADK and GenAI
pip install google-adk google-genai

# Google Cloud services
pip install google-cloud-firestore google-auth google-auth-oauthlib google-auth-httplib2

# OpenTelemetry for Cloud Trace
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-gcp-trace opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests

# Langfuse for observability
pip install langfuse

# Additional dependencies
pip install aiofiles jinja2 websockets requests
```

## Verification

After installation, verify everything is working:

1. **Check platform health**:
   ```bash
   curl http://localhost:8083/api/health
   ```

2. **Check service account authentication**:
   ```bash
   curl http://localhost:8083/api/config
   ```

3. **Check Cloud Trace status**:
   ```bash
   curl http://localhost:8083/api/trace-info
   ```

## Environment Variables

The platform uses service account authentication, so no API keys are needed. However, you can set these optional environment variables:

```bash
# Optional: Langfuse configuration
export LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
export LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Optional: Server configuration
export HOST="0.0.0.0"
export PORT="8083"
```

## Troubleshooting

### Port Already in Use
If port 8083 is already in use:
```bash
# Find and kill the process
lsof -ti:8083 | xargs kill -9
```

### Service Account Issues
Make sure your `svcacct.json` file:
1. Is in the project root directory
2. Has the correct permissions
3. Contains valid service account credentials
4. Has the necessary roles (Firestore, Cloud Trace, etc.)

### Firestore Index Issues
If you see Firestore index errors, the platform will automatically create the required indexes. Wait a few minutes for them to be built.

## Support

If you continue to have issues:
1. Check the logs in the terminal
2. Verify all dependencies are installed
3. Ensure the service account file is correct
4. Check that your Google Cloud project has the necessary APIs enabled
