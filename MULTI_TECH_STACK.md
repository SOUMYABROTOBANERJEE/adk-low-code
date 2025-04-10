# Using No-Code ADK Agents in Different Tech Stacks

This guide explains how to use agents created with the No-Code ADK in various tech stacks, including Node.js, TypeScript, and others.

## Overview

The No-Code ADK generates agents that can be used in multiple ways:

1. **Python Import**: Directly import the agent in Python code
2. **REST API**: Use the agent via a REST API from any language
3. **Generated Clients**: Use the generated TypeScript/JavaScript clients

## Python Usage

### Direct Import

```python
from your_agent_package import root_agent

async def main():
    response = await root_agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Using the API in Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate",
    json={"prompt": "Hello, agent!"}
)
print(response.json()["text"])
```

## Node.js/TypeScript Usage

### Using the TypeScript Client

```typescript
// TypeScript
import { AgentClient } from './your_agent/clients/typescript/agent-client';

async function main() {
  const agent = new AgentClient('http://localhost:8000');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}

main().catch(console.error);
```

### Using the JavaScript Client

```javascript
// JavaScript
const { AgentClient } = require('./your_agent/clients/javascript/agent-client');

async function main() {
  const agent = new AgentClient('http://localhost:8000');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}

main().catch(console.error);
```

### Using Fetch API

```javascript
// JavaScript with Fetch
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
.then(data => console.log(data.text))
.catch(error => console.error('Error:', error));
```

## Other Languages

### Java

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class AgentClient {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        
        String requestBody = "{\"prompt\": \"Hello, agent!\"}";
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:8000/api/generate"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();
            
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        System.out.println(response.body());
    }
}
```

### C#

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Program
{
    static async Task Main(string[] args)
    {
        using (HttpClient client = new HttpClient())
        {
            var requestData = new { prompt = "Hello, agent!" };
            var content = new StringContent(
                JsonConvert.SerializeObject(requestData),
                Encoding.UTF8,
                "application/json");
                
            HttpResponseMessage response = await client.PostAsync(
                "http://localhost:8000/api/generate", content);
                
            string responseBody = await response.Content.ReadAsStringAsync();
            Console.WriteLine(responseBody);
        }
    }
}
```

### PHP

```php
<?php
$url = 'http://localhost:8000/api/generate';
$data = array('prompt' => 'Hello, agent!');

$options = array(
    'http' => array(
        'header'  => "Content-type: application/json\r\n",
        'method'  => 'POST',
        'content' => json_encode($data)
    )
);

$context  = stream_context_create($options);
$result = file_get_contents($url, false, $context);

if ($result === FALSE) {
    echo "Error\n";
} else {
    $response = json_decode($result, true);
    echo $response['text'] . "\n";
}
?>
```

## Running the API Server

Before using the agent from any tech stack, you need to start the API server:

```bash
python your_agent/api.py
```

This will start the server on http://localhost:8000 by default.

## Customizing the API

You can customize the API port when creating the agent in the No-Code ADK interface by setting the "API Port" field.

## Security Considerations

- The API server does not include authentication by default
- For production use, consider adding authentication and HTTPS
- The API server is designed for local use by default
