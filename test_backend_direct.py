#!/usr/bin/env python3
"""
Quick backend test - run this to check for import/startup errors
"""

print("=" * 60)
print("Backend Import Test")
print("=" * 60)
print()

print("Testing imports...")
try:
    print("  ✓ Importing FastAPI...")
    from fastapi import FastAPI, HTTPException
    print("  ✓ Importing socket...")
    import socket
    print("  ✓ Importing os...")
    import os
    print("  ✓ Importing sys...")
    import sys
    print("  ✓ Importing logging...")
    import logging
    print("  ✓ Importing yt...")
    import yt
    print("  ✓ All imports successful!")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("Testing socket...")
try:
    hostname = socket.gethostname()
    print(f"  ✓ Hostname: {hostname}")
except Exception as e:
    print(f"  ✗ Socket error: {e}")
    exit(1)

print()
print("Testing file system...")
try:
    cwd = os.getcwd()
    print(f"  ✓ Current directory: {cwd}")
    
    # Test path operations
    test_path = "/tmp"
    exists = os.path.exists(test_path)
    print(f"  ✓ Path test ({test_path}): exists={exists}")
except Exception as e:
    print(f"  ✗ Filesystem error: {e}")
    exit(1)

print()
print("Loading backend module...")
try:
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.join(backend_dir, 'backend'))
    print(f"  Changed to: {os.getcwd()}")
    
    print("  Importing main module...")
    import main
    print(f"  ✓ Module loaded successfully")
    print(f"  ✓ App object: {main.app}")
    print(f"  ✓ DATA_DIR: {main.DATA_DIR}")
except Exception as e:
    print(f"  ✗ Module load failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("✓ All tests passed!")
print("=" * 60)
print()
print("If this works, the issue is likely in uvicorn startup.")
print("Try running:")
print("  cd backend")
print("  python -c 'import main; print(main.app)'")
print()

