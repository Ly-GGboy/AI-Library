#!/usr/bin/env python3

import argparse
import sys
import traceback
from duckduckgo_search import DDGS

def search(query, max_results=10):
    """
    Search using DuckDuckGo and return results with URLs and text snippets.
    Uses the HTML backend which has proven to be more reliable.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
    """
    try:
        print(f"DEBUG: Searching for query: {query}", file=sys.stderr)
        
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=max_results,
                backend='html'  # Use only the HTML backend
            ))
            
            if not results:
                print("DEBUG: No results found", file=sys.stderr)
                return
            
            print(f"DEBUG: Found {len(results)} results", file=sys.stderr)
            
            for i, r in enumerate(results, 1):
                print(f"\n=== Result {i} ===")
                print(f"URL: {r.get('link', r.get('href', 'N/A'))}")
                print(f"Title: {r.get('title', 'N/A')}")
                print(f"Snippet: {r.get('snippet', r.get('body', 'N/A'))}")
                
    except Exception as e:
        print(f"ERROR: Search failed: {str(e)}", file=sys.stderr)
        print(f"ERROR type: {type(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Search using DuckDuckGo API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10,
                      help="Maximum number of results (default: 10)")
    
    args = parser.parse_args()
    search(args.query, args.max_results)

if __name__ == "__main__":
    main() 