import joblib
import os
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

def convert_models():
    print("AROS-S: Initializing ONNX conversion pipeline...")

    #load the existing joblib binaries
    scaler = joblib.load('models/scaler.joblib')
    m_elec = joblib.load('models/model_electrical.joblib')
    m_comp = joblib.load('models/model_computational.joblib')
    m_auto = joblib.load('models/model_autoencoder.joblib')

    #define the exact input math shapes
    type_5_features = [('float_input', FloatTensorType([None, 5]))] #scaler and autoencoder
    type_2_features = [('float_input', FloatTensorType([None, 2]))] #elec Forest
    type_3_features = [('float_input', FloatTensorType([None, 3]))] #comp Forest

    #define standard fallback opsets for compatibility
    custom_opset = {'': 15, 'ai.onnx.ml': 3}

    #convert the models to ONNX graphs with target opsets specified
    print("Translating logic gates to C++ optimized ONNX graphs...")
    onnx_scaler = convert_sklearn(scaler, initial_types=type_5_features, target_opset=custom_opset)
    onnx_elec = convert_sklearn(m_elec, initial_types=type_2_features, target_opset=custom_opset)
    onnx_comp = convert_sklearn(m_comp, initial_types=type_3_features, target_opset=custom_opset)
    onnx_auto = convert_sklearn(m_auto, initial_types=type_5_features, target_opset=custom_opset)

    m_temp = joblib.load('models/model_temporal.joblib')
    type_temporal = [('float_input', FloatTensorType([None, 50]))]   # W*5 = 10*5
    onnx_temp = convert_sklearn(m_temp, initial_types=type_temporal, target_opset=custom_opset)
    with open("models/model_temporal.onnx", "wb") as f:
        f.write(onnx_temp.SerializeToString())

    #save the new .onnx files
    print("Exporting ONNX binaries to models/ directory...")
    with open("models/scaler.onnx", "wb") as f:
        f.write(onnx_scaler.SerializeToString())
        
    with open("models/model_electrical.onnx", "wb") as f:
        f.write(onnx_elec.SerializeToString())
        
    with open("models/model_computational.onnx", "wb") as f:
        f.write(onnx_comp.SerializeToString())
        
    with open("models/model_autoencoder.onnx", "wb") as f:
        f.write(onnx_auto.SerializeToString())

    print("Success! All models converted to ONNX format.")

if __name__ == "__main__":
    convert_models()