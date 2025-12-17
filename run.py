#!/usr/bin/env python3
"""
Indian Legal Document Analyzer
Entry point for running the application
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Indian Legal Document Analyzer - RAG-based legal document analysis"
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Launch the Streamlit web interface"
    )
    parser.add_argument(
        "--cli", "-c",
        action="store_true", 
        help="Launch the command-line interface"
    )
    
    args = parser.parse_args()
    
    if args.cli:
        from app.cli import main as cli_main
        cli_main()
    else:
        # Default to web interface
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app/web_interface.py",
            "--server.headless", "true"
        ])


if __name__ == "__main__":
    main()
