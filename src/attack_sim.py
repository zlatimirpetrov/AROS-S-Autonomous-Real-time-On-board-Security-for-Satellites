import pandas as pd
import numpy as np
import os

# goal: forcing the ML model (Isolation Forest) to see values outside the 'Normal' IQR.

def create_malicious_telemetry():
    print("AROS-S: Generating attack vectors...")

    #starting with 100 samples of normal behavior 
    np.random.seed(99)
    rows=100
    data={
        'V_bus': np.random.normal(28.0, 0.1, rows),
        'I_total': np.random.normal(1.1, 0.05, rows),
        'CPU_load': np.random.uniform(10, 20, rows),
        'RAM_usage': np.random.uniform(130, 140, rows),
        'MCU_temp': np.random.normal(30.0, 1.0, rows)
    }
    df=pd.DataFrame(data)

    # Unauthorized Hardware Activation- simulating a component turning on that shouldn't
    #result: Voltage drop and current spike.
    df.loc[20:40, 'V_bus']= 22.0  #big drop from 28V
    df.loc[20:40, 'I_total']= 5.5  #huge spike in Amps

    #CPU DoS, malicious code thottle the CPU, CPU load on 100% and Temp rises
    df.loc[70:90, 'CPU_load']= 99.5
    df.loc[70:90, 'MCU_temp']= 80.0    #overheating

    #save to a sep file so to not overwrite the training data
    if not os.path.exists('data'): 
        os.makedirs('data')
    df.to_csv('data/attack_telemetry.csv', index=False)

    print("Status: OK. Malicious data saved to data/attack_telemetry.csv")

if __name__== "__main__":
    create_malicious_telemetry()