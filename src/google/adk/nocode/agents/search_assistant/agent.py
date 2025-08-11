import sys, pathlib, os
import asyncio
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / 'custom_tools'))
from google.generativeai import GenerativeModel, configure
from google.generativeai import types

# Configure Google GenAI
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set")
configure(api_key=api_key)

# Simple Google GenAI Agent implementation
class GoogleGenAIAgent:
    def __init__(self, model, name, description, instruction, tools=None, sub_agents=None, flow="auto", temperature=0.2):
        self.model = model
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.sub_agents = sub_agents or []
        self.flow = flow
        self.temperature = temperature
        
        # Initialize Google GenAI model
        self.genai_model = GenerativeModel(
            model_name=model,
            generation_config=types.GenerationConfig(
                temperature=temperature,
            )
        )
        
    async def generate_content(self, prompt, **kwargs):
        """Generate content using Google GenAI API."""
        try:
            # Combine instruction and prompt
            full_prompt = f"{self.instruction}\n\nUser: {prompt}\n\nAssistant:"
            
            # Generate content
            response = self.genai_model.generate_content(full_prompt)
            return response
        except Exception as e:
            return types.GenerateContentResponse(text=f"Error generating content: {str(e)}")

# Create the agent instance
root_agent = GoogleGenAIAgent(
    model="gemini-2.0-flash-001",
    name="search_assistant",
    description="An assistant that can search the web.",
    instruction="""
You are a helpful assistant. Answer user questions using Google Search when needed.
""",
    tools=[],
    temperature=0.2,
)

# Add async methods for better compatibility
async def chat(message: str):
    """Async chat method for the agent."""
    try:
        result = await root_agent.generate_content(message)
        return result.text if hasattr(result, 'text') else str(result)
    except Exception as e:
        return f"Error: {str(e)}"

async def run(message: str):
    """Async run method for the agent."""
    try:
        result = await root_agent.generate_content(message)
        return result.text if hasattr(result, 'text') else str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Main execution block for testing
if __name__ == "__main__":
    async def main():
        # Test the agent
        try:
            result = await root_agent.generate_content("Hello, how are you?")
            print(f"Agent response: {result.text if hasattr(result, 'text') else result}")
        except Exception as e:
            print(f"Error running agent: {e}")
    
    # Run the async main function
    asyncio.run(main())
