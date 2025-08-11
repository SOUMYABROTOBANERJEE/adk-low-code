/**
 * TypeScript client for search_assistant API
 */

export interface GenerateRequest {
  prompt: string;
  temperature?: number;
}

export interface GenerateResponse {
  text: string;
}

export class AgentClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generate content using the agent
   * @param prompt The prompt to send to the agent
   * @param temperature Optional temperature parameter
   * @returns The generated text
   */
  async generateContent(prompt: string, temperature?: number): Promise<GenerateResponse> {
    const request: GenerateRequest = {
      prompt,
      ...(temperature !== undefined && { temperature })
    };

    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API error: ${error.detail || response.statusText}`);
    }

    return await response.json();
  }
}
