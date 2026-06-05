import os
import sys
import csv
import time
import hashlib
import numpy as np
import pandas as pd
import onnxruntime as ort
from src.bus_handler import TelemetryBus
from huggingface_hub import hf_hub_download

LOG_DIR="logs"
LOG_FILE=os.path.join(LOG_DIR, f"mission_log_{time.strftime('%Y%m%d_%H%M%S')}.csv")

#AROS-S detector
#logic: Dual-Subspace Isolation Forests + autoencoder (Layer 2) + SHA-256 integrity layer

#core model registry config
HF_REPO_ID = "zlatimirpetrov/aros-s-anomaly-detector"
MODEL_FILES = {
    'scaler': 'models/scaler.onnx',
    'elec': 'models/model_electrical.onnx',
    'comp': 'models/model_computational.onnx',
    'auto': 'models/model_autoencoder.onnx'
}

GOLDEN_SIGNATURES = {
    'scaler':'8990e325',
    'elec': 'd6bd510a',
    'comp': 'c4ededc3',
    'auto': '609cfd7f'
}

ELEC_THR = 0.03
COMP_THR = 0.025
MSE_THR  = 0.95

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

def log_telemetry(data_row):
    file_exists=os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=data_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_row)

def start_monitor(mode='UDP'):

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    print(f"AROS-S: initializing on-board security module in {mode} mode...")
    print(f"AROS-S: Resolving runtime artifacts from cloud registry [{HF_REPO_ID}]...")

    #hold the initialized C++ ONNX sessions
    sessions = {}

    #integrity loading, verify files exists and log their unique signatures for the mission log
    try:
        for name,repo_path in MODEL_FILES.items():
            #downloads/locates the file via the HF API cache mechanism
            try:
                local_cached_path=hf_hub_download(repo_id=HF_REPO_ID, filename=repo_path)
            except Exception as e:
                print(f"  HF unavailable ({e}); falling back to local {repo_path}")
                local_cached_path = repo_path

            sig=get_file_hash(local_cached_path)[:8]
            
            if sig != GOLDEN_SIGNATURES[name]:
                raise ValueError(
                    f"Critical tampered detected: Signature mismatch on asset '{name}'. "
                    f"Expected [{GOLDEN_SIGNATURES[name]}], but calculated [{sig}]. Execution halted."
                )
            
            print(f"Verified: {repo_path} -> Cached at edge [SHA-256 SIG: {sig}]")
            #compiles the mathematical graph into memory using an Inference Session
            sessions[name]= ort.InferenceSession(local_cached_path)

        print("All optimized ONNX sessions successfully initialized.")
    
    except Exception as e:
        print(f"Critical BOOT Failure during asset resolution: {e}")
        sys.exit(1)

    #unpacks our dictionary into explicit session handlers to keep downstream math clean
    s_scaler = sessions['scaler']
    s_elec = sessions['elec']
    s_comp = sessions['comp']
    s_auto = sessions['auto']

    bus = TelemetryBus(mode=mode)
    print(f"AROS-S: {mode} stream active. Listening for packets...")
    print("-" * 60)

    #enumerate to keep track of the packet count (Pkt:001, etc.)
    #the 'bus.stream()' generator handles the 'for' loop logic now
    for i, packet in enumerate(bus.stream()):

        feature_order = list(packet.columns)

        scaler_input_name = s_scaler.get_inputs()[0].name
        raw_input_matrix = packet.to_numpy().astype(np.float32)
        #execute the scaler graph across its input gate
        scaled_matrix = s_scaler.run(None, {scaler_input_name: raw_input_matrix})[0]
        
        #reconstruct the DataFrame 
        packet_scaled = pd.DataFrame(scaled_matrix, columns=feature_order)

        #2D float32 matrices
        elec_features = packet_scaled[['V_bus', 'I_total']].to_numpy().astype(np.float32)
        comp_features = packet_scaled[['CPU_load', 'RAM_usage', 'MCU_temp']].to_numpy().astype(np.float32)

        e_score = -s_elec.run(None, {s_elec.get_inputs()[0].name: elec_features})[1][0][0]
        c_score = -s_comp.run(None, {s_comp.get_inputs()[0].name: comp_features})[1][0][0]

        #global standardized array to float32
        auto_input_matrix = packet_scaled.to_numpy().astype(np.float32)
        #run data through the Autoencoder compression/decompression neural graph
        reconstruction = s_auto.run(None, {s_auto.get_inputs()[0].name: auto_input_matrix})[0]
        reconstruction = np.asarray(reconstruction).reshape(packet_scaled.shape)  #onnx returns (n*5,1) -> (n,5)
        
        mse = float(((packet_scaled.values - reconstruction) ** 2).mean())

        #hybrid threshold logic, if either layer flags an issue, trigger the alert
        #tuned to catch the +0.080 and +0.000 signatures seen in the live run
        is_forest_anomaly = (e_score > ELEC_THR or c_score > COMP_THR)
        is_neural_anomaly = (mse > MSE_THR)

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

        #persistence: save to flight recorder
        log_entry = packet.iloc[0].to_dict()
        log_entry.update({
            'timestamp': timestamp,
            'packet_id': i,
            'elec_score': round(e_score, 4),
            'comp_score': round(c_score, 4),
            'nn_mse': round(mse, 4),
            'status': status,
            'source': source
        })
        log_telemetry(log_entry)

        #real time simulation delay
        if mode=='CSV':
            time.sleep(0.4)

if __name__ == "__main__":
    start_monitor(mode='UDP')
    #start_monitor(mode='CSV')