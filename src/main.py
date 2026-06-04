import pandas as pd
import numpy as np

def start_engine():
    print("=========================================")
    print("AROS-S Starting...")
    print("Loading dependencies...")
    
    test_array = np.array([1, 2, 3])
    print(f"NumPy is active. Test array: {test_array}")
    print("=========================================")
    print("Waiting for satellite telemetry...")

if __name__ == "__main__":
    start_engine()