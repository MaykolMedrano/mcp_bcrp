"""
Example: Fetching Economic Data from BCRP

This script demonstrates how to use mcp-bcrp as a Python library.
"""
import asyncio
from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata


async def main():
    # 1. Search for an indicator
    print("=== Searching for 'tasa politica monetaria' ===")
    metadata = BCRPMetadata()
    await metadata.load()
    
    result = metadata.solve("tasa politica monetaria")
    print(f"Result: {result}")
    
    if "codigo_serie" in result:
        code = result["codigo_serie"]
        print(f"\nFound: {code} (Confidence: {result['confidence']})")
        
        # 2. Fetch the data
        print(f"\n=== Fetching data for {code} ===")
        client = AsyncBCRPClient()
        df = await client.get_series([code], "2024-01", "2024-12")
        print(df.to_markdown())
    
    # 3. Fetch multiple series (Copper price)
    print("\n=== Copper Price (PN01652XM) ===")
    client = AsyncBCRPClient()
    copper_df = await client.get_series(["PN01652XM"], "2024-06", "2024-12")
    print(copper_df.to_markdown())


if __name__ == "__main__":
    asyncio.run(main())
