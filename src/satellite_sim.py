import socket
import json
import time
import pandas as pd

def simulate_bus(data_path='data/attack_telemetry.csv', port=5005):
    #setup udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address=('127.0.0.1', port)

    df=pd.read_csv(data_path)
    print(f"Satellite bus: streaming {len(df)} packets to port {port}...")

    for i, row in df.iterrows():
        #row to JSON (simulation of telemetry data)
        packet=row.to_json().encode('utf-8')
        sock.sendto(packet,server_address)

        if i % 5 == 0:
            print(f"Sent packet {i:03}...")
        time.sleep(0.5)  # 2Hz telemetry rate

if __name__=="__main__":
    simulate_bus()