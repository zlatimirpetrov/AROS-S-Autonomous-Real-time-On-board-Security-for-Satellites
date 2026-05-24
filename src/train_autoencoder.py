import pandas as pd
import joblib
from sklearn.neural_network import MLPRegressor
import os

#aros-s neural layer training script (layer 2)

def train_neural_layer():
    print("AROS-S: Training Layer 2  (Neural Reconstruction)...")

    if not os.path.exists('data/raw_telemetry.csv') or not os.path.exists('models/scaler.joblib'):
        print("Error: required data or scaler missing. Run prepare_data.py first.")
        return
    
    #load normal layer and the scaler
    df=pd.read_csv('data/raw_telemetry.csv')
    scaler=joblib.load('models/scaler.joblib')
    df_scaled=pd.DataFrame(scaler.transform(df), columns=df.columns)

    #define the autoencoder,5 input senzors into a 3 neuron bottleneck, then rebuilds them
    nn_model = MLPRegressor(
        hidden_layer_sizes=(3,), 
        activation='relu',
        solver='adam',
        max_iter=1000,
        random_state=42,
        early_stopping=True  #stops training early if the model is optimized
    )

    #train: input (x) should perfectly equal Output (X) during normal behavior
    nn_model.fit(df_scaled, df_scaled)

    joblib.dump(nn_model, 'models/model_autoencoder.joblib')
    print("Success: neural layer saved to models/model_autoencoder.joblib")

if __name__=="__main__":
    train_neural_layer()