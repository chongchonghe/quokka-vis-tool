#!/usr/bin/env python3
"""Test script to verify the refactored plot generation with annotations."""

import requests
import os

BASE_URL = "http://localhost:9010"

def test_annotations():
    """Test grids, timestamp, and particles annotations."""
    
    print("Testing refactored plot generation with annotations...")
    
    # Load dataset
    print("\n1. Loading dataset...")
    response = requests.post(f"{BASE_URL}/api/load_dataset?filename=plt10240")
    if response.status_code == 200:
        print("✓ Dataset loaded successfully")
    else:
        print(f"✗ Failed to load dataset: {response.status_code}")
        return
    
    # Test 1: Slice with grids
    print("\n2. Testing slice with grids...")
    url = f"{BASE_URL}/api/slice?axis=z&field=density&kind=slc&grids=true&show_colorbar=true&log_scale=true&cmap=viridis"
    response = requests.get(url)
    if response.status_code == 200:
        with open("test_grids.png", "wb") as f:
            f.write(response.content)
        print("✓ Saved test_grids.png")
    else:
        print(f"✗ Failed: {response.status_code}")
    
    # Test 2: Slice with timestamp
    print("\n3. Testing slice with timestamp...")
    url = f"{BASE_URL}/api/slice?axis=z&field=density&kind=slc&timestamp=true&show_colorbar=true&log_scale=true&cmap=viridis"
    response = requests.get(url)
    if response.status_code == 200:
        with open("test_timestamp.png", "wb") as f:
            f.write(response.content)
        print("✓ Saved test_timestamp.png")
    else:
        print(f"✗ Failed: {response.status_code}")
    
    # Test 3: Slice with grids AND timestamp
    print("\n4. Testing slice with grids AND timestamp...")
    url = f"{BASE_URL}/api/slice?axis=z&field=density&kind=slc&grids=true&timestamp=true&show_colorbar=true&log_scale=true&cmap=viridis"
    response = requests.get(url)
    if response.status_code == 200:
        with open("test_grids_timestamp.png", "wb") as f:
            f.write(response.content)
        print("✓ Saved test_grids_timestamp.png")
    else:
        print(f"✗ Failed: {response.status_code}")
    
    # Test 4: Projection with particles (if they exist)
    print("\n5. Testing projection with particles...")
    url = f"{BASE_URL}/api/slice?axis=z&field=density&kind=prj&particles=StochasticStellarPop_particles&show_colorbar=true&log_scale=true&cmap=viridis"
    response = requests.get(url)
    if response.status_code == 200:
        with open("test_particles.png", "wb") as f:
            f.write(response.content)
        print("✓ Saved test_particles.png")
    else:
        print(f"✗ Failed: {response.status_code}")
    
    # Test 5: Scale bar
    print("\n6. Testing scale bar...")
    url = f"{BASE_URL}/api/slice?axis=z&field=density&kind=slc&show_scale_bar=true&show_colorbar=true&log_scale=true&cmap=viridis"
    response = requests.get(url)
    if response.status_code == 200:
        with open("test_scale_bar.png", "wb") as f:
            f.write(response.content)
        print("✓ Saved test_scale_bar.png")
    else:
        print(f"✗ Failed: {response.status_code}")
    
    print("\n✓ All tests completed! Check the generated PNG files.")

if __name__ == "__main__":
    test_annotations()
