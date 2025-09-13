# 🚀 Google ADK No-Code Platform

> **Production-ready AI agent development platform with Google Cloud integration**

A comprehensive, enterprise-grade platform for building, deploying, and managing AI agents using Google's Agent Development Kit (ADK). Features service account authentication, Firestore database, Cloud Trace observability, and complete user ID tracking.

## 📊 **Platform Status**

| **Component** | **Status** | **Version** | **Production Ready** |
|---------------|------------|-------------|----------------------|
| **Core Platform** | ✅ Complete | 2.0 | ✅ Yes |
| **Firestore Integration** | ✅ Complete | 2.0 | ✅ Yes |
| **Cloud Trace** | ✅ Complete | 2.0 | ✅ Yes |
| **Service Account Auth** | ✅ Complete | 2.0 | ✅ Yes |
| **User Management** | ✅ Complete | 2.0 | ✅ Yes |
| **Agent Management** | ✅ Complete | 2.0 | ✅ Yes |
| **Tool System** | ✅ Complete | 2.0 | ✅ Yes |

---

## 🏗️ **System Architecture**

### **High-Level Architecture**

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI]
        API[REST API Client]
        WS[WebSocket Client]
    end
    
    subgraph "Application Layer"
        FASTAPI[FastAPI Server]
        AUTH[Auth Service]
        ADK[ADK Service]
        TRACE[Trace Service]
    end
    
    subgraph "Data Layer"
        FIRESTORE[(Google Firestore)]
        SESSIONS[Session Storage]
    end
    
    subgraph "Google Cloud Services"
        GCP[Google Cloud Platform]
        ADK_SDK[Google ADK SDK]
        GENAI[Google GenAI]
        TRACE_SVC[Cloud Trace]
    end
    
    UI --> FASTAPI
    API --> FASTAPI
    WS --> FASTAPI
    
    FASTAPI --> AUTH
    FASTAPI --> ADK
    FASTAPI --> TRACE
    
    AUTH --> FIRESTORE
    ADK --> FIRESTORE
    ADK --> ADK_SDK
    ADK --> GENAI
    TRACE --> TRACE_SVC
    
    ADK_SDK --> GCP
    GENAI --> GCP
    TRACE_SVC --> GCP
```

### **Detailed Component Architecture**

```mermaid
graph LR
    subgraph "Frontend Layer"
        HTML[HTML Templates]
        CSS[Tailwind CSS]
        JS[JavaScript ES6+]
        WS_CLIENT[WebSocket Client]
    end
    
    subgraph "API Layer"
        REST[REST Endpoints]
        WS_SERVER[WebSocket Server]
        MIDDLEWARE[CORS Middleware]
        VALIDATION[Pydantic Validation]
    end
    
    subgraph "Service Layer"
        MAIN[Main Service]
        ADK_SVC[ADK Service]
        AUTH_SVC[Auth Service]
        DB_SVC[Database Service]
        LANG_SVC[Langfuse Service]
        TRACE_SVC[Trace Service]
    end
    
    subgraph "Data Models"
        AGENT_MODEL[Agent Models]
        TOOL_MODEL[Tool Models]
        USER_MODEL[User Models]
        SESSION_MODEL[Session Models]
    end
    
    subgraph "External Services"
        FIRESTORE[(Firestore)]
        CLOUD_TRACE[Cloud Trace]
        LANGFUSE[Langfuse]
        GOOGLE_ADK[Google ADK]
        GOOGLE_GENAI[Google GenAI]
    end
    
    HTML --> REST
    CSS --> REST
    JS --> REST
    WS_CLIENT --> WS_SERVER
    
    REST --> MAIN
    WS_SERVER --> MAIN
    MIDDLEWARE --> MAIN
    VALIDATION --> MAIN
    
    MAIN --> ADK_SVC
    MAIN --> AUTH_SVC
    MAIN --> DB_SVC
    MAIN --> LANG_SVC
    MAIN --> TRACE_SVC
    
    ADK_SVC --> AGENT_MODEL
    AUTH_SVC --> USER_MODEL
    DB_SVC --> SESSION_MODEL
    
    DB_SVC --> FIRESTORE
    TRACE_SVC --> CLOUD_TRACE
    LANG_SVC --> LANGFUSE
    ADK_SVC --> GOOGLE_ADK
    ADK_SVC --> GOOGLE_GENAI
```

---

## 🔥 **Firestore Database Architecture**

### **Collection Structure**

```mermaid
graph TD
    ROOT[agent-genie Collection]
    
    ROOT --> TOOLS[tools/items/]
    ROOT --> AGENTS[agents/items/]
    ROOT --> PROJECTS[projects/items/]
    ROOT --> CHAT_SESSIONS[chat_sessions/items/]
    ROOT --> USERS[users/items/]
    ROOT --> USER_SESSIONS[user_sessions/items/]
    
    TOOLS --> TOOL_DOC[Tool Document]
    AGENTS --> AGENT_DOC[Agent Document]
    PROJECTS --> PROJECT_DOC[Project Document]
    CHAT_SESSIONS --> CHAT_DOC[Chat Session Document]
    USERS --> USER_DOC[User Document]
    USER_SESSIONS --> SESSION_DOC[User Session Document]
    
    subgraph "Tool Document Structure"
        TOOL_DOC --> TOOL_FIELDS[id, name, description, tool_type, function_code, tags, is_enabled, created_at, updated_at]
    end
    
    subgraph "Agent Document Structure"
        AGENT_DOC --> AGENT_FIELDS[id, name, description, agent_type, system_prompt, tools, sub_agents, model_settings, workflow_config, ui_config, tags, is_enabled, created_at, updated_at]
    end
    
    subgraph "User Document Structure"
        USER_DOC --> USER_FIELDS[id, email, password_hash, is_active, metadata, created_at, updated_at]
    end
```

### **Data Flow Architecture**

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant FirestoreManager
    participant Firestore
    participant ADKService
    participant GoogleADK
    
    Client->>FastAPI: POST /api/agents
    FastAPI->>FirestoreManager: create_agent(agent_data)
    FirestoreManager->>Firestore: Save agent document
    Firestore-->>FirestoreManager: Document created
    FirestoreManager-->>FastAPI: Agent created
    FastAPI-->>Client: Success response
    
    Client->>FastAPI: POST /api/chat/{agent_id}
    FastAPI->>ADKService: execute_agent(agent_id, message, user_id)
    ADKService->>GoogleADK: Run agent with trace
    GoogleADK-->>ADKService: Agent response
    ADKService->>FirestoreManager: save_chat_session(session_data)
    FirestoreManager->>Firestore: Save chat session
    ADKService-->>FastAPI: Execution result
    FastAPI-->>Client: Chat response
```

---

## 🔍 **Cloud Trace Integration Architecture**

### **Tracing Flow**

```mermaid
graph TD
    REQUEST[HTTP Request] --> FASTAPI_TRACE[FastAPI Trace]
    FASTAPI_TRACE --> AGENT_EXEC[Agent Execution Trace]
    
    AGENT_EXEC --> USER_SPAN[User ID Span]
    AGENT_EXEC --> SESSION_SPAN[Session Span]
    AGENT_EXEC --> AGENT_SPAN[Agent Run Span]
    
    AGENT_SPAN --> TOOL_SPAN[Tool Call Spans]
    AGENT_SPAN --> LLM_SPAN[LLM Call Spans]
    AGENT_SPAN --> RESPONSE_SPAN[Response Generation Span]
    
    TOOL_SPAN --> CLOUD_TRACE[Cloud Trace]
    LLM_SPAN --> CLOUD_TRACE
    RESPONSE_SPAN --> CLOUD_TRACE
    USER_SPAN --> CLOUD_TRACE
    SESSION_SPAN --> CLOUD_TRACE
    
    CLOUD_TRACE --> TRACE_EXPLORER[Trace Explorer]
    TRACE_EXPLORER --> MONITORING[Monitoring Dashboard]
```

### **Span Hierarchy**

```mermaid
graph LR
    ROOT_SPAN[adk-platform.agent_execution.{agent_id}.{user_id}]
    
    ROOT_SPAN --> USER_CONTEXT[User Context Span]
    ROOT_SPAN --> SESSION_MGMT[Session Management Span]
    ROOT_SPAN --> AGENT_RUN[Agent Run Span]
    
    USER_CONTEXT --> USER_ATTRS[user.id, user.session, timestamp]
    SESSION_MGMT --> SESSION_ATTRS[session.id, session.state, last_activity]
    AGENT_RUN --> AGENT_ATTRS[agent.id, agent.type, model, prompt_length]
    
    AGENT_RUN --> TOOL_CALLS[Tool Call Spans]
    AGENT_RUN --> LLM_CALLS[LLM Call Spans]
    AGENT_RUN --> RESPONSE_GEN[Response Generation Span]
    
    TOOL_CALLS --> TOOL_ATTRS[tool.id, tool.name, execution_time, result]
    LLM_CALLS --> LLM_ATTRS[model, tokens, response_time, response_length]
    RESPONSE_GEN --> RESPONSE_ATTRS[response_length, generation_time, success]
```

---

## 🔐 **Authentication & Security Architecture**

### **Service Account Authentication Flow**

```mermaid
sequenceDiagram
    participant App
    participant ServiceAccount
    participant GoogleCloud
    participant Firestore
    participant CloudTrace
    
    App->>ServiceAccount: Load svcacct.json
    ServiceAccount->>GoogleCloud: Authenticate with service account
    GoogleCloud-->>ServiceAccount: Access token
    ServiceAccount-->>App: Authenticated client
    
    App->>Firestore: Database operations
    Firestore->>GoogleCloud: Validate service account
    GoogleCloud-->>Firestore: Authorized
    Firestore-->>App: Data response
    
    App->>CloudTrace: Trace operations
    CloudTrace->>GoogleCloud: Validate service account
    GoogleCloud-->>CloudTrace: Authorized
    CloudTrace-->>App: Trace data
```

### **User Session Management**

```mermaid
graph TD
    LOGIN[User Login] --> AUTH_SERVICE[Auth Service]
    AUTH_SERVICE --> VALIDATE[Validate Credentials]
    VALIDATE --> HASH_CHECK[Check Password Hash]
    HASH_CHECK --> SESSION_CREATE[Create Session Token]
    SESSION_CREATE --> FIRESTORE_SAVE[Save to Firestore]
    FIRESTORE_SAVE --> TOKEN_RETURN[Return Session Token]
    
    REQUEST[API Request] --> TOKEN_CHECK[Check Session Token]
    TOKEN_CHECK --> FIRESTORE_LOOKUP[Lookup Session in Firestore]
    FIRESTORE_LOOKUP --> EXPIRY_CHECK[Check Expiry]
    EXPIRY_CHECK --> USER_CONTEXT[Set User Context]
    USER_CONTEXT --> TRACE_USER[Trace with User ID]
```

---

## 🚀 **Quick Start Guide**

### **Prerequisites**
- Python 3.8+
- Google Cloud Service Account (`svcacct.json`)
- Git

### **Installation**

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd adk-low-code
   ```

2. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Service Account Setup**
   - Download your Google Cloud service account JSON file
   - Rename it to `svcacct.json`
   - Place it in the project root directory

5. **Start Platform**
   ```bash
   python app.py
   ```

6. **Access Platform**
   - Web UI: `http://127.0.0.1:8083`
   - API Docs: `http://127.0.0.1:8083/docs`

---

## 🧪 **Testing & Verification**

### **Health Checks**
```bash
# Platform health
curl http://127.0.0.1:8083/api/health

# Service account authentication
curl http://127.0.0.1:8083/api/config

# Cloud Trace status
curl http://127.0.0.1:8083/api/trace-info
```

### **Comprehensive Testing**
```bash
# Test agent execution
curl -X POST http://127.0.0.1:8083/api/chat/sample_agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test_user", "session_id": "test_session"}'

# Test tool creation
curl -X POST http://127.0.0.1:8083/api/tools \
  -H "Content-Type: application/json" \
  -d '{"id": "test_tool", "name": "Test Tool", "description": "A test tool", "tool_type": "function"}'

# Test agent creation
curl -X POST http://127.0.0.1:8083/api/agents \
  -H "Content-Type: application/json" \
  -d '{"id": "test_agent", "name": "Test Agent", "description": "A test agent", "agent_type": "llm"}'
```

---

## 📊 **API Reference**

### **Core Endpoints**

| **Endpoint** | **Method** | **Description** |
|--------------|------------|-----------------|
| `/api/health` | GET | Platform health check |
| `/api/config` | GET | Configuration and auth status |
| `/api/trace-info` | GET | Cloud Trace status |
| `/api/agents` | GET/POST | List/create agents |
| `/api/tools` | GET/POST | List/create tools |
| `/api/chat/{agent_id}` | POST | Chat with agent |
| `/api/auth/login` | POST | User authentication |
| `/api/auth/register` | POST | User registration |

### **Chat API Example**
```http
POST /api/chat/sample_agent
Content-Type: application/json

{
  "message": "What is 15 + 25?",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

**Response:**
```json
{
  "success": true,
  "response": "15 + 25 = 40",
  "execution_time": 1.23,
  "user_id": "user_123",
  "session_id": "session_456",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Service Account (Required)
GOOGLE_APPLICATION_CREDENTIALS=svcacct.json

# Optional: Langfuse Configuration
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8083
```

### **Service Account Permissions**
The service account needs these IAM roles:
- `Cloud Datastore User` - For Firestore access
- `Cloud Trace Agent` - For Cloud Trace writing
- `Cloud Run Invoker` - For Cloud Run deployment

---

## 🚀 **Deployment**

### **Google Cloud Run Deployment**
```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Manual deployment
docker build -t gcr.io/PROJECT_ID/adk-platform .
docker push gcr.io/PROJECT_ID/adk-platform
gcloud run deploy adk-platform \
  --image gcr.io/PROJECT_ID/adk-platform \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### **Docker Configuration**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY svcacct.json .
ENV GOOGLE_APPLICATION_CREDENTIALS=svcacct.json
EXPOSE 8083
CMD ["python", "app.py"]
```

---

## 📈 **Monitoring & Observability**

### **Cloud Trace Monitoring**
1. Navigate to Google Cloud Console > Cloud Trace
2. Filter by service: `adk-platform`
3. Filter by user ID for user-specific traces
4. Analyze performance and error patterns

### **Key Metrics**
- Agent execution time per user
- Tool call frequency and performance
- LLM response times by model
- Error rates by user and agent
- Concurrent user capacity

### **Health Monitoring**
```bash
# Check platform health
curl http://localhost:8083/api/health

# Expected response
{
  "status": "healthy",
  "adk_available": true,
  "langfuse_available": true,
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **OpenTelemetry Not Available**
```bash
# Solution: Install OpenTelemetry dependencies
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-gcp-trace opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests
```

#### **Service Account Issues**
- Ensure `svcacct.json` is in project root
- Check service account has required IAM roles
- Verify project ID matches service account

#### **Firestore Index Errors**
- Platform automatically creates required indexes
- Wait 5-10 minutes for indexes to build
- Check Firestore console for index status

#### **Port Already in Use**
```bash
# Find and kill process using port 8083
lsof -ti:8083 | xargs kill -9
```

---

## 🏗️ **Project Structure**

```
adk-low-code/
├── src/google2/adk1/nocode/
│   ├── main.py                 # FastAPI application (2904 lines)
│   ├── models.py              # Pydantic data models
│   ├── adk_service.py         # Google ADK integration
│   ├── firestore_manager.py   # Firestore database manager
│   ├── traced_agent_runner.py # Cloud Trace integration
│   ├── auth_service.py         # Authentication service
│   ├── langfuse_service.py     # Observability service
│   ├── static/                # Frontend assets
│   │   ├── css/styles.css     # Tailwind CSS
│   │   └── js/app.js          # JavaScript application
│   └── templates/             # HTML templates
├── unit_test/                 # Comprehensive testing suite
├── app.py                     # Main entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration
├── cloudbuild.yaml           # GCP deployment configuration
├── svcacct.json              # Service account credentials
└── README.md                 # This documentation
```

---

## 🎯 **Key Features**

### **🤖 AI Agent Management**
- **LLM Agents**: Create intelligent agents powered by Gemini models
- **Workflow Agents**: Build complex multi-step workflows
- **Sub-Agents**: Compose agents with specialized sub-agents
- **Agent Templates**: Pre-built templates for common use cases

### **🛠️ Tool Integration**
- **Custom Tools**: Build Python-based function tools
- **Built-in Tools**: Access Google Search and other ADK tools
- **MCP Tools**: Connect to Model Context Protocol servers
- **AI Code Generation**: Get intelligent tool code suggestions
- **Tool Testing**: Built-in testing framework
- **Environment Variables**: Secure configuration for external services

### **🔍 Observability**
- **Cloud Trace**: Complete user ID tracking for all agent executions
- **Performance Monitoring**: Real-time performance metrics
- **Error Tracking**: Detailed error analysis with user context
- **User Behavior**: Insights into user interaction patterns

### **🔐 Security**
- **Service Account Authentication**: No API keys required
- **User Management**: Complete user authentication system
- **Session Management**: Secure session handling
- **Data Encryption**: All data encrypted at rest and in transit

### **☁️ Cloud Integration**
- **Firestore Database**: Scalable NoSQL database
- **Cloud Trace**: Distributed tracing with user context
- **Cloud Run**: Serverless deployment platform
- **Auto-scaling**: Handles traffic spikes automatically

---

## 🔌 **Model Context Protocol (MCP) Integration**

The platform supports **Model Context Protocol (MCP)** servers, allowing agents to connect to external tools and services seamlessly.

### **Supported MCP Servers**

| **Server** | **Package** | **Description** | **Environment Variables** |
|------------|--------------|-----------------|---------------------------|
| **Filesystem** | `@modelcontextprotocol/server-filesystem` | File system operations | `NODE_ENV`, `DEBUG` |
| **AWS S3** | `@geunoh/s3-mcp-server` | S3 bucket operations | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| **GitHub** | `@modelcontextprotocol/server-github` | GitHub API operations | `GITHUB_TOKEN`, `GITHUB_API_URL` |
| **SQLite** | `@modelcontextprotocol/server-sqlite` | Database operations | `DATABASE_URL`, `DB_PATH` |

### **Creating MCP Tools**

**Via UI:**
1. Create Tool → Select "MCP Server Tool"
2. Configure:
   - **Command**: `npx`
   - **Arguments**: `-y`, `@modelcontextprotocol/server-filesystem`
   - **Environment Variables**: Use templates (AWS, GitHub, Database)
   - **Timeout**: `300`

**Via API:**
```json
{
  "id": "filesystem_mcp",
  "name": "Filesystem MCP",
  "description": "File system operations via MCP",
  "tool_type": "mcp",
  "mcp_configuration": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
    "env": {
      "NODE_ENV": "production",
      "DEBUG": "true"
    },
    "timeout": 300
  }
}
```

### **Environment Variable Templates**

The platform provides pre-configured templates for common services:

**AWS Template:**
```json
{
  "AWS_ACCESS_KEY_ID": "your_access_key_here",
  "AWS_SECRET_ACCESS_KEY": "your_secret_key_here",
  "AWS_REGION": "us-east-1",
  "AWS_SESSION_TOKEN": "your_session_token_here",
  "NODE_ENV": "production"
}
```

**GitHub Template:**
```json
{
  "GITHUB_TOKEN": "your_github_token_here",
  "GITHUB_API_URL": "https://api.github.com",
  "GITHUB_OWNER": "your_username",
  "NODE_ENV": "production"
}
```

**Database Template:**
```json
{
  "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname",
  "DB_HOST": "localhost",
  "DB_PORT": "5432",
  "DB_NAME": "your_database",
  "DB_USER": "your_username",
  "DB_PASSWORD": "your_password",
  "NODE_ENV": "production"
}
```

---

## 📚 **Technology Stack**

### **Backend**
- **FastAPI**: Modern, fast web framework
- **Python 3.11+**: Latest Python features
- **Pydantic**: Data validation and serialization
- **Google ADK**: Agent Development Kit
- **Google GenAI**: Generative AI models

### **Database**
- **Google Firestore**: NoSQL document database
- **Service Account Auth**: Secure authentication
- **Real-time Updates**: Live data synchronization

### **Observability**
- **OpenTelemetry**: Distributed tracing
- **Google Cloud Trace**: Trace storage and analysis
- **Langfuse**: LLM observability platform

### **Frontend**
- **HTML5**: Modern web standards
- **Tailwind CSS**: Utility-first CSS framework
- **JavaScript ES6+**: Modern JavaScript features
- **WebSocket**: Real-time communication

### **Deployment**
- **Docker**: Containerization
- **Google Cloud Run**: Serverless platform
- **Cloud Build**: CI/CD pipeline
- **Service Account**: Secure authentication

---

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### **Code Standards**
- **Python**: PEP 8 compliance
- **JavaScript**: ES6+ with consistent formatting
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit tests for new features

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Google ADK Team**: For the amazing Agent Development Kit
- **FastAPI**: For the excellent web framework
- **Tailwind CSS**: For the beautiful UI components
- **Open Source Community**: For inspiration and support

---

**Made with ❤️ for the AI community**

*Build the future of AI agents today!*

---

*Last Updated: September 2024 | Version: 2.0 | Status: Production Ready*
