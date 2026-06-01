import socket
import json
import time
import os
import pandas as pd
from dotenv import load_dotenv

#local env
load_dotenv()

def simulate_bus(data_path='data/attack_telemetry.csv', port=5005):
    #setup udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    TARGET_HOST = os.getenv('AROS_DETECTOR_HOST', '127.0.0.1')
    TARGET_PORT = int(os.getenv('AROS_DETECTOR_PORT', 5005))

    server_address = (TARGET_HOST, TARGET_PORT)

    df=pd.read_csv(data_path)
    print(f"Satellite bus: streaming {len(df)} packets to port {port}...")

    for i, row in df.iterrows():
        #row to JSON (simulation of telemetry data)
        packet=json.dumps(row.to_dict()).encode('utf-8')
        sock.sendto(packet,server_address)

        print(f"Sent packet {i:03} to {server_address}")
        time.sleep(0.5)

if __name__=="__main__":
    simulate_bus()