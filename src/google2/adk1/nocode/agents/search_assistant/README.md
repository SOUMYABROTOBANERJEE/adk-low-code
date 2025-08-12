# search_assistant

An assistant that can search the web.

## Running the Agent

### As a Python Module

```python
from search_assistant import root_agent

async def main():
    response = await root_agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### As an API

Start the API server:

```bash
python search_assistant/api.py
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs.

## Using in Different Tech Stacks

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate",
    json={"prompt": "Hello, agent!"}
)
print(response.json()["text"])
```

### Node.js/TypeScript

```typescript
// TypeScript
import { AgentClient } from './search_assistant/clients/typescript/agent-client';

async function main() {
  const agent = new AgentClient('http://localhost:8000');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}

main().catch(console.error);
```

### JavaScript

```javascript
// JavaScript
const { AgentClient } = require('./search_assistant/clients/javascript/agent-client');

async function main() {
  const agent = new AgentClient('http://localhost:8000');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}

main().catch(console.error);
```

### Other Languages

You can use the REST API directly from any language that can make HTTP requests:

```
POST http://localhost:8000/api/generate
Content-Type: application/json

{
  "prompt": "Hello, agent!"
}
```
