#!/usr/bin/env python3
"""Test script to verify MCP tool integration."""

import asyncio
import sys
import os

# Add the terminai package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terminai.terminal import TerminaiTerminal


async def test_mcp_integration():
    """Test MCP tool integration."""
    print("Testing MCP tool integration...")
    
    # Create terminal instance
    terminal = TerminaiTerminal()
    
    # Connect to MCP servers
    print("\n1. Connecting to MCP servers...")
    await terminal._connect_mcp_servers_async()
    
    # List all tools
    print("\n2. Listing all available tools...")
    tools_by_type = terminal.tool_manager.list_tools_by_type()
    
    print(f"Builtin tools: {len(tools_by_type['builtin'])}")
    for tool in tools_by_type['builtin']:
        print(f"  - {tool}")
    
    print(f"\nMCP tools: {len(tools_by_type['mcp'])}")
    for tool in tools_by_type['mcp']:
        print(f"  - {tool}")
    
    # Test MCP tool info
    if tools_by_type['mcp']:
        print("\n3. Testing MCP tool info...")
        first_mcp_tool = tools_by_type['mcp'][0]
        info = terminal.tool_manager.get_tool_info(first_mcp_tool)
        if info:
            print(f"Tool: {info['name']}")
            print(f"Description: {info['description']}")
            print("Parameters:")
            for param_name, param_info in info['parameters'].items():
                required = "required" if param_info['required'] else "optional"
                print(f"  {param_name} ({param_info['type']}, {required}): {param_info['description']}")
    
    # Test tool definitions for LLM
    print("\n4. Testing tool definitions for LLM...")
    tool_definitions = terminal.tool_manager.get_tool_definitions()
    print(f"Total tool definitions: {len(tool_definitions)}")
    
    mcp_tool_definitions = [t for t in tool_definitions if t['function']['name'].startswith('mcp_')]
    print(f"MCP tool definitions: {len(mcp_tool_definitions)}")
    
    if mcp_tool_definitions:
        print("First MCP tool definition:")
        first_def = mcp_tool_definitions[0]
        print(f"  Name: {first_def['function']['name']}")
        print(f"  Description: {first_def['function']['description']}")
    
    # Test MCP resources
    print("\n5. Testing MCP resources...")
    mcp_resources = terminal.mcp_tool_wrapper.get_mcp_resources()
    print(f"MCP resources from {len(mcp_resources)} servers:")
    for server, resources in mcp_resources.items():
        print(f"  {server}: {len(resources)} resources")
    
    # Cleanup
    await terminal.mcp_client.disconnect_all()
    print("\n✓ MCP integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_integration())
