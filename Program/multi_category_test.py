#!/usr/bin/env python3
"""
Multi-category test for Olive Young Crawler
"""

from oliveyoung_crawler_refactored import OliveYoungCrawler, RankingPeriod

def main():
    print("=" * 60)
    print("Multi-Category Test - Olive Young Crawler")
    print("=" * 60)
    
    # Test with multiple categories
    test_categories = ["all", "bodycare"]
    
    crawler = OliveYoungCrawler(
        headless=True,
        use_mobile=True,
        config={
            'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data/multi_test',
            'retry_attempts': 2,
            'retry_delay': 5
        }
    )
    
    try:
        print(f"\nCapturing {len(test_categories)} categories: {test_categories}")
        print("-" * 40)
        
        results = crawler.capture_all_rankings(
            categories=test_categories,
            period=RankingPeriod.REALTIME
        )
        
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        
        if results:
            print(f"✅ Successfully captured {len(results)} categories:")
            for category, path in results.items():
                print(f"   - {category}: {path}")
        else:
            print("❌ No screenshots were captured")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()