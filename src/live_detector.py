import pandas as pd
import joblib
import hashlib
import time
import os
import sys
from bus_handler import TelemetryBus

#AROS-S detector
#logic: Dual-Subspace Isolation Forests + autoencoder (Layer 2) + SHA-256 integrity layer

def get_file_hash(path):
    """
    generates SHA-256 checksum for model verification
    prevents model injection attacks where the brain is changed
    """
    sha256=hashlib.sha256()
    with open(path, "rb") as f:
        while chunk :=f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def start_monitor(mode='UDP'):
    print(f"AROS-S: initializing on-board security module in {mode} mode...")

    #component registry, paths to the artifacts generated during ground-prep and training
    files = {
        'scaler': 'models/scaler.joblib',
        'elec': 'models/model_electrical.joblib',
        'comp': 'models/model_computational.joblib',
        'auto': 'models/model_autoencoder.joblib'
    }

    #integrity loading, verify files exists and log their unique signatures for the mission log
    try:
        for name,path in files.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing {name} artifact.")
            
            sig=get_file_hash(path) [:8]  #log short-hash
            print(f"Verified: {path} [SIG:{sig}]")

        scaler=joblib.load(files['scaler'])
        m_elec=joblib.load(files['elec'])
        m_comp=joblib.load(files['comp'])
        m_auto = joblib.load(files['auto'])
    
    except Exception as e:
        print(f"Critical BOOT Failure: {e}")
        sys.exit(1)

    bus = TelemetryBus(mode=mode)
    print(f"AROS-S: {mode} stream active. Listening for packets...")
    print("-" * 60)

    #enumerate to keep track of the packet count (Pkt:001, etc.)
    #the 'bus.stream()' generator handles the 'for' loop logic now
    for i, packet in enumerate(bus.stream()):

        #normalisation iqr based, ml need feature on the same scale 
        packet_scaled=pd.DataFrame(scaler.transform(packet), columns=packet.columns)

        #dual-forest scoring, the decision function return negative values for anomalies 
        #high-score = high-danger
        e_score= -m_elec.decision_function(packet_scaled[['V_bus', 'I_total']])[0]
        c_score= -m_comp.decision_function(packet_scaled[['CPU_load', 'RAM_usage', 'MCU_temp']])[0]

        #Layer 2 neural net autoencoder (pattern breakdown)
        reconstruction=m_auto.predict(packet_scaled)
        #mean squared error, how badly the nn fails to rebuild the data
        mse= ((packet_scaled.values-reconstruction)**2).mean()

        # hybrid threshold logic, if either layer flags an issue, trigger the alert
        is_forest_anomaly=(e_score>0.1 or c_score>0.05)
        is_neural_anomaly=(mse > 0.2) #0.2 is a strict threshold for reconstruction error

        if is_forest_anomaly or is_neural_anomaly:
            status="! Detected anomaly !"
            marker="[!]"
            #identify which layer triggered the alarm
            if is_forest_anomaly:
                source= "Forest" 
            else:
                source="Neural Net"
        else:
            status="Nominal"
            marker="---"
            source="System"

        #formatted telemetry Log
        timestamp = time.strftime("%H:%M:%S")
        print(f"{marker} {timestamp} | Pkt:{i:03} | Status: {status} [{source}]")
        print(f"    [Scores] Elec: {e_score:+.3f} | Comp: {c_score:+.3f} | NN-MSE: {mse:.4f}")

        #real time simulation delay
        if mode=='CSV':
            time.sleep(0.4)

if __name__ == "__main__":
    start_monitor(mode='UDP')
    #start_monitor(mode='CSV')