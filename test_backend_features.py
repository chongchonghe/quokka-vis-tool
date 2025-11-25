import requests
import os
import sys

# Configuration
BASE_URL = "http://localhost:9010"
DATASET_NAME = "plt00000" # Assuming this exists or will be found
OUTPUT_DIR = "test_output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def test_load_dataset():
    print("Testing load_dataset...")
    # First get datasets to find a valid one
    res = requests.get(f"{BASE_URL}/api/datasets")
    datasets = res.json().get("datasets", [])
    if not datasets:
        print("No datasets found!")
        return None
    
    dataset = datasets[0]
    print(f"Loading dataset: {dataset}")
    res = requests.post(f"{BASE_URL}/api/load_dataset?filename={dataset}")
    if res.status_code == 200:
        print("Success")
        return dataset
    else:
        print(f"Failed: {res.text}")
        return None

def test_fields():
    print("Testing fields...")
    res = requests.get(f"{BASE_URL}/api/fields")
    if res.status_code == 200:
        fields = res.json().get("fields", [])
        print(f"Fields found: {len(fields)}")
        if "temperature" in fields:
            print("Derived field 'temperature' found!")
        else:
            print("Derived field 'temperature' NOT found!")
    else:
        print(f"Failed: {res.text}")

def test_plot(dataset, filename, params):
    print(f"Testing plot: {filename}...")
    url = f"{BASE_URL}/api/slice"
    res = requests.get(url, params=params)
    if res.status_code == 200:
        with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
            f.write(res.content)
        print(f"Saved {filename}")
    else:
        print(f"Failed: {res.text}")

def main():
    dataset = test_load_dataset()
    if not dataset:
        return

    test_fields()

    # Test 1: Basic Slice with Derived Field (Temperature)
    test_plot(dataset, "temperature_slice.png", {
        "field": "temperature",
        "kind": "slc",
        "cmap": "hot"
    })

    # Test 2: Projection Plot
    test_plot(dataset, "density_projection.png", {
        "field": "density",
        "kind": "prj",
        "weight_field": "None"
    })

    # Test 3: Projection Plot with Weight
    test_plot(dataset, "temperature_projection_weighted.png", {
        "field": "temperature",
        "kind": "prj",
        "weight_field": "density",
        "cmap": "hot"
    })

    # Test 4: Width Control
    test_plot(dataset, "zoomed_slice.png", {
        "field": "density",
        "width_value": 0.5,
        "width_unit": "cm" # Assuming cm is valid, or whatever unit the dataset has. 
                           # If dataset is cosmological, might need kpc/Mpc.
                           # Let's try without unit first if it fails? 
                           # Actually, let's just try a small value.
                           # If unit is wrong, yt might complain.
                           # We'll assume code units if unit is missing? 
                           # My code requires both value and unit.
                           # Let's try 'cm' as it's standard.
    })

    # Test 5: Annotations
    test_plot(dataset, "annotations.png", {
        "field": "density",
        "grids": "true",
        "cell_edges": "true",
        "timestamp": "true",
        "top_left_text": "Top Left",
        "top_right_text": "Top Right"
    })

if __name__ == "__main__":
    main()
