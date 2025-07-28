#!/usr/bin/env python3
"""Test MCP SSE connection."""

import asyncio
import logging
import sys
import os

# Add the terminai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from terminai.mcp.connections.sse_connection import SSEConnection

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_connection():
    """Test the MCP SSE connection."""
    config = {
        "url": "http://127.0.0.1:8000/mcp/sse",
        "headers": {
            "Authorization": "Bearer 2|Loeq3pihCqvVrJQxnX3ZT9SATpJNQId81ZDAZRwt0cafb2d1"
        },
        "timeout": 30
    }
    
    connection = SSEConnection("takeoff", config)
    
    try:
        print("Testing MCP SSE connection...")
        success = await connection.connect()
        print(f"Connection result: {success}")
        
        if success:
            print("Connection successful! Testing tools list...")
            tools = await connection.list_tools()
            print(f"Available tools: {tools}")
            
            print("Testing resources list...")
            resources = await connection.list_resources()
            print(f"Available resources: {resources}")
        
        # Keep connection alive for a bit
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await connection.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(test_connection())
