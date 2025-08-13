#!/usr/bin/env python3
"""
Quick test for Olive Young Crawler
"""

from oliveyoung_crawler_refactored import OliveYoungCrawler, RankingPeriod

def main():
    print("=" * 60)
    print("Quick Test - Olive Young Crawler")
    print("=" * 60)
    
    # Test with just one category
    crawler = OliveYoungCrawler(
        headless=True,
        use_mobile=True,
        config={
            'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data/test',
            'retry_attempts': 2,
            'retry_delay': 3
        }
    )
    
    try:
        print("\nCapturing '전체' category ranking...")
        category = [c for c in crawler.categories if c.name == "all"][0]
        result = crawler.capture_category_ranking(category, RankingPeriod.REALTIME)
        
        if result:
            print(f"✅ Success! Screenshot saved to:")
            print(f"   {result}")
        else:
            print("❌ Failed to capture screenshot")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        crawler.cleanup()
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()