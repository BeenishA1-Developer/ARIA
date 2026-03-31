#!/usr/bin/env python3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set paths
base_dir = Path(__file__).parent
sys.path.append(str(base_dir))
load_dotenv(base_dir / ".env")

from core.poster import WPPoster

def test_manual():
    print("Initializing Poster...")
    p = WPPoster()
    print(f"Site Type: {p.type}")
    print(f"Is Connected: {p.is_connected}")
    
    if not p.is_connected:
        print("ERROR: Connection failed!")
        return

    data = {
        "title": "AstraZeneca Internship 2025-26",
        "content": "<p>This is a manual test post for the blogging agent.</p>",
        "meta_description": "Manual test for blogging agent",
        "tags": ["test", "intership"]
    }
    
    print("\nAttempting to post...")
    res = p.post_to_wordpress(data)
    print(f"\nRESULT: {res}")

if __name__ == "__main__":
    test_manual()
