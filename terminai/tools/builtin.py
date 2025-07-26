"""Builtin tools for terminai."""

import os
import json
import re
from typing import Dict, Any, List
from pathlib import Path

from .manager import ToolManager, ToolResult


class BuiltinTools:
    """Builtin tools for file operations and command execution."""
    
    def __init__(self, bash_executor):
        """Initialize builtin tools."""
        self.bash_executor = bash_executor
    
    def register_all(self, tool_manager: ToolManager):
        """Register all builtin tools."""
        self._register_execute_command(tool_manager)
        self._register_read_file(tool_manager)
        self._register_write_to_file(tool_manager)
        self._register_replace_in_file(tool_manager)
        self._register_list_files(tool_manager)
        self._register_search_files(tool_manager)
    
    def _register_execute_command(self, tool_manager: ToolManager):
        """Register the execute_command tool."""
        tool_manager.register_tool(
            name="execute_command",
            description="Execute a bash command and return the output",
            parameters={
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                    "required": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "required": False
                }
            },
            executor=self._execute_command
        )
    
    async def _execute_command(self, command: str, timeout: int = 30) -> ToolResult:
        """Execute a bash command."""
        try:
            exit_code, stdout, stderr = self.bash_executor.execute_command(
                command,
                timeout=timeout
            )
            
            result = {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
            
            content = f"Command executed successfully\nExit code: {exit_code}\n"
            if stdout:
                content += f"Output:\n{stdout}\n"
            if stderr:
                content += f"Error:\n{stderr}\n"
            
            return ToolResult(
                success=True,
                content=content,
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _register_read_file(self, tool_manager: ToolManager):
        """Register the read_file tool."""
        tool_manager.register_tool(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                    "required": True
                }
            },
            executor=self._read_file
        )
    
    async def _read_file(self, path: str) -> ToolResult:
        """Read a file."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path is not a file: {path}"
                )
            
            content = file_path.read_text()
            return ToolResult(
                success=True,
                content=content,
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _register_write_to_file(self, tool_manager: ToolManager):
        """Register the write_to_file tool."""
        tool_manager.register_tool(
            name="write_to_file",
            description="Write content to a file",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                    "required": True
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                    "required": True
                },
                "append": {
                    "type": "boolean",
                    "description": "Whether to append to the file instead of overwriting",
                    "required": False
                }
            },
            executor=self._write_to_file
        )
    
    async def _write_to_file(self, path: str, content: str, append: bool = False) -> ToolResult:
        """Write content to a file."""
        try:
            file_path = Path(path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if append:
                with open(file_path, 'a') as f:
                    f.write(content)
                action = "Appended to"
            else:
                file_path.write_text(content)
                action = "Wrote to"
            
            return ToolResult(
                success=True,
                content=f"{action} file: {path}",
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _register_replace_in_file(self, tool_manager: ToolManager):
        """Register the replace_in_file tool."""
        tool_manager.register_tool(
            name="replace_in_file",
            description="Replace content in a file",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to modify",
                    "required": True
                },
                "old_content": {
                    "type": "string",
                    "description": "Content to search for (can be regex)",
                    "required": True
                },
                "new_content": {
                    "type": "string",
                    "description": "Content to replace with",
                    "required": True
                }
            },
            executor=self._replace_in_file
        )
    
    async def _replace_in_file(self, path: str, old_content: str, new_content: str) -> ToolResult:
        """Replace content in a file."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}"
                )
            
            content = file_path.read_text()
            
            # Try exact match first, then regex
            if old_content in content:
                new_content_str = content.replace(old_content, new_content)
            else:
                # Try regex replacement
                try:
                    new_content_str = re.sub(old_content, new_content, content)
                except re.error:
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Invalid regex pattern: {old_content}"
                    )
            
            file_path.write_text(new_content_str)
            
            return ToolResult(
                success=True,
                content=f"Replaced content in file: {path}",
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _register_list_files(self, tool_manager: ToolManager):
        """Register the list_files tool."""
        tool_manager.register_tool(
            name="list_files",
            description="List files and directories in a path",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                    "required": True
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively",
                    "required": False
                },
                "pattern": {
                    "type": "string",
                    "description": "File pattern to filter (e.g., '*.py')",
                    "required": False
                }
            },
            executor=self._list_files
        )
    
    async def _list_files(self, path: str, recursive: bool = False, pattern: str = None) -> ToolResult:
        """List files and directories."""
        try:
            base_path = Path(path)
            if not base_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path not found: {path}"
                )
            
            if not base_path.is_dir():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path is not a directory: {path}"
                )
            
            files = []
            if recursive:
                if pattern:
                    files = [str(p.relative_to(base_path)) for p in base_path.rglob(pattern)]
                else:
                    files = [str(p.relative_to(base_path)) for p in base_path.rglob('*') if p.is_file()]
            else:
                if pattern:
                    files = [str(p.name) for p in base_path.glob(pattern)]
                else:
                    files = [str(p.name) for p in base_path.iterdir()]
            
            content = "\n".join(sorted(files))
            return ToolResult(
                success=True,
                content=content,
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
    
    def _register_search_files(self, tool_manager: ToolManager):
        """Register the search_files tool."""
        tool_manager.register_tool(
            name="search_files",
            description="Search for files or content in files",
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (can be filename or content)",
                    "required": True
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in",
                    "required": True
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to search recursively",
                    "required": False
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to search in (e.g., '*.py')",
                    "required": False
                },
                "search_content": {
                    "type": "boolean",
                    "description": "Whether to search file content instead of filenames",
                    "required": False
                }
            },
            executor=self._search_files
        )
    
    async def _search_files(self, pattern: str, path: str, recursive: bool = True, file_pattern: str = None, search_content: bool = False) -> ToolResult:
        """Search for files or content."""
        try:
            base_path = Path(path)
            if not base_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path not found: {path}"
                )
            
            results = []
            
            if search_content:
                # Search file content
                search_files = base_path.rglob(file_pattern or '*') if recursive else base_path.glob(file_pattern or '*')
                
                for file_path in search_files:
                    if file_path.is_file():
                        try:
                            content = file_path.read_text()
                            if pattern in content:
                                results.append(str(file_path))
                        except (UnicodeDecodeError, PermissionError):
                            continue
            else:
                # Search filenames
                search_files = base_path.rglob('*') if recursive else base_path.iterdir()
                
                for file_path in search_files:
                    if file_path.is_file():
                        if file_pattern and not file_path.match(file_pattern):
                            continue
                        if pattern in str(file_path):
                            results.append(str(file_path))
            
            content = "\n".join(sorted(results))
            return ToolResult(
                success=True,
                content=content,
                error=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )
