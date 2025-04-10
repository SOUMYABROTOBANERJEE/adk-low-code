# No-Code ADK Interface

A visual, no-code interface for creating, configuring, and deploying AI agents using the Google Agent Development Kit (ADK) without writing Python code. This package also supports integration with various tech stacks including Node.js and TypeScript.

## Latest Updates (v0.1.3)

- **Improved Package Structure**: Fixed issues with static files and templates
- **Enhanced Ollama Integration**: Better support for locally installed Ollama models
- **Multi-Tech Stack Support**: Generate API wrappers and clients for different programming languages
- **GitHub Sponsors Integration**: Added support for project funding

## Features

- Visual agent builder with intuitive interface
- Tool configuration through forms
- Agent flow visualization and editing
- One-click deployment
- Template library for common agent patterns
- Export to Python code for advanced customization
- Support for both Google Gemini models and local Ollama models
- Multi-tech stack integration (Python, Node.js, TypeScript, etc.)

## Installation

```bash
pip install google-adk-nocode
```

## Quick Start

1. Launch the no-code interface:
```bash
adk-nocode start
```

2. Access the interface at http://localhost:8080

3. Create your first agent using the visual interface

## Using Agents in Different Tech Stacks

### Python Applications

Agents created with the No-Code ADK can be directly imported in Python:

```python
from your_agent_package import root_agent

async def main():
    response = await root_agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Node.js/TypeScript Applications

The No-Code ADK can generate REST API wrappers for your agents, making them accessible from any tech stack:

1. Enable API export when creating your agent
2. Use the generated API client in your Node.js/TypeScript application:

```typescript
// TypeScript example
import { AgentClient } from './generated/agent-client';

async function main() {
  const agent = new AgentClient('http://localhost:8000');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}

main().catch(console.error);
```

### Other Tech Stacks

For other tech stacks, you can use the REST API directly:

```javascript
// JavaScript fetch example
fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: 'Hello, agent!',
  }),
})
.then(response => response.json())
.then(data => console.log(data.text));
```

## Documentation

For full documentation, visit [our documentation site](https://github.com/abhishekkumar35/google-adk-nocode).

## Support the Project

If you find No-Code ADK useful, please consider supporting its development:

[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa.svg)](https://github.com/sponsors/abhishekkumar35)

Your support helps ensure the continued development and maintenance of this project.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
