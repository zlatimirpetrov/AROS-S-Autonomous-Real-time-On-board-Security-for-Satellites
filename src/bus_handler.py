import socket
import json
import pandas as pd

class TelemetryBus:
    def __init__(self, mode='UDP', source='data/attack_telemetry.csv', port=5005):
        self.mode = mode
        self.source = source
        self.port = port
        #hardened:feature order to match the training data
        self.features = ['V_bus', 'I_total', 'CPU_load', 'RAM_usage', 'MCU_temp']

    def stream(self):
        if self.mode=="CSV":
            df=pd.read_csv(self.source)
            for _, row in df.iterrows():
                yield pd.DataFrame([row])

        elif self.mode=='UDP':
            sock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', self.port))
            while True:
                try:
                    data, _ = sock.recvfrom(4096)
                    packet_dict = json.loads(data.decode('utf-8'))
                    yield pd.DataFrame([packet_dict])[self.features]
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"AROS-S [Bus Error]: dropping malformed packet: {e}")
                    continue