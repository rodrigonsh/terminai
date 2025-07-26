#!/usr/bin/env python3
"""Test script for remote MCP server functionality."""

import asyncio
import json
from terminai.mcp.client import MCPClient


async def test_remote_mcp():
    """Test remote MCP server connections."""
    client = MCPClient()
    
    # Test configurations
    test_configs = [
        {
            "name": "local-filesystem",
            "type": "stdio",
            "command": "mcp-server-filesystem",
            "args": ["/tmp"]
        },
        {
            "name": "remote-github",
            "type": "http",
            "url": "https://mcp-server.example.com/github",
            "headers": {
                "Authorization": "Bearer test-token"
            }
        },
        {
            "name": "remote-sse",
            "type": "sse",
            "url": "https://mcp-server.example.com/sse",
            "headers": {
                "X-API-Key": "test-key"
            }
        }
    ]
    
    print("Testing MCP client with remote server support...")
    
    for config in test_configs:
        try:
            print(f"\nTesting {config['name']} ({config['type']})...")
            success = await client.connect_server(config['name'], config)
            print(f"  Connection: {'✓' if success else '✗'}")
            
            if success:
                servers = client.get_connected_servers()
                print(f"  Connected servers: {servers}")
                
                # Test listing tools
                tools = await client.list_tools(config['name'])
                print(f"  Available tools: {len(tools)}")
                
                # Test connection info
                info = client.get_connection_info(config['name'])
                print(f"  Connection type: {info.get('type', 'unknown')}")
                
                # Disconnect
                await client.disconnect_server(config['name'])
                print(f"  Disconnected: ✓")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_remote_mcp())
