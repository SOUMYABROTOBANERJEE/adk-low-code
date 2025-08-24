#!/usr/bin/env python3
"""
Health check script for the Google ADK No-Code Platform
"""

import asyncio
import aiohttp
import sys
import os
from typing import Dict, Any

async def check_health(host: str = "localhost", port: int = 8080) -> Dict[str, Any]:
    """Check the health of the application"""
    url = f"http://{host}:{port}/api/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "response": data,
                        "status_code": response.status
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "status_code": response.status
                    }
    except aiohttp.ClientConnectorError:
        return {
            "status": "unreachable",
            "error": "Connection refused - server may not be running",
            "status_code": None
        }
    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "error": "Request timed out",
            "status_code": None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "status_code": None
        }

def print_health_status(result: Dict[str, Any]) -> None:
    """Print formatted health status"""
    status = result["status"]
    
    if status == "healthy":
        print("✅ Server is healthy")
        response = result.get("response", {})
        print(f"   ADK Available: {'✅' if response.get('adk_available') else '❌'}")
        print(f"   Langfuse Available: {'✅' if response.get('langfuse_available') else '❌'}")
        print(f"   Timestamp: {response.get('timestamp', 'N/A')}")
    elif status == "unhealthy":
        print(f"❌ Server is unhealthy: {result.get('error', 'Unknown error')}")
    elif status == "unreachable":
        print(f"🔌 Server is unreachable: {result.get('error', 'Unknown error')}")
    elif status == "timeout":
        print(f"⏱️  Request timed out: {result.get('error', 'Unknown error')}")
    else:
        print(f"❓ Unknown status: {result.get('error', 'Unknown error')}")

async def main():
    """Main function"""
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8080))
    
    print(f"🔍 Checking health of server at {host}:{port}...")
    
    result = await check_health(host, port)
    print_health_status(result)
    
    # Exit with appropriate code for scripting
    if result["status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
