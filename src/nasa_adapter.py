import pandas as pd
import numpy as np

def transform_smap_to_aros(nasa_df):
    """
    translates NASA SMAP scientific telemetry into AROS-S system metrics
    """
    aros_data=pd.DataFrame()

    #mapping logic
    #'tb_v_corrected' fluctuations mimic 'V_bus' noise
    aros_data['V_bus']= (nasa_df['tb_v_corrected'] / nasa_df['tb_v_corrected'].mean()) * 28.0
    
    #'tb_h_corrected' fluctuations mimic 'I_total' noise
    aros_data['I_total']= (nasa_df['tb_h_corrected'] / nasa_df['tb_h_corrected'].mean()) * 1.5
    
    #randomly simulate CPU/RAM based on data activity density
    aros_data['CPU_load']= np.random.uniform(15, 45, size=len(nasa_df))
    aros_data['RAM_usage']= np.random.uniform(200, 600, size=len(nasa_df))
    
    #'surface_temp' maps directly to our 'MCU_temp'
    aros_data['MCU_temp'] = nasa_df['surface_temp'] - 273.15
    
    return aros_data