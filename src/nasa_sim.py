import socket
import time
import os
import pandas as pd
from nasa_adapter import transform_smap_to_aros

def run_ghost_mission():

    if not os.path.exists('data/nasa_smap_raw.csv'):
        print("Error: data/nasa_smap_raw.csv not found.")
        return

    #loading the raw nasa data
    nasa_raw=pd.read_csv('data/nasa_smap_raw.csv')
    #transforming via adapter
    aros_telemetry=transform_smap_to_aros(nasa_raw)

    #UDP bridge
    sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #env your machine ip
    TARGET_HOST = os.getenv('AROS_DETECTOR_HOST', '127.0.0.1')
    TARGET_PORT = int(os.getenv('AROS_DETECTOR_PORT', 5005))

    server_address = (TARGET_HOST, TARGET_PORT)
    print(f"Commencing ghost run: beaming {len(aros_telemetry)} NASA derived packets...")
    print(f"Target: {server_address}")

    try:
        for i in range(len(aros_telemetry)):
            packet_json=aros_telemetry.iloc[[i]].to_json(orient='records')
            #clean up the string: to_json(orient='records') returns '[{...}]'
            #just '{...}'
            packet_data = packet_json[1:-1].encode()
            sock.sendto(packet_data,server_address)
            #progress
            if i%50 == 0:
                print(f"Sent {i}/{len(aros_telemetry)} packets...")

            time.sleep(0.3)

    except Exception as e:
        print(f"Transmission failed: {e}")
    finally:
        sock.close()
        print("Mission Complete.")

if __name__ == "__main__":
    run_ghost_mission()