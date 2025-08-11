/**
 * JavaScript client for search_assistant API
 */

class AgentClient {
  /**
   * Create a new AgentClient
   * @param {string} baseUrl - The base URL of the agent API
   */
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generate content using the agent
   * @param {string} prompt - The prompt to send to the agent
   * @param {number|undefined} temperature - Optional temperature parameter
   * @returns {Promise<{text: string}>} The generated text
   */
  async generateContent(prompt, temperature) {
    const request = {
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

// For CommonJS environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AgentClient };
}
