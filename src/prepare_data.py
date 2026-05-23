import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
import joblib
import os

#I use RobustScaler here instead of StandardScaler.
#satellite sensors are prone to random noise. RobustScaler uses the Interquartile Range "IQR", making the baseline 
#resilient to random sensor glitches that aren't actually attacks.

def generate_telemetry(row_count=2000):
    """
    gens a synthetic dataset representing a healthy sat state.
    mapping these to the 5 core features defined in the SDD.
    """
    np.random.seed(42) #for testing

    data = {
        'V_bus': np.random.normal(28.0, 0.15, row_count), # 28V rail
        'I_total': np.random.normal(1.1, 0.05, row_count), # ~1.1 Amps draw
        'CPU_load': np.random.uniform(5, 20, row_count),    # low idle load
        'RAM_usage': np.random.uniform(120, 150, row_count), # mb
        'MCU_temp': np.random.normal(32.0, 1.5, row_count)  # 32°C nominal temp
    }
    return pd.DataFrame(data)

def run_ground_prep():
    #folder structure check
    #'data' for CSVs and models for the exported Scaler
    for path in ['data', 'models']:
        if not os.path.exists(path):
            os.makedirs(path)
    print("AROS-S: Loading baseline telemetry...")

    #normal data
    #df = pd.read_csv('nasa_smap_raw.csv')
    df = generate_telemetry()

    #Init the scaler
    #most important part of the pipeline
    #calcs the median and IQR of 'normal' behavior.
    scaler = RobustScaler()
    scaler.fit(df)

    # saving the artifacts
    df.to_csv('data/raw_telemetry.csv', index=False)

    # satellite Docker needs to use the same parameters to scale live data
    joblib.dump(scaler, 'models/scaler.joblib')

    print(f"Status: OK. Exported {len(df)} samples to data/ and scaler to models/.")

if __name__ == "__main__":
    run_ground_prep()