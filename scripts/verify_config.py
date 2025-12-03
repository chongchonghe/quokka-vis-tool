
import matplotlib
import matplotlib.pyplot as plt
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Import main to trigger the config changes
try:
    import main
    print(f"Backend: {matplotlib.get_backend()}")
    print(f"text.usetex: {matplotlib.rcParams['text.usetex']}")
    print(f"path.simplify: {matplotlib.rcParams['path.simplify']}")
    print(f"agg.path.chunksize: {matplotlib.rcParams['agg.path.chunksize']}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
