#!/usr/bin/env python3
"""Main entry point for terminai."""

import asyncio
import sys
import argparse
from .terminal import TerminaiTerminal


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Terminai - Intelligent terminal with LLM integration")
    parser.add_argument("--config", help="Path to configuration directory")
    parser.add_argument("--version", action="version", version="terminai 0.1.0")
    
    args = parser.parse_args()
    
    try:
        terminal = TerminaiTerminal()
        asyncio.run(terminal.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
