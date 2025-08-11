# Google ADK No-Code Platform

A comprehensive, visual platform for building, configuring, and testing AI agents using Google's Agent Development Kit (ADK) without writing Python code.

![Platform Screenshot](https://via.placeholder.com/800x400/4A90E2/FFFFFF?text=Google+ADK+Platform)

## 🚀 Features

### Core Functionality
- **Visual Agent Builder**: Create and configure AI agents through an intuitive web interface
- **Tool Management**: Create custom function tools, integrate built-in tools, and manage tool configurations
- **Multi-Agent Systems**: Build complex workflows with sequential, parallel, and loop agents
- **Real-time Chat Interface**: Test your agents immediately in a chat environment
- **Code Generation**: Export your agent configurations as ready-to-run Python code

### Advanced Capabilities
- **Model Configuration**: Fine-tune Gemini models with temperature, max tokens, and other parameters
- **Tool Integration**: Attach multiple tools to agents for enhanced capabilities
- **Project Management**: Organize agents and tools into projects
- **Export & Deployment**: Generate production-ready Python code for deployment
- **WebSocket Support**: Real-time communication for enhanced chat experience

## 🏗️ Architecture

The platform is built with a modern, scalable architecture:

- **Backend**: FastAPI with async support and WebSocket capabilities
- **Frontend**: Modern HTML5 with Tailwind CSS and vanilla JavaScript
- **Data Models**: Pydantic models for type safety and validation
- **ADK Integration**: Direct integration with Google's Agent Development Kit
- **Real-time Communication**: WebSocket support for live chat

## 📋 Requirements

- Python 3.9+
- Google ADK 0.2.0+
- FastAPI and related web dependencies
- Google Cloud credentials (for Gemini models)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/adk-low-code.git
cd adk-low-code
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `config.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
```

### 4. Run the Platform
```bash
# Using Python directly
python app.py

# Using the CLI
python src/google/adk1/nocode/cli.py start

# Using the CLI with auto-browser opening
python src/google/adk1/nocode/cli.py start --open-browser
```

## 🎯 Quick Start

### 1. Access the Platform
Open your browser and navigate to `http://localhost:8080`

### 2. Create Your First Tool
1. Click "New Tool" in the navigation
2. Choose "Function Tool" type
3. Write your Python function code
4. Save the tool

### 3. Create Your First Agent
1. Click "New Agent" in the navigation
2. Configure the agent:
   - Name and description
   - System prompt
   - Model settings (temperature, max tokens)
   - Attach tools
3. Save the agent

### 4. Test Your Agent
1. Select your agent from the chat interface
2. Type a message and press Enter
3. Watch your agent respond using the configured tools!

### 5. Export Your Code
1. Click the code icon on any agent
2. Review the generated Python code
3. Download the code for deployment

## 🔧 API Endpoints

The platform provides a comprehensive REST API:

### Agents
- `GET /api/agents` - List all agents
- `POST /api/agents` - Create a new agent
- `GET /api/agents/{id}` - Get agent details
- `PUT /api/agents/{id}` - Update an agent
- `DELETE /api/agents/{id}` - Delete an agent

### Tools
- `GET /api/tools` - List all tools
- `POST /api/tools` - Create a new tool
- `GET /api/tools/{id}` - Get tool details
- `PUT /api/tools/{id}` - Update a tool
- `DELETE /api/tools/{id}` - Delete a tool

### Chat & Execution
- `POST /api/chat/{agent_id}` - Chat with an agent
- `GET /api/chat/sessions/{session_id}` - Get chat session
- `DELETE /api/chat/sessions/{session_id}` - Clear chat session

### Code Generation
- `POST /api/generate/{agent_id}` - Generate Python code for an agent
- `POST /api/export/project/{project_id}` - Export project as Python files

### WebSocket
- `WS /ws/chat/{agent_id}` - Real-time chat with an agent

## 🎨 UI Components

### Agent Configuration Panel
- **Basic Settings**: Name, description, type
- **System Prompt**: Define agent behavior and capabilities
- **Model Configuration**: Temperature, max tokens, model selection
- **Tool Selection**: Attach multiple tools to agents
- **Advanced Options**: Instructions, tags, workflow configuration

### Tool Creation Interface
- **Tool Types**: Function, Built-in, Google Cloud, MCP, OpenAPI
- **Code Editor**: Write Python functions for custom tools
- **Parameter Configuration**: Define tool inputs and outputs
- **Validation**: Syntax checking and error handling

### Chat Interface
- **Agent Selection**: Choose which agent to chat with
- **Real-time Messaging**: Instant responses with WebSocket support
- **Session Management**: Persistent chat history
- **Error Handling**: Clear error messages and debugging

### Code Generation
- **Python Export**: Generate production-ready Python code
- **Project Structure**: Complete project files with dependencies
- **Download Support**: Direct file downloads for generated code
- **Code Preview**: Review generated code before downloading

## 🔌 Tool Types

### Function Tools
Create custom Python functions that agents can call:
```python
def execute(input_data: str) -> str:
    # Your custom logic here
    result = process_input(input_data)
    return f"Processed: {result}"
```

### Built-in Tools
Integrate with ADK's built-in tool ecosystem:
- Search tools
- Code execution
- File operations
- Web scraping

### Google Cloud Tools
Leverage Google Cloud services:
- Vertex AI
- Cloud Storage
- BigQuery
- Cloud Functions

### MCP Tools
Model Context Protocol integration for enhanced capabilities.

### OpenAPI Tools
Integrate with any OpenAPI-compliant service.

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn src.google.adk1.nocode.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t adk-platform .
docker run -p 8080:8080 adk-platform
```

### Cloud Deployment
- **Google Cloud Run**: Serverless deployment
- **Google Kubernetes Engine**: Scalable container deployment
- **Cloud Functions**: Event-driven execution
- **App Engine**: Managed platform deployment

## 🧪 Testing

Run the test suite:
```bash
# Using the CLI
python src/google/adk1/nocode/cli.py test

# Using pytest directly
pytest test_google_adk.py
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the platform
- **Google ADK Docs**: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- **Platform Guide**: Comprehensive usage guide in the platform UI

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
python app.py

# Run tests
pytest

# Format code
black src/
isort src/
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google ADK Team**: For the excellent Agent Development Kit
- **FastAPI**: For the modern, fast web framework
- **Tailwind CSS**: For the beautiful, responsive UI components
- **Open Source Community**: For the tools and libraries that make this possible

## 📞 Support

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the platform's built-in help system
- **Email**: Contact the development team

## 🔮 Roadmap

### Upcoming Features
- **Visual Workflow Builder**: Drag-and-drop workflow creation
- **Agent Templates**: Pre-built agent configurations
- **Advanced Analytics**: Performance metrics and insights
- **Team Collaboration**: Multi-user support and sharing
- **Plugin System**: Extensible tool and agent ecosystem
- **Mobile App**: Native mobile application
- **Enterprise Features**: SSO, RBAC, audit logging

### Long-term Vision
- **AI-Powered Agent Generation**: Generate agents from natural language descriptions
- **Advanced Workflow Orchestration**: Complex multi-agent workflows
- **Integration Marketplace**: Third-party tool and service integrations
- **Global Agent Network**: Share and discover agents across the community

---

**Built with ❤️ by the ADK Community**

*Transform your ideas into intelligent agents with the power of Google ADK and the simplicity of no-code development.*
