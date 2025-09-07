# 🔥 Firestore Migration Guide

## Overview

The Google ADK No-Code Platform has been successfully migrated from SQLite to Google Cloud Firestore for production deployment. This migration ensures:

- ✅ **Scalability**: Handles production workloads
- ✅ **Reliability**: Google Cloud infrastructure
- ✅ **Security**: Service account authentication
- ✅ **Compatibility**: All existing functionality preserved

## 🏗️ Architecture Changes

### Before (SQLite)
```
Local SQLite Database
├── agents table
├── tools table
├── projects table
├── chat_sessions table
└── users table
```

### After (Firestore)
```
Google Cloud Firestore
└── agent-genie collection
    ├── tools/items/ (subcollection)
    ├── agents/items/ (subcollection)
    ├── projects/items/ (subcollection)
    ├── chat_sessions/items/ (subcollection)
    ├── users/items/ (subcollection)
    └── user_sessions/items/ (subcollection)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Firestore Collections
```bash
python migrate_to_firestore.py
```

### 3. Start the Platform
```bash
python app.py
```

The platform will automatically detect the service account file and use Firestore in production mode.

## 📁 File Structure

### New Files Added
- `src/google2/adk1/nocode/firestore_manager.py` - Firestore database manager
- `migrate_to_firestore.py` - Collection initialization script
- `test_firestore_migration.py` - Migration verification tests

### Modified Files
- `main.py` - Updated to use Firestore manager
- `requirements.txt` - Added Firestore dependencies
- `Dockerfile` - Added service account configuration
- `cloudbuild.yaml` - Added service account for Cloud Run

## 🔧 Configuration

### Service Account
The platform uses the service account file `svcacct.json` for authentication:

```json
{
    "type": "service_account",
    "project_id": "tsl-generative-ai",
    "private_key_id": "...",
    "private_key": "...",
    "client_email": "svc-generative-ai@tsl-generative-ai.iam.gserviceaccount.com",
    ...
}
```

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account file
- `GOOGLE_API_KEY` - Google API key for ADK services

## 🧪 Testing

### Run Migration Tests
```bash
python test_firestore_migration.py
```

This will test:
- ✅ Health endpoint
- ✅ Tool creation/retrieval
- ✅ Agent creation/retrieval
- ✅ Project creation/retrieval
- ✅ Chat functionality
- ✅ Data listing
- ✅ Cleanup operations

### Manual Testing
1. Start the platform: `python app.py`
2. Open browser: `http://127.0.0.1:8083`
3. Test all functionality through the UI
4. Verify data persistence in Firestore console

## 🚀 Deployment

### Local Development
- Uses SQLite database (fallback)
- No service account required
- Perfect for development and testing

### Production Deployment
- Uses Firestore database
- Requires service account file
- Deployed to Google Cloud Run

### Deploy to Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or use the provided script
./deploy.sh
```

## 📊 Firestore Collection Structure

### Main Collection: `agent-genie`

#### Tools Subcollection (`tools/items/`)
```json
{
    "id": "tool_id",
    "name": "Tool Name",
    "description": "Tool description",
    "tool_type": "function|api|webhook",
    "function_code": "Python code",
    "api_endpoint": "API URL",
    "webhook_url": "Webhook URL",
    "parameters": {...},
    "tags": [...],
    "is_enabled": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

#### Agents Subcollection (`agents/items/`)
```json
{
    "id": "agent_id",
    "name": "Agent Name",
    "description": "Agent description",
    "agent_type": "llm|workflow|hybrid",
    "system_prompt": "System prompt",
    "tools": [...],
    "sub_agents": {...},
    "model_settings": {...},
    "workflow_config": {...},
    "ui_config": {...},
    "tags": [...],
    "is_enabled": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

#### Projects Subcollection (`projects/items/`)
```json
{
    "id": "project_id",
    "name": "Project Name",
    "description": "Project description",
    "agents": [...],
    "tools": [...],
    "config": {...},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

#### Chat Sessions Subcollection (`chat_sessions/items/`)
```json
{
    "id": "session_id",
    "agent_id": "agent_id",
    "messages": [...],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

#### Users Subcollection (`users/items/`)
```json
{
    "id": "user_id",
    "email": "user@example.com",
    "password_hash": "hashed_password",
    "is_active": true,
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

#### User Sessions Subcollection (`user_sessions/items/`)
```json
{
    "id": "session_id",
    "user_id": "user_id",
    "session_token": "token",
    "expires_at": "2024-01-01T00:00:00",
    "last_activity": "2024-01-01T00:00:00"
}
```

## 🔒 Security

### Service Account Permissions
The service account needs the following IAM roles:
- `Cloud Datastore User` - For Firestore access
- `Cloud Run Invoker` - For Cloud Run deployment
- `Storage Object Viewer` - For Cloud Build artifacts

### Data Security
- All data is encrypted at rest in Firestore
- Service account authentication
- No sensitive data in code
- Environment variables for secrets

## 📈 Monitoring

### Firestore Metrics
Monitor in Google Cloud Console:
- Document reads/writes
- Storage usage
- Query performance
- Error rates

### Application Metrics
- Response times
- Error rates
- User sessions
- Agent executions

## 🛠️ Troubleshooting

### Common Issues

#### 1. Service Account Not Found
```
Error: Service account file not found: svcacct.json
```
**Solution**: Ensure `svcacct.json` is in the project root

#### 2. Firestore Permission Denied
```
Error: Permission denied accessing Firestore
```
**Solution**: Check service account IAM roles

#### 3. Collection Not Found
```
Error: Collection agent-genie not found
```
**Solution**: Run `python migrate_to_firestore.py`

#### 4. Import Errors
```
Error: google-cloud-firestore not found
```
**Solution**: Run `pip install -r requirements.txt`

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Migration Benefits

### Performance
- **Scalability**: Handles millions of documents
- **Speed**: Sub-second query responses
- **Concurrency**: Multiple users simultaneously

### Reliability
- **Uptime**: 99.95% SLA
- **Backup**: Automatic backups
- **Recovery**: Point-in-time recovery

### Cost
- **Pay-per-use**: Only pay for what you use
- **No maintenance**: Managed service
- **Predictable**: Transparent pricing

## 📚 Additional Resources

- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Service Account Guide](https://cloud.google.com/iam/docs/service-accounts)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)

## 🎯 Next Steps

1. **Deploy to Production**: Use Cloud Build to deploy
2. **Monitor Performance**: Set up monitoring and alerts
3. **Scale as Needed**: Firestore scales automatically
4. **Backup Strategy**: Configure backup policies
5. **Security Review**: Regular security audits

---

**Migration Status**: ✅ **COMPLETE**
**Production Ready**: ✅ **YES**
**All Functionality Preserved**: ✅ **CONFIRMED**
