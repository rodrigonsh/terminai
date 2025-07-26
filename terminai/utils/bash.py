"""Bash command execution utilities."""

import os
import subprocess
import shlex
import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BashExecutor:
    """Executes bash commands safely."""
    
    def __init__(self, shell: str = "/bin/bash"):
        """Initialize bash executor."""
        self.shell = shell
        self.forbidden_patterns = [
            r'rm\s+-rf\s+/$',
            r'rm\s+-rf\s+/\s',
            r'sudo\b',
            r'su\b',
        ]
    
    def is_bash_command(self, text: str) -> bool:
        """Determine if text is a bash command or natural language."""
        text = text.strip()
        
        # First, check for natural language indicators
        text_lower = text.lower()
        
        # Natural language indicators
        natural_language_indicators = [
            r'^please\b',  # starts with "please"
            r'^can you\b',  # starts with "can you"
            r'^could you\b',  # starts with "could you"
            r'^would you\b',  # starts with "would you"
            r'^what\b',  # starts with "what"
            r'^how\b',  # starts with "how"
            r'^where\b',  # starts with "where"
            r'^when\b',  # starts with "when"
            r'^why\b',  # starts with "why"
            r'^create a\b',  # starts with "create a"
            r'^make a\b',  # starts with "make a"
            r'^write a\b',  # starts with "write a"
            r'^find all\b',  # starts with "find all"
            r'^list all\b',  # starts with "list all"
            r'^show me\b',  # starts with "show me"
            r'^tell me\b',  # starts with "tell me"
        ]
        
        # Check for natural language indicators
        for pattern in natural_language_indicators:
            if re.match(pattern, text_lower):
                return False
        
        # Check for special characters that indicate natural language
        if text.startswith(('-', '*', '?', '!')):
            return False
        
        # Common bash command patterns - more specific patterns
        bash_patterns = [
            r'^[a-zA-Z][a-zA-Z0-9_-]*\s+',  # command with space and arguments
            r'^[a-zA-Z][a-zA-Z0-9_-]*$',   # single command
            r'^\.?/',                     # path
            r'^\.\s+',                    # dot command with space
            r'^ls\b', r'^cd\b', r'^pwd\b', r'^cat\b', r'^grep\b',
            r'^find\b', r'^mkdir\b', r'^rm\b', r'^cp\b', r'^mv\b',
            r'^echo\b', r'^printf\b', r'^head\b', r'^tail\b',
            r'^wc\b', r'^sort\b', r'^uniq\b', r'^cut\b', r'^awk\b',
            r'^sed\b', r'^tr\b', r'^xargs\b', r'^tar\b', r'^zip\b',
            r'^unzip\b', r'^curl\b', r'^wget\b', r'^git\b', r'^docker\b',
            r'^python\b', r'^python3\b', r'^node\b', r'^npm\b', r'^yarn\b',
            r'^chmod\b', r'^chown\b', r'^sudo\b', r'^apt\b', r'^apt-get\b',
            r'^systemctl\b', r'^service\b', r'^journalctl\b',
        ]
        
        # Check if it matches any bash pattern
        for pattern in bash_patterns:
            if re.match(pattern, text):
                return True
        
        # Check for pipes, redirects, or other bash operators
        bash_operators = ['|', '>', '<', '&&', '||', ';', '&', '$', '`', '$(', '${']
        for op in bash_operators:
            if op in text:
                return True
        
        # Additional check: if it has articles and natural language structure
        natural_language_words = ['a', 'an', 'the', 'and', 'or', 'but', 'with', 'for', 'to', 'from', 'in', 'on', 'at', 'by']
        words = text_lower.split()
        if len(words) > 3 and any(word in natural_language_words for word in words):
            return False
        
        return False
    
    def is_safe_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if command is safe to execute."""
        command = command.strip()
        
        # Check against forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command matches forbidden pattern: {pattern}"
        
        # Parse command to check for dangerous operations
        try:
            parts = shlex.split(command)
            if not parts:
                return True, None
            
            cmd = parts[0]
            
            # Check for dangerous commands
            dangerous_commands = {
                'rm': 'Use with caution - can delete files',
                'dd': 'Can overwrite disks',
                'chmod': 'Can change file permissions',
                'chown': 'Can change file ownership',
                'mkfs': 'Can format filesystems',
                'fdisk': 'Can modify disk partitions',
            }
            
            if cmd in dangerous_commands:
                return False, f"Potentially dangerous command: {dangerous_commands[cmd]}"
                
        except ValueError:
            # If shlex fails, it's probably a complex command
            pass
        
        return True, None
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute a bash command and return (exit_code, stdout, stderr)."""
        try:
            # Clean the command
            command = command.strip()
            if not command:
                return 0, "", ""
            
            # Execute the command with proper shell escaping
            process = subprocess.Popen(
                [self.shell, '-c', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return process.returncode, stdout, stderr
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return -1, "", f"Command timed out after {timeout} seconds"
                
        except Exception as e:
            return -1, "", str(e)
    
    def get_command_suggestion(self, natural_language: str) -> str:
        """Convert natural language to a bash command suggestion."""
        # This is a simple fallback - the actual conversion is done by LLM
        suggestions = {
            "list files": "ls -la",
            "show current directory": "pwd",
            "disk usage": "df -h",
            "memory usage": "free -h",
            "processes": "ps aux",
            "find text": "grep -r 'text' .",
            "create directory": "mkdir new_directory",
            "remove file": "rm filename",
            "copy file": "cp source destination",
            "move file": "mv source destination",
        }
        
        text = natural_language.lower().strip()
        for key, cmd in suggestions.items():
            if key in text:
                return cmd
        
        return f"echo 'No suggestion for: {natural_language}'"
