import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import IsolationForest
import joblib
import os

def recalibrate_brain():
    print("Initiating calibration sequence...")

    if not os.path.exists('data/raw_telemetry.csv'):
        print("Error: data/raw_telemetry.csv missing.")
        return

    #original clean data
    clean_data=pd.read_csv('data/raw_telemetry.csv')

    #space noise script
    nasa_logs='logs/mission_log_20260531_150233.csv'
    if not os.path.exists(nasa_logs):
        print(f"Error: {nasa_logs} missing. Update the filename in the script.")
        return

    nasa_logs_df = pd.read_csv(nasa_logs)

    #filter the log to only include the raw telemetry columns
    nasa_clean = nasa_logs_df[['V_bus', 'I_total', 'CPU_load', 'RAM_usage', 'MCU_temp']]

    #the ml model will re learn that both nasa and stablility noise are normal behaviour 
    combined_training=pd.concat([clean_data, nasa_clean], ignore_index=True)
    print(f"Combined dataset ready: {len(combined_training)} total packets.")

    #refit the scaler 
    scaler= StandardScaler()
    scaled_data= scaler.fit_transform(combined_training)
    scaled_df = pd.DataFrame(scaled_data, columns=combined_training.columns)

    #save the new scaler
    joblib.dump(scaler, 'models/scaler.joblib')
    print("New feature scaler saved.")

    #Isolation forest- electrical layer
    print("Training electrical isolation forest...")
    model_electrical = IsolationForest(contamination=0.01, random_state=42)
    model_electrical.fit(scaled_df[['V_bus', 'I_total']])
    joblib.dump(model_electrical, 'models/model_electrical.joblib')
    print("-> Saved updated model_electrical.joblib")

    #Isolation forest, computational layer
    print("Training computational isolation forest...")
    model_computational = IsolationForest(contamination=0.01, random_state=42)
    model_computational.fit(scaled_df[['CPU_load', 'RAM_usage', 'MCU_temp']])
    joblib.dump(model_computational, 'models/model_computational.joblib')
    print("-> Saved updated model_computational.joblib")

    #define the Autoencoder
    nn_model = MLPRegressor(
        hidden_layer_sizes=(16, 8, 16),  #upgraded brain capacity
        activation='relu',
        solver='adam',
        max_iter=1500,
        random_state=42,
        early_stopping=False 
    )

    #train the brain to reconstruct both perfect data and nasa noise
    print("Training neural layer... this may take a moment.")
    nn_model.fit(scaled_df, scaled_df)

    #overwrite the old brain
    joblib.dump(nn_model, 'models/model_autoencoder.joblib')
    print("Success: calibrated Neural Layer saved to models/model_autoencoder.joblib")

if __name__ == "__main__":
    recalibrate_brain()