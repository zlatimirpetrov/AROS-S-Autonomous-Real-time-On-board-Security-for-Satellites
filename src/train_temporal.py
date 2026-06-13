import os, sys
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
import joblib

BASE= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC= os.path.join(BASE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
from nasa_adapter import transform_smap_to_aros

DATA=os.path.join(BASE, "data")
MODELS=os.path.join(BASE,"models")
F=["V_bus", "I_total", "CPU_load", "RAM_usage", "MCU_temp"]
W=10
SEED=42

def make_windows(scaled, w=W):
    arr=scaled.values if hasattr(scaled, "values") else np.asarray(scaled)
    n=len(arr)
    if n < w:
        return np.empty((0, w * arr.shape[1]))
    out = np.stack([arr[i:i + w] for i in range(n - w + 1)])
    return out.reshape(out.shape[0], -1)

def main():
    scaler = joblib.load(os.path.join(MODELS, "scaler.joblib"))
    nominal = pd.read_csv(os.path.join(DATA, "raw_telemetry.csv"))[F]
    nasa = transform_smap_to_aros(pd.read_csv(os.path.join(DATA, "nasa_smap_raw.csv")))[F]

    Zn = pd.DataFrame(scaler.transform(nominal), columns=F)
    Zk = pd.DataFrame(scaler.transform(nasa),    columns=F)

    Xn = make_windows(Zn)
    Xk = make_windows(Zk)
    X  = np.vstack([Xn, Xk])
    print(f"Training windows: {len(X)}  (window={W}, input dim={W*len(F)})")

    ae = MLPRegressor(hidden_layer_sizes=(8,), activation="relu", solver="adam",
                      max_iter=2000, random_state=SEED)
    ae.fit(X, X)
    joblib.dump(ae, os.path.join(MODELS, "model_temporal.joblib"))
    print("Saved models/model_temporal.joblib")
    # threshold MUST cover BOTH normal regimes, not nominal only
    mse_all = ((X - ae.predict(X)) ** 2).mean(axis=1)
    print(f"\nSuggested TEMP_THR (99th pct of ALL normal windows): {np.percentile(mse_all, 99):.4f}")
    mse_n = ((Xn - ae.predict(Xn)) ** 2).mean(axis=1)
    mse_k = ((Xk - ae.predict(Xk)) ** 2).mean(axis=1)
    print(f"  nominal windows p50/p90/p99: {np.round(np.percentile(mse_n,[50,90,99]),4)}")
    print(f"  NASA    windows p50/p90/p99: {np.round(np.percentile(mse_k,[50,90,99]),4)}")

if __name__ == "__main__":
    main()