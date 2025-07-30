#!/usr/bin/env python3
"""
Simple multiprocessing test for macOS M2
"""

import multiprocessing as mp
import time
import os

def worker_function(x):
    """Simple worker function for testing."""
    process_id = os.getpid()
    time.sleep(0.1)  # Simulate some work
    return f"Process {process_id} processed {x}"

def test_multiprocessing():
    """Test if multiprocessing works on this system."""
    print(f"Testing multiprocessing on macOS M2...")
    print(f"CPU count: {mp.cpu_count()}")
    print(f"Default start method: {mp.get_start_method()}")
    
    # Test data
    test_data = list(range(10))
    
    # Test with Pool
    print(f"\nTesting with Pool...")
    start_time = time.time()
    
    with mp.Pool(processes=4) as pool:
        results = pool.map(worker_function, test_data)
    
    end_time = time.time()
    print(f"Pool test completed in {end_time - start_time:.2f} seconds")
    print(f"Results: {results[:3]}...")  # Show first 3 results
    
    return True

if __name__ == "__main__":
    try:
        test_multiprocessing()
        print("✅ Multiprocessing test PASSED")
    except Exception as e:
        print(f"❌ Multiprocessing test FAILED: {e}")
        import traceback
        traceback.print_exc() 