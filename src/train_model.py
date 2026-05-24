import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
import os

#logic is in two subspaces
#this prevents from software spikes
#sub electrical anomalies 

def train_security_models():
    #checks if the ground prep data exists before starting
    if not os.path.exists('data/raw_telemetry.csv') or not os.path.exists('models/scaler.joblib'):
        print("Error: Required data or scaler missing. Run prepare_data.py first.")
        return
    
    #loading data and setup
    df=pd.read_csv('data/raw_telemetry.csv')
    scaler=joblib.load('models/scaler.joblib')

    #transforming real data into a scaled values (around 0)
    #this is mandatory for the IsolationForest alg to calculate distance accurately
    df_scaled=pd.DataFrame(scaler.transform(df), columns=df.columns)

    #model A, for Electrical anomalies
    #watches V_bus (voltage) and I_total (current)
    elec_features=['V_bus', 'I_total']
    print(f'Status: Training Electrical Forest on {elec_features}...')

    #contamination=0.02 means I expect only 2% of normal power data to be noisy
    #satellites have very strict power budgets, so I keep this sensitivity high.
    m_elec=IsolationForest(n_estimators=100, contamination=0.02,random_state=42)
    m_elec.fit(df_scaled[elec_features])
    joblib.dump(m_elec, 'models/model_electrical.joblib')

    #Model B, Computational expert, watches CPU usage, Ram and Temp
    comp_features=['CPU_load', 'RAM_usage', 'MCU_temp']
    print(f'Status: training Computational Forest on {comp_features}...')

    #software load is more volatile than power, so we allow 5% noise contamination=0.05
    # this reduces 'false positives' during normal satellite data processing tasks
    m_comp=IsolationForest(n_estimators=100, contamination=0.05,random_state=42)
    m_comp.fit(df_scaled[comp_features])
    joblib.dump(m_comp, 'models/model_computational.joblib')

    print("Success: Dual-Forest models saved to /models folder")

if __name__ == "__main__":
    train_security_models()