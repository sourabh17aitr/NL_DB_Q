"""
Example usage of the NL2SQL Agent Workflow

This script demonstrates how to use the agent workflow to query a database
using natural language.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent_workflow import run_nl2sql_query


def main():
    """Run example queries."""
    
    print("=" * 80)
    print("NL2SQL Agent Workflow - Example Usage")
    print("=" * 80)
    
    # Example queries
    queries = [
        "How many customers do we have?",
        "List the top 5 products by sales",
        "Show me all employees in the Sales department"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Example {i}: {query}")
        print(f"{'=' * 80}\n")
        
        try:
            result = run_nl2sql_query(query)
            
            print("\nFINAL RESPONSE:")
            print("-" * 80)
            print(result["final_response"])
            
            print("\nGENERATED SQL:")
            print("-" * 80)
            print(result["generated_query"])
            
            if result.get("retry_count", 0) > 0:
                print(f"\nNote: Query was retried {result['retry_count']} time(s)")
            
        except Exception as e:
            print(f"Error executing query: {str(e)}")
        
        print()
    
    print("=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
