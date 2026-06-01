import pandas as pd
import numpy as np

rows = 500
data = {
    'tb_v_corrected': np.random.normal(250, 5, rows) + np.sin(np.linspace(0, 10, rows)) * 10,
    'tb_h_corrected': np.random.normal(200, 8, rows) + np.cos(np.linspace(0, 10, rows)) * 5,
    'surface_temp': np.random.normal(285, 2, rows), #Kelvin
    'quality_flag': np.zeros(rows) #0 = good data
}

df = pd.DataFrame(data)
df.to_csv('data/nasa_smap_raw.csv', index=False)
print("NASA SMAP Sample generated: data/nasa_smap_raw.csv")