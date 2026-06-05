import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import IsolationForest
import joblib
import os
from nasa_adapter import transform_smap_to_aros

FEATURES = ['V_bus', 'I_total', 'CPU_load', 'RAM_usage', 'MCU_temp']

def recalibrate_brain():
    print("Initiating calibration sequence...")

    if not os.path.exists('data/raw_telemetry.csv'):
        print("Error: data/raw_telemetry.csv missing.")
        return
    if not os.path.exists('data/nasa_smap_raw.csv'):
        print("Error: data/nasa_smap_raw.csv missing. Run nasa_smap_raw.py first.")
        return

    #original clean data
    clean_data=pd.read_csv('data/raw_telemetry.csv')[FEATURES]
    nasa_clean = transform_smap_to_aros(pd.read_csv('data/nasa_smap_raw.csv'))[FEATURES]

    combined = pd.concat([clean_data, nasa_clean], ignore_index=True)
    print(f"Combined dataset: {len(combined)} packets "
          f"({len(clean_data)} nominal + {len(nasa_clean)} NASA).")


    #refit the scaler consistent with prepare_data.py / train_model.py
    scaler = RobustScaler()
    scaled = pd.DataFrame(scaler.fit_transform(combined), columns=FEATURES)
    joblib.dump(scaler, 'models/scaler.joblib')
    print("New feature scaler saved.")


    #Isolation forest- electrical layer
    print("Training electrical isolation forest...")
    model_electrical = IsolationForest(contamination=0.01, random_state=42)
    model_electrical.fit(scaled[['V_bus', 'I_total']])
    joblib.dump(model_electrical, 'models/model_electrical.joblib')
    print("-> Saved updated model_electrical.joblib")

    #Isolation forest, computational layer
    print("Training computational isolation forest...")
    model_computational = IsolationForest(contamination=0.01, random_state=42)
    model_computational.fit(scaled[['CPU_load', 'RAM_usage', 'MCU_temp']])
    joblib.dump(model_computational, 'models/model_computational.joblib')
    print("-> Saved updated model_computational.joblib")

    #define the Autoencoder
    nn = MLPRegressor(hidden_layer_sizes=(3,), activation='relu', solver='adam',
                      max_iter=1500, random_state=42, early_stopping=False)
    nn.fit(scaled, scaled)
    joblib.dump(nn, 'models/model_autoencoder.joblib')
    print("Success: calibrated neural layer saved.")

    e = -model_electrical.decision_function(scaled[['V_bus', 'I_total']])
    c = -model_computational.decision_function(scaled[['CPU_load', 'RAM_usage', 'MCU_temp']])
    recon = nn.predict(scaled)
    mse = ((scaled.values - recon) ** 2).mean(axis=1)
    print("\n=== Suggested thresholds (99th percentile of NORMAL) ===")
    print(f"  elec > {np.percentile(e, 99):+.4f}")
    print(f"  comp > {np.percentile(c, 99):+.4f}")
    print(f"  mse  > {np.percentile(mse, 99):.4f}")

if __name__ == "__main__":
    recalibrate_brain()