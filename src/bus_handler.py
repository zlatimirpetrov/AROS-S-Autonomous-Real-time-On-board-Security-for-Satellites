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

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)
            #the port can be reused immediately on restart
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock.bind(('0.0.0.0', self.port))

            while True:
                data, addr = sock.recvfrom(4096)

                try: 
                    packet_dict = json.loads(data.decode('utf-8'))
                    df = pd.DataFrame([packet_dict])

                    #ensure we only yield the columns the model expects
                    yield df[self.features]
                except Exception as e:
                    print(f"AROS-S [Bus Error]: dropping malformed packet: {e}")
                    continue