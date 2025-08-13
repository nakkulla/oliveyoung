#!/usr/bin/env python3
"""Test script for the modified Olive Young crawler with only two URLs"""

from oliveyoung_crawler_refactored import OliveYoungCrawler
import json

def test_two_urls():
    """Test the crawler with the two specific URLs only"""
    
    print("Starting test with modified crawler (2 URLs only)")
    print("-" * 50)
    
    # Create crawler instance with mobile emulation
    crawler = OliveYoungCrawler(
        headless=False,  # Set to False to see the browser during testing
        use_mobile=True
    )
    
    try:
        # Run crawler - it will automatically use the two defined URLs
        results = crawler.run()
        
        print("\n" + "="*50)
        print("Capture Results:")
        print("="*50)
        
        for category, path in results.items():
            print(f"✓ {category}: {path}")
        
        print("\n" + "="*50)
        print(f"Total categories captured: {len(results)}")
        print("="*50)
        
        # Verify we only have 2 results
        if len(results) == 2:
            print("✅ Correct number of categories captured (2)")
        else:
            print(f"❌ Expected 2 categories, got {len(results)}")
        
        if "bodycare" in results:
            print("✅ Bodycare category captured successfully")
        else:
            print("❌ Missing bodycare category")
            
        if "all" in results:
            print("✅ All (전체 랭킹) category captured successfully")
        else:
            print("❌ Missing all category")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        raise
    finally:
        crawler.cleanup()

if __name__ == "__main__":
    test_two_urls()