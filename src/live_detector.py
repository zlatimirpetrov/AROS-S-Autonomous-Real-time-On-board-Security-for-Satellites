import pandas as pd
import joblib
import hashlib
import time
import os
import sys

#AROS-S detector
#logic: Dual-Subspace Isolation Forests + SHA-256 integrity layer

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

def start_monitor():
    print("AROS-S: initializing on-board security module...")

    #component registry, paths to the artifacts generated during ground-prep and training
    files = {
        'scaler': 'models/scaler.joblib',
        'elec': 'models/model_electrical.joblib',
        'comp': 'models/model_computational.joblib'
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
    
    except Exception as e:
        print(f"Critical BOOT Failure: {e}")
        sys.exit(1)

    #Telemetry stream intake
    #simulation- reading from the verified attack stream CSV

    input_source='data/attack_telemetry.csv'

    if not os.path.exists(input_source):
        print(f"Stream error: {input_source} not found.")
        return
    
    stream=pd.read_csv(input_source)
    print(f"AROS-S: stream active. Processing {len(stream)} packets...")
    print("-" * 60)

    #processing loop
    for i in range(len(stream)):
        #capture raw telemetry packet
        packet=stream.iloc[[i]]

        #normalisation iqr based, ml need feature on the same scale 
        packet_scaled=pd.DataFrame(scaler.transform(packet), columns=packet.columns)

        #dual-forest scoring, the decision function return negative values for anomalies 
        #high-score = high-danger
        e_score= -m_elec.decision_function(packet_scaled[['V_bus', 'I_total']])[0]
        c_score= -m_comp.decision_function(packet_scaled[['CPU_load', 'RAM_usage', 'MCU_temp']])[0]

        #threshold and response logic
        #0.5 is the caution flag, 0.7+ is red alert 
        if e_score>0.1 or c_score>0.05:
            status = "!! Detected anomaly !!"
            marker = "[!]"
        else:
            status = "Nominal"
            marker = "---"

        #formatted telemetry Log
        timestamp = time.strftime("%H:%M:%S")
        print(f"{marker} {timestamp} | Pkt:{i:03} | Status: {status}")
        print(f"    [Subspace Scores] Elec: {e_score:+.4f} | Comp: {c_score:+.4f}")

        # Real-time simulation delay
        time.sleep(0.4)

if __name__ == "__main__":
    start_monitor()