# MCP Server Configuration Examples

This file provides comprehensive examples of how to configure MCP (Model Context Protocol) servers for Terminai.

## Basic Configuration Format

MCP servers are configured in your `~/.terminai/config.json` file under the `mcp.servers` array:

```json
{
  "mcp": {
    "servers": [
      {
        "name": "server_name",
        "command": "command_to_execute",
        "args": ["arg1", "arg2"],
        "env": {
          "ENV_VAR": "value"
        }
      }
    ],
    "auto_discover": true
  }
}
```

## Available MCP Servers

### 1. Filesystem Server
Provides filesystem operations like reading, writing, and searching files.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

**Configuration:**
```json
{
  "name": "filesystem",
  "command": "mcp-server-filesystem",
  "args": ["/home/user", "/var/log"],
  "env": {}
}
```

### 2. GitHub Server
Provides GitHub API access for repositories, issues, and pull requests.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-github
```

**Configuration:**
```json
{
  "name": "github",
  "command": "mcp-server-github",
  "args": [],
  "env": {
    "GITHUB_TOKEN": "ghp_your_github_token_here"
  }
}
```

### 3. PostgreSQL Server
Provides PostgreSQL database operations.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-postgresql
```

**Configuration:**
```json
{
  "name": "postgresql",
  "command": "mcp-server-postgresql",
  "args": [],
  "env": {
    "POSTGRES_URL": "postgresql://username:password@localhost:5432/database_name"
  }
}
```

### 4. SQLite Server
Provides SQLite database operations.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-sqlite
```

**Configuration:**
```json
{
  "name": "sqlite",
  "command": "mcp-server-sqlite",
  "args": ["/path/to/database.db"],
  "env": {}
}
```

### 5. Brave Search Server
Provides web search capabilities using Brave Search API.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-brave-search
```

**Configuration:**
```json
{
  "name": "brave-search",
  "command": "mcp-server-brave-search",
  "args": [],
  "env": {
    "BRAVE_API_KEY": "your_brave_api_key"
  }
}
```

### 6. Web Search Server
Provides web search capabilities using SERP API.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-web-search
```

**Configuration:**
```json
{
  "name": "web-search",
  "command": "mcp-server-web-search",
  "args": [],
  "env": {
    "SERP_API_KEY": "your_serp_api_key"
  }
}
```

### 7. Fetch Server
Provides HTTP fetching capabilities for web content.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-fetch
```

**Configuration:**
```json
{
  "name": "fetch",
  "command": "mcp-server-fetch",
  "args": [],
  "env": {}
}
```

### 8. Memory Server
Provides persistent memory storage across sessions.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-memory
```

**Configuration:**
```json
{
  "name": "memory",
  "command": "mcp-server-memory",
  "args": [],
  "env": {}
}
```

### 9. Time Server
Provides current time and date information.

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-time
```

**Configuration:**
```json
{
  "name": "time",
  "command": "mcp-server-time",
  "args": [],
  "env": {}
}
```

## Complete Example Configuration

Here's a complete example of a `~/.terminai/config.json` file with multiple MCP servers configured:

```json
{
  "llm": {
    "default_provider": "openai",
    "providers": {
      "openai": {
        "type": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": "your-openai-api-key",
        "max_tokens": 150,
        "temperature": 0.1
      }
    }
  },
  "mcp": {
    "servers": [
      {
        "name": "filesystem",
        "command": "mcp-server-filesystem",
        "args": ["/home/user", "/var/log"],
        "env": {}
      },
      {
        "name": "github",
        "command": "mcp-server-github",
        "args": [],
        "env": {
          "GITHUB_TOKEN": "ghp_your_github_token_here"
        }
      },
      {
        "name": "fetch",
        "command": "mcp-server-fetch",
        "args": [],
        "env": {}
      },
      {
        "name": "memory",
        "command": "mcp-server-memory",
        "args": [],
        "env": {}
      }
    ],
    "auto_discover": true
  },
  "terminal": {
    "history_file": "~/.terminai/history",
    "max_history": 1000,
    "prompt": "terminai> ",
    "confirm_commands": true,
    "timeout": 30
  },
  "tools": {
    "enabled": true,
    "confirm_tool_calls": true,
    "builtin_tools": {
      "execute_command": true,
      "read_file": true,
      "write_to_file": true,
      "replace_in_file": true,
      "list_files": true,
      "search_files": true
    }
  }
}
```

## Testing MCP Servers

After configuring MCP servers, you can test them using these commands in Terminai:

- `!mcp list` - List all connected MCP servers
- `!mcp tools <server_name>` - List tools available from a specific server
- `!mcp resources <server_name>` - List resources available from a server

## Troubleshooting

1. **Server not found**: Ensure the MCP server is installed globally (`npm install -g <package>`)
2. **Permission errors**: Check file permissions for directories specified in `args`
3. **Environment variables**: Make sure required environment variables are set correctly
4. **Command not found**: Verify the command is in your PATH or use the full path to the executable

## Getting API Keys

- **GitHub**: Create a personal access token at https://github.com/settings/tokens
- **Brave Search**: Get an API key from https://brave.com/search/api
- **SERP**: Get an API key from https://serpapi.com
