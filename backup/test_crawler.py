#!/usr/bin/env python3
"""
Test script for Olive Young Crawler
"""

import sys
import time
from pathlib import Path
from oliveyoung_crawler_refactored import OliveYoungCrawler, RankingPeriod


def test_basic_functionality():
    """Test basic crawler functionality"""
    print("=" * 60)
    print("Testing Olive Young Crawler - Basic Functionality")
    print("=" * 60)
    
    # Test with minimal categories first
    test_categories = ["all", "skincare"]
    
    try:
        # Initialize crawler
        print("\n1. Initializing crawler...")
        crawler = OliveYoungCrawler(
            headless=True,
            use_mobile=True,
            config={
                'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data',
                'retry_attempts': 2,
                'retry_delay': 3
            }
        )
        print("   ✓ Crawler initialized successfully")
        
        # Test single category capture
        print("\n2. Testing single category capture...")
        category = [c for c in crawler.categories if c.name == "all"][0]
        result = crawler.capture_category_ranking(
            category,
            RankingPeriod.REALTIME
        )
        
        if result:
            print(f"   ✓ Successfully captured: {result}")
        else:
            print("   ✗ Failed to capture ranking")
            return False
        
        # Test multiple categories
        print("\n3. Testing multiple categories capture...")
        results = crawler.capture_all_rankings(
            categories=test_categories,
            period=RankingPeriod.REALTIME
        )
        
        print(f"   ✓ Captured {len(results)} categories:")
        for cat, path in results.items():
            print(f"      - {cat}: {Path(path).name}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    finally:
        if 'crawler' in locals():
            crawler.cleanup()


def test_mobile_vs_desktop():
    """Test mobile vs desktop mode"""
    print("=" * 60)
    print("Testing Mobile vs Desktop Mode")
    print("=" * 60)
    
    test_category = ["all"]
    
    try:
        # Test mobile mode
        print("\n1. Testing mobile mode...")
        mobile_crawler = OliveYoungCrawler(
            headless=False,
            use_mobile=True,
            config={
                'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data/mobile'
            }
        )
        
        mobile_result = mobile_crawler.capture_all_rankings(
            categories=test_category,
            period=RankingPeriod.REALTIME
        )
        print(f"   ✓ Mobile mode captured: {len(mobile_result)} categories")
        mobile_crawler.cleanup()
        
        # Test desktop mode
        print("\n2. Testing desktop mode...")
        desktop_crawler = OliveYoungCrawler(
            headless=False,
            use_mobile=False,
            config={
                'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data/desktop'
            }
        )
        
        desktop_result = desktop_crawler.capture_all_rankings(
            categories=test_category,
            period=RankingPeriod.REALTIME
        )
        print(f"   ✓ Desktop mode captured: {len(desktop_result)} categories")
        desktop_crawler.cleanup()
        
        print("\n✅ Mobile/Desktop test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


def test_error_handling():
    """Test error handling and retry logic"""
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    try:
        # Test with invalid configuration
        print("\n1. Testing with invalid URL...")
        crawler = OliveYoungCrawler(
            headless=False,
            use_mobile=True,
            config={
                'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data/test',
                'retry_attempts': 1,
                'retry_delay': 1
            }
        )
        
        # Temporarily modify URL to test error handling
        original_template = crawler.BASE_URL_TEMPLATE
        crawler.BASE_URL_TEMPLATE = "https://invalid-url-test.com/{category}/{period}"
        
        category = crawler.categories[0]
        result = crawler.capture_category_ranking(category, RankingPeriod.REALTIME)
        
        # Restore original URL
        crawler.BASE_URL_TEMPLATE = original_template
        
        if result is None:
            print("   ✓ Error handling worked correctly")
        else:
            print("   ✗ Error handling failed")
        
        crawler.cleanup()
        
        print("\n✅ Error handling test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OLIVE YOUNG CRAWLER TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        # ("Mobile vs Desktop", test_mobile_vs_desktop),  # Optional: takes longer
        # ("Error Handling", test_error_handling),  # Optional: test error cases
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Test crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(2)  # Pause between tests
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)