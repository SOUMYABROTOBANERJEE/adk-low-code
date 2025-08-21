# 🚀 Google ADK No-Code Platform

A powerful, production-ready platform for building and deploying AI agents using Google's Agent Development Kit (ADK). Create sophisticated AI workflows with a visual interface, AI-powered suggestions, and seamless deployment to Google Cloud Platform.

## ✨ Features

### 🤖 **AI Agent Management**
- **LLM Agents**: Create intelligent agents powered by Gemini models
- **Workflow Agents**: Build complex multi-step workflows
- **Sub-Agents**: Compose agents with specialized sub-agents
- **Agent Templates**: Pre-built templates for common use cases

### 🛠️ **Tool Integration**
- **Custom Tools**: Build Python-based function tools
- **Built-in Tools**: Access Google Search and other ADK tools
- **Tool Marketplace**: Reusable tool library
- **AI Code Generation**: Get intelligent tool code suggestions

### 🎯 **AI-Powered Development**
- **Smart Suggestions**: AI-generated names, descriptions, and system prompts
- **Code Generation**: Automatic Python function code creation
- **Best Practices**: Built-in coding standards and error handling
- **Intelligent Workflows**: AI-assisted agent composition

### 💾 **Persistent Storage**
- **SQLite Database**: Local development with easy migration path
- **GCP Ready**: Designed for Firestore/BigQuery migration
- **Data Persistence**: Agents, tools, and projects saved permanently
- **Session Management**: Chat history and conversation tracking

### 🔐 **Security & Users**
- **User Authentication**: Registration, login, and sessions
- **Password Hashing**: SHA-256 stored hashes
- **Session Tokens**: Expiring user sessions
- **Optional Observability**: Langfuse tracing for prod insights

### 🌐 **Modern Web Interface**
- **Responsive Design**: Works on desktop and mobile
- **Real-time Chat**: WebSocket-powered conversations
- **Visual Builder**: Drag-and-drop agent creation
- **Dark/Light Themes**: Customizable interface

### ☁️ **Cloud Deployment**
- **Docker Ready**: Containerized for easy deployment
- **GCP Cloud Run**: Optimized for Google Cloud Platform
- **Auto-scaling**: Handles traffic spikes automatically
- **Health Monitoring**: Built-in health checks and logging

## 🏗️ Project Structure

```
adk-low-code/
├── src/                    # Main source code
│   └── google2/adk1/nocode/
│       ├── main.py        # FastAPI application
│       ├── models.py      # Pydantic models
│       ├── adk_service.py # Google ADK integration
│       ├── static/        # Frontend assets (CSS, JS)
│       └── templates/     # HTML templates
├── unit_test/             # Testing and development utilities
│   ├── check_db.py        # Database testing
│   ├── test_platform.py   # Platform functionality testing
│   ├── start_platform.py  # Startup testing
│   └── add_updated_at.py  # Database migration utilities
├── app.py                 # Main entry point
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google AI API Key
- Google ADK installed

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/adk-low-code.git
   cd adk-low-code
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

5. **Run the platform**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://127.0.0.1:8083`

### Authentication (Quick test)

```bash
curl -X POST http://127.0.0.1:8083/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"User","password":"secret123"}'

curl -X POST http://127.0.0.1:8083/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'
```

## 🏗️ Architecture

### Database Layer
- **SQLite**: Local development and testing
- **Migration Ready**: Easy transition to GCP services
- **Schema Design**: Optimized for agent and tool management

### Service Layer
- **ADK Service**: Google ADK integration
- **Database Manager**: Persistent storage operations
- **AI Service**: Google GenAI integration for suggestions

### API Layer
- **FastAPI**: Modern, fast web framework
- **REST Endpoints**: Full CRUD for agents, tools, projects
- **WebSocket Support**: Real-time chat functionality
- **AI Suggestions**: Intelligent development assistance

### Frontend Layer
- **Modern UI**: Tailwind CSS with responsive design
- **Interactive Components**: Drag-and-drop, real-time updates
- **AI Integration**: Magic wand buttons for smart suggestions

## 🎨 Creating Your First Agent

### 1. **Create a Tool**
- Click "Create Tool" button
- Fill in name and description
- Use the magic wand 🪄 for AI suggestions
- Write or generate Python function code
- Save and test your tool

### 2. **Create an Agent**
- Click "Create Agent" button
- Choose agent type (LLM, Workflow, etc.)
- Write system prompt and instructions
- Use AI suggestions for better prompts
- Assign tools to your agent
- Configure model settings

### 3. **Test Your Agent**
- Use the chat interface
- Send messages to your agent
- Watch it use tools and respond
- Monitor performance and logs

## 🚀 Deployment to GCP

### Option 1: Cloud Build (Recommended)

1. **Set up Cloud Build**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. **Update cloudbuild.yaml**
   - Set your Google API key in substitutions
   - Adjust region and resources as needed

3. **Deploy**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

### Option 2: Manual Deployment

1. **Build Docker image**
   ```bash
   docker build -t gcr.io/PROJECT_ID/adk-platform .
   ```

2. **Push to Container Registry**
   ```bash
   docker push gcr.io/PROJECT_ID/adk-platform
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy adk-platform \
     --image gcr.io/PROJECT_ID/adk-platform \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your-key
   ```

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google AI API key
- `DATABASE_URL`: Database connection string (for production)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

Optional (Langfuse Observability):
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_HOST` (default `https://cloud.langfuse.com`)

### Database Configuration
- **Development**: SQLite (default)
- **Production**: Firestore or BigQuery
- **Migration**: Use database manager methods

### Model Settings
- **Gemini 2.0 Flash**: Fast, efficient responses
- **Gemini 2.5 Flash**: Balanced performance and quality
- **Gemini 2.5 Pro**: Highest quality, slower responses

## 📊 Monitoring & Logging

### Health Checks
- **Endpoint**: `/api/health`
- **Status**: Database, ADK, and GenAI availability
- **Response Time**: Performance metrics

### Logging
- **Structured Logs**: JSON format for easy parsing
- **Error Tracking**: Detailed error information
- **Performance Metrics**: Response times and resource usage

### Metrics
- **Agent Usage**: Popular agents and tools
- **Response Times**: Performance monitoring
- **Error Rates**: System health tracking

## 🔒 Security

### Authentication
- **API Key Management**: Secure Google API key handling
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Parameterized queries

### Data Protection
- **Encryption**: Data encryption at rest and in transit
- **Access Control**: Role-based permissions (planned)
- **Audit Logging**: Complete activity tracking

## 🧪 Testing

### Test Structure
The project includes a comprehensive testing suite organized in the `unit_test/` folder:

- **`unit_test/check_db.py`**: Database connectivity and schema verification
- **`unit_test/test_platform.py`**: Platform functionality testing
- **`unit_test/start_platform.py`**: Platform startup and configuration testing
- **`unit_test/add_updated_at.py`**: Database migration utilities

See [unit_test/README.md](unit_test/README.md) for detailed testing documentation.

### API Testing
```bash
# Test health endpoint
curl http://127.0.0.1:8083/api/health

# Test tool creation
curl -X POST http://127.0.0.1:8083/api/tools \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Tool","description":"A test tool","tool_type":"function"}'

# Test agent creation
curl -X POST http://127.0.0.1:8083/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"Test_Agent","description":"A test agent","agent_type":"llm"}'
```

### Frontend Testing
- Open browser developer tools
- Check console for errors
- Test responsive design
- Verify AI suggestions work

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **Python**: PEP 8 compliance
- **JavaScript**: ES6+ with consistent formatting
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit tests for new features

## 📚 API Reference

### Core Endpoints
- `GET /api/health` - System health check
- `GET /api/agents` - List all agents
- `POST /api/agents` - Create new agent
- `GET /api/tools` - List all tools
- `POST /api/tools` - Create new tool
- `POST /api/chat/{agent_id}` - Chat with agent

### Authentication Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and receive session token
- `POST /api/auth/logout` - Logout (invalidate session)

### AI Suggestion Endpoints
- `POST /api/suggestions/agent/name` - Get agent name suggestions
- `POST /api/suggestions/agent/description` - Get description suggestions
- `POST /api/suggestions/tool/code` - Get tool code suggestions

### WebSocket Endpoints
- `WS /ws/chat/{agent_id}` - Real-time chat

## 🆘 Troubleshooting

### Common Issues

1. **ADK Not Available**
   - Check Google ADK installation
   - Verify API key is set
   - Check network connectivity

2. **Database Errors**
   - Verify database file permissions
   - Check SQLite installation
   - Review error logs

3. **AI Suggestions Not Working**
   - Verify GenAI API key
   - Check API quotas
   - Review network connectivity

### Getting Help
- **Issues**: GitHub issue tracker
- **Documentation**: This README and inline docs
- **Community**: GitHub discussions

## 📈 Roadmap

### Phase 1 (Current)
- ✅ Basic agent and tool management
- ✅ AI-powered suggestions
- ✅ Persistent storage
- ✅ Docker deployment

### Phase 2 (Next)
- 🔄 Advanced workflow agents
- 🔄 Tool marketplace
- 🔄 User authentication
- 🔄 Team collaboration

### Phase 3 (Future)
- 📋 Multi-tenant support
- 📋 Advanced analytics
- 📋 Custom UI themes
- 📋 Plugin system

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google ADK Team**: For the amazing Agent Development Kit
- **FastAPI**: For the excellent web framework
- **Tailwind CSS**: For the beautiful UI components
- **Open Source Community**: For inspiration and support

---

**Made with ❤️ for the TSL AI community**

*Build the future of AI agents today!*
