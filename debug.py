#!/usr/bin/env python
"""
SecureOps AI - Debug with LangSmith Studio

This script starts the LangGraph development server with LangSmith Studio integration.

Usage:
    python debug.py

The server will start on http://127.0.0.1:2024 and automatically connect to LangSmith Studio.
You can then test your agent directly in https://smith.langchain.com

Requirements:
    - langgraph-cli installed (pip install langgraph-cli)
    - .env file with LANGSMITH_API_KEY set
    - Agent code in src/graph.py
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


def main():
    print("=" * 70)
    print("SecureOps AI - LangGraph Studio Debug Mode")
    print("=" * 70)
    print()

    # Load environment
    load_dotenv()

    # Check requirements
    print("Checking requirements...")

    if not Path(".env").exists():
        print("[ERROR] ERROR: .env file not found")
        print("Please create .env with your API keys")
        sys.exit(1)

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("[ERROR] ERROR: LANGSMITH_API_KEY not set in .env")
        sys.exit(1)

    print("[OK] .env configured")
    print("[OK] LANGSMITH_API_KEY set")

    if not Path("langgraph.json").exists():
        print("[ERROR] ERROR: langgraph.json not found")
        sys.exit(1)

    print("[OK] langgraph.json found")

    if not Path("src/graph.py").exists():
        print("[ERROR] ERROR: src/graph.py not found")
        sys.exit(1)

    print("[OK] src/graph.py found")
    print()

    print("=" * 70)
    print("Starting LangGraph Development Server")
    print("=" * 70)
    print()
    print("Server will start on: http://127.0.0.1:2024")
    print("Studio will connect automatically")
    print()
    print("Next steps:")
    print("  1. Open https://smith.langchain.com")
    print("  2. Click 'Configure Studio connection'")
    print("  3. Enter Base URL: http://127.0.0.1:2024")
    print("  4. Click 'Connect'")
    print("  5. Your agent will appear in the graph view")
    print("  6. Test your agent in the playground")
    print("  7. Edit code and changes will hot-reload")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    print("-" * 70)
    print()

    try:
        # Start LangGraph dev server using langgraph-cli
        subprocess.run(
            [sys.executable, "-m", "langgraph_cli", "dev"],
            check=False
        )
    except KeyboardInterrupt:
        print()
        print("Server stopped")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
