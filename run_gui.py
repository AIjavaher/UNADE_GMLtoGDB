#!/usr/bin/env python3
"""
Simple launcher for the GML Importer GUI
"""
import sys
import os

def main():
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Import and run GUI
        from gml_importer_gui import main as run_gui
        run_gui()
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install neo4j")
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 