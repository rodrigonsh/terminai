"""Main terminal interface for terminai."""

import os
import sys
import asyncio
import readline
import atexit
import logging
import json
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.json import JSON

from .config.manager import ConfigManager
from .llm.base import LLMManager, LLMMessage
from .mcp.client import MCPClient
from .utils.bash import BashExecutor
from .tools.manager import ToolManager
from .tools.builtin import BuiltinTools


class TerminaiTerminal:
    """Main terminal interface."""
    
    def __init__(self):
        """Initialize the terminal."""
        self.console = Console()
        self.config = ConfigManager()
        self.llm_manager = LLMManager()
        self.mcp_client = MCPClient()
        self.bash_executor = BashExecutor(
            shell=self.config.get("bash.shell", "/bin/bash")
        )
        self.tool_manager = ToolManager()
        self.builtin_tools = BuiltinTools(self.bash_executor)
        
        # Setup logging
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.config_dir / "logs" / "terminai.log"),
                logging.StreamHandler(sys.stderr)
            ]
        )
        
        # Setup history
        self.setup_history()
        
        # Setup tools
        self.setup_tools()
        
        # Current LLM provider
        self.current_provider = None
        self.setup_llm_provider()
    
    def setup_history(self):
        """Setup command history."""
        history_file = self.config.get_history_file()
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        
        # Set up history search
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('"\\e[A": history-search-backward')
        readline.parse_and_bind('"\\e[B": history-search-forward')
        
        # Save history on exit
        atexit.register(self.save_history)
    
    def save_history(self):
        """Save command history."""
        try:
            history_file = self.config.get_history_file()
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            readline.write_history_file(history_file)
        except Exception as e:
            self.console.print(f"[red]Error saving history: {e}[/red]")
    
    def setup_tools(self):
        """Setup the tool system."""
        # Register builtin tools
        self.builtin_tools.register_all(self.tool_manager)
        
        # Check if tools are enabled in config
        tools_enabled = self.config.get("tools.enabled", True)
        if not tools_enabled:
            self.console.print("[yellow]Warning: Tools are disabled in configuration[/yellow]")
    
    def setup_llm_provider(self):
        """Setup the LLM provider."""
        # Load providers dynamically from configuration
        self.llm_manager.load_providers_from_config(self.config._config)
        
        provider_name = self.config.get("llm.default_provider", "openai")
        provider_config = self.config.get_llm_config(provider_name)
        
        if not provider_config:
            self.console.print(f"[yellow]Warning: No configuration for provider '{provider_name}'[/yellow]")
            return
        
        self.current_provider = self.llm_manager.get_provider(provider_name, provider_config)
        
        if self.current_provider and not self.current_provider.is_configured():
            self.console.print(f"[yellow]Warning: Provider '{provider_name}' is not properly configured[/yellow]")
            self.console.print(f"[yellow]Please set the required API keys in {self.config.config_file}[/yellow]")
    
    async def process_input(self, user_input: str) -> bool:
        """Process user input."""
        user_input = user_input.strip()
        
        if not user_input:
            return True
        
        # Handle special commands
        if user_input.startswith('!'):
            return await self.handle_special_command(user_input[1:])
        
        # Check if it's a bash command or natural language
        if self.bash_executor.is_bash_command(user_input):
            # It's a bash command, execute directly
            return await self.execute_bash_command(user_input)
        else:
            # It's natural language, use tool-calling
            return await self.handle_natural_language(user_input)
    
    async def handle_natural_language(self, text: str) -> bool:
        """Handle natural language input with tool-calling."""
        if not self.current_provider or not self.current_provider.is_configured():
            # Fallback to basic command suggestions when no LLM is configured
            self.console.print("[yellow]Note: No LLM provider configured. Using basic suggestions.[/yellow]")
            suggested_command = self.bash_executor.get_command_suggestion(text)
            
            # Display the suggestion
            self.console.print(Panel(
                Syntax(suggested_command, "bash", theme="monokai"),
                title="Suggested Command",
                expand=False
            ))
            
            # Ask for confirmation
            if self.config.get("terminal.confirm_commands", True):
                if not Confirm.ask("Execute this command?"):
                    return True
            
            # Execute the suggested command
            return await self.execute_bash_command(suggested_command)
        
        try:
            # Use tool-calling for complex tasks
            messages = self.current_provider.format_prompt(text)
            
            # Get available tools
            tools = self.tool_manager.get_tool_definitions()
            
            # Generate response with tool-calling
            response = await self.current_provider.generate(messages, tools=tools)
            
            # Handle tool calls
            if response.tool_calls:
                await self.handle_tool_calls(response.tool_calls, messages)
            else:
                # No tool calls, display the response
                if response.content.strip():
                    self.console.print(Panel(
                        response.content.strip(),
                        title="AI Response",
                        expand=False
                    ))
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error processing request: {e}[/red]")
            return True
    
    async def handle_tool_calls(self, tool_calls: List[Dict[str, Any]], messages: List[LLMMessage]):
        """Handle tool calls from the LLM."""
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            tool_id = tool_call["id"]
            
            # Display tool call
            self.console.print(Panel(
                f"Calling tool: {tool_name}\nArguments: {json.dumps(tool_args, indent=2)}",
                title="Tool Call",
                expand=False
            ))
            
            # Ask for confirmation if enabled
            if self.config.get("tools.confirm_tool_calls", True):
                if not Confirm.ask("Execute this tool call?"):
                    continue
            
            # Execute the tool
            result = await self.tool_manager.execute_tool(tool_name, tool_args)
            
            if result.success:
                self.console.print(Panel(
                    result.content,
                    title=f"Tool Result: {tool_name}",
                    expand=False
                ))
                
                # Add tool result to conversation
                messages.append(
                    LLMMessage(
                        role="tool",
                        content=result.content,
                        tool_call_id=tool_id
                    )
                )
            else:
                self.console.print(f"[red]Tool execution failed: {result.error}[/red]")
                
                # Add error to conversation
                messages.append(
                    LLMMessage(
                        role="tool",
                        content=f"Error: {result.error}",
                        tool_call_id=tool_id
                    )
                )
    
    async def execute_bash_command(self, command: str) -> bool:
        """Execute a bash command."""
        # Check if command is safe
        is_safe, warning = self.bash_executor.is_safe_command(command)
        if not is_safe:
            self.console.print(f"[red]Warning: {warning}[/red]")
            if not Confirm.ask("Execute anyway?"):
                return True
        
        # Execute the command
        exit_code, stdout, stderr = self.bash_executor.execute_command(
            command,
            timeout=self.config.get("terminal.timeout", 30)
        )
        
        # Display results
        if stdout:
            self.console.print(stdout)
        if stderr:
            self.console.print(f"[red]{stderr}[/red]")
        
        return True
    
    async def handle_special_command(self, command: str) -> bool:
        """Handle special commands starting with !."""
        parts = command.split()
        if not parts:
            return True
        
        cmd = parts[0].lower()
        
        if cmd == "help":
            self.show_help()
        elif cmd == "exit" or cmd == "quit":
            return False
        elif cmd == "providers":
            self.show_providers()
        elif cmd == "config":
            self.show_config()
        elif cmd == "mcp":
            await self.handle_mcp_command(parts[1:])
        elif cmd == "tools":
            await self.handle_tools_command(parts[1:])
        else:
            self.console.print(f"[red]Unknown command: !{command}[/red]")
            self.console.print("Type !help for available commands")
        
        return True
    
    def show_help(self):
        """Show help information."""
        help_text = """
[bold]Terminai Help[/bold]

[bold]Usage:[/bold]
  Just type commands or natural language descriptions

[bold]Examples:[/bold]
  ls -la                    # Execute bash command
  list all files           # Use AI with tools to list files
  find python files        # Use AI with tools to search
  read README.md          # Use AI with tools to read files

[bold]Special Commands:[/bold]
  !help                   Show this help
  !exit, !quit           Exit terminal
  !providers             Show available LLM providers
  !config                Show current configuration
  !mcp                   MCP server commands
  !tools                 Tool management commands

[bold]Configuration:[/bold]
  Edit ~/.terminai/config.json to configure LLM providers and tools
        """
        self.console.print(help_text)
    
    def show_providers(self):
        """Show available LLM providers."""
        providers = self.llm_manager.list_providers()
        configured = self.llm_manager.get_configured_providers(
            self.config._config
        )
        
        table = Table(title="Available LLM Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Configured", style="yellow")
        
        for provider in providers:
            is_configured = configured.get(provider, False)
            status = "✓" if is_configured else "✗"
            table.add_row(provider, status, str(is_configured))
        
        self.console.print(table)
    
    def show_config(self):
        """Show current configuration."""
        config = self.config._config
        self.console.print("[bold]Current Configuration:[/bold]")
        self.console.print(JSON.from_data(config))
    
    async def handle_tools_command(self, args: list):
        """Handle tool-related commands."""
        if not args:
            self.console.print("[bold]Tool Commands:[/bold]")
            self.console.print("  !tools list          List available tools")
            self.console.print("  !tools info <tool>   Show tool information")
            return
        
        cmd = args[0].lower()
        
        if cmd == "list":
            tools = self.tool_manager.list_tools()
            if tools:
                self.console.print("[bold]Available Tools:[/bold]")
                for tool in tools:
                    self.console.print(f"  - {tool}")
            else:
                self.console.print("[yellow]No tools available[/yellow]")
        
        elif cmd == "info" and len(args) > 1:
            tool_name = args[1]
            info = self.tool_manager.get_tool_info(tool_name)
            if info:
                self.console.print(f"[bold]Tool: {tool_name}[/bold]")
                self.console.print(f"Description: {info['description']}")
                self.console.print("[bold]Parameters:[/bold]")
                for param_name, param_info in info['parameters'].items():
                    required = "required" if param_info['required'] else "optional"
                    self.console.print(f"  {param_name} ({param_info['type']}, {required}): {param_info['description']}")
            else:
                self.console.print(f"[red]Tool '{tool_name}' not found[/red]")
    
    async def handle_mcp_command(self, args: list):
        """Handle MCP-related commands."""
        if not args:
            self.console.print("[bold]MCP Commands:[/bold]")
            self.console.print("  !mcp list          List connected servers")
            self.console.print("  !mcp tools <server> List tools from server")
            return
        
        cmd = args[0].lower()
        
        if cmd == "list":
            servers = self.mcp_client.get_connected_servers()
            if servers:
                self.console.print("[bold]Connected MCP Servers:[/bold]")
                for server in servers:
                    self.console.print(f"  - {server}")
            else:
                self.console.print("[yellow]No MCP servers connected[/yellow]")
        
        elif cmd == "tools" and len(args) > 1:
            server_name = args[1]
            try:
                tools = await self.mcp_client.list_tools(server_name)
                if tools:
                    self.console.print(f"[bold]Tools from {server_name}:[/bold]")
                    for tool in tools:
                        self.console.print(f"  - {tool.get('name', 'unknown')}")
                else:
                    self.console.print(f"[yellow]No tools available from {server_name}[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    async def run(self):
        """Run the terminal."""
        self.console.print("[bold green]Welcome to Terminai![/bold green]")
        self.console.print("Type !help for commands, or just start typing!")
        
        prompt = self.config.get_prompt()
        
        try:
            while True:
                try:
                    user_input = input(prompt)
                    if not await self.process_input(user_input):
                        break
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use !exit to quit[/yellow]")
                except EOFError:
                    break
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
        finally:
            await self.mcp_client.disconnect_all()
            self.console.print("[green]Goodbye![/green]")
