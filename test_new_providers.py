#!/usr/bin/env python3
"""Test script for new providers and tool system."""

import asyncio
import json
from terminai.llm.base import LLMManager
from terminai.config.manager import ConfigManager
from terminai.tools.manager import ToolManager
from terminai.utils.bash import BashExecutor
from terminai.tools.builtin import BuiltinTools


async def test_providers():
    """Test the new providers."""
    print("Testing new LLM providers...")
    
    # Create config manager
    config = ConfigManager()
    
    # Create LLM manager
    llm_manager = LLMManager()
    llm_manager.load_providers_from_config(config._config)
    
    # List available providers
    providers = llm_manager.list_providers()
    print(f"Available providers: {providers}")
    
    # Check configuration status
    configured = llm_manager.get_configured_providers(config._config)
    for provider, is_configured in configured.items():
        print(f"  {provider}: {'✓' if is_configured else '✗'}")
    
    # Test DeepSeek and OpenRouter specifically
    for provider_name in ["deepseek", "openrouter"]:
        provider_config = config.get_llm_config(provider_name)
        if provider_config:
            provider = llm_manager.get_provider(provider_name, provider_config)
            if provider:
                print(f"\n{provider_name.upper()} Provider:")
                print(f"  Configured: {provider.is_configured()}")
                print(f"  Required config: {provider.get_required_config()}")
                if provider.is_configured():
                    print(f"  Model: {provider.model}")
                    print(f"  Base URL: {provider.base_url if hasattr(provider, 'base_url') else 'default'}")


async def test_tools():
    """Test the tool system."""
    print("\nTesting tool system...")
    
    # Create tool manager
    tool_manager = ToolManager()
    
    # Create bash executor and builtin tools
    bash_executor = BashExecutor()
    builtin_tools = BuiltinTools(bash_executor)
    builtin_tools.register_all(tool_manager)
    
    # List available tools
    tools = tool_manager.list_tools()
    print(f"Available tools: {tools}")
    
    # Test tool definitions
    definitions = tool_manager.get_tool_definitions()
    print(f"\nTool definitions ({len(definitions)} tools):")
    for definition in definitions:
        print(f"  - {definition['function']['name']}: {definition['function']['description']}")
    
    # Test specific tools
    print("\nTesting specific tools:")
    
    # Test list_files
    print("  Testing list_files...")
    result = await tool_manager.execute_tool("list_files", {"path": "."})
    print(f"    Success: {result.success}")
    if result.success:
        print(f"    Found {len(result.content.split())} items")
    
    # Test read_file
    print("  Testing read_file...")
    result = await tool_manager.execute_tool("read_file", {"path": "README.md"})
    print(f"    Success: {result.success}")
    if result.success:
        print(f"    File size: {len(result.content)} characters")
    
    # Test search_files
    print("  Testing search_files...")
    result = await tool_manager.execute_tool("search_files", {
        "pattern": "py",
        "path": ".",
        "recursive": True,
        "search_content": False
    })
    print(f"    Success: {result.success}")
    if result.success:
        files = result.content.split('\n') if result.content else []
        print(f"    Found {len(files)} Python files")


async def main():
    """Main test function."""
    print("=== Terminai New Features Test ===\n")
    
    await test_providers()
    await test_tools()
    
    print("\n=== Test Complete ===")
    print("\nTo use the new features:")
    print("1. Set your API keys in ~/.terminai/config.json or environment variables")
    print("2. Run: terminai")
    print("3. Try commands like:")
    print("   - 'list all python files'")
    print("   - 'read README.md'")
    print("   - 'search for TODO in all files'")


if __name__ == "__main__":
    asyncio.run(main())
