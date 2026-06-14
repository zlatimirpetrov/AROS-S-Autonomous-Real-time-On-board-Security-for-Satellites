import socket
import json
import time
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from attack_sim import create_malicious_telemetry
from secure_cmd import verify

#local env
load_dotenv()


def safe_packet():
    """nominal telemetry the spacecraft emits once it has recovered."""
    return {
        "V_bus":     float(np.random.normal(28.0, 0.1)),
        "I_total":   float(np.random.normal(1.1, 0.03)),
        "CPU_load":  float(np.random.uniform(8, 15)),
        "RAM_usage": float(np.random.uniform(125, 140)),
        "MCU_temp":  float(np.random.normal(31.0, 0.8)),
    }


def simulate_bus(data_path='data/attack_telemetry.csv', port=5005):
    #creating malicious telemetry
    create_malicious_telemetry()
    #setup udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    TARGET_HOST = os.getenv('AROS_DETECTOR_HOST', '127.0.0.1')
    TARGET_PORT = int(os.getenv('AROS_DETECTOR_PORT', 5005))

    server_address = (TARGET_HOST, TARGET_PORT)

    #return channel: listen for AROS-S telecommands (non-blocking)
    cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    cmd_sock.bind(("0.0.0.0", int(os.getenv("AROS_CMD_PORT", 5006))))
    cmd_sock.setblocking(False)
    recovered = False

    #read the generated telemetry
    if not os.path.exists(data_path):
        print(f"Error: {data_path} was not generated successfully.")
        return

    df = pd.read_csv(data_path)
    print(f"Satellite bus: streaming {len(df)} packets to port {port}...")

    for i, row in df.iterrows():
        #check for an authenticated telecommand from AROS-S
        try:
            data, _ = cmd_sock.recvfrom(2048)
            cmd = verify(data)
            if cmd:
                print(f"\n[SPACECRAFT] authenticated {cmd['action']} from AROS-S "
                      f"(reason: {cmd.get('reason')}). Executing -- returning to safe state.\n")
                recovered = True
            else:
                print("[SPACECRAFT] rejected a forged/unsigned command.")
        except BlockingIOError:
            pass
        except Exception:
            pass

        #once recovered, the payload emits safe nominal telemetry instead of the attack
        payload = safe_packet() if recovered else row.to_dict()
        sock.sendto(json.dumps(payload).encode('utf-8'), server_address)

        print(f"Sent {'SAFE' if recovered else 'pkt'} {i:03} to {server_address}")
        time.sleep(0.5)


if __name__ == "__main__":
    simulate_bus()
