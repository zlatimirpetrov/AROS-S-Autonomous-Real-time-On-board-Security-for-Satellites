"""
Numerical equivalence tests: every exported ONNX model must reproduce its
scikit-learn (.joblib) counterpart, layer by layer.
"""

import os
import numpy as np
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(BASE, "models")
DATA = os.path.join(BASE, "data")
F = ["V_bus", "I_total", "CPU_load", "RAM_usage", "MCU_temp"]

joblib = pytest.importorskip("joblib")
ort = pytest.importorskip("onnxruntime")
pd = pytest.importorskip("pandas")

TOL = 1e-3        # scaler / autoencoder (float32 vs float64)
TOL_FOREST = 1e-2  # isolation-forest score export is slightly lossier


def _need(*files):
    for f in files:
        if not os.path.exists(os.path.join(MODELS, f)):
            pytest.skip(f"missing models/{f}; run the build step first")


def _sample(n=20):
    csv = os.path.join(DATA, "raw_telemetry.csv")
    if os.path.exists(csv):
        return pd.read_csv(csv)[F].to_numpy()[:n].astype(np.float32)
    return np.random.default_rng(0).normal(size=(n, 5)).astype(np.float32)


def _onnx(sess, X, idx=0):
    name = sess.get_inputs()[0].name
    return np.asarray(sess.run(None, {name: X.astype(np.float32)})[idx])


def _scaler():
    return joblib.load(os.path.join(MODELS, "scaler.joblib"))


def test_scaler_equivalence():
    _need("scaler.joblib", "scaler.onnx")
    sc = _scaler()
    sess = ort.InferenceSession(os.path.join(MODELS, "scaler.onnx"))
    X = _sample()
    assert np.abs(sc.transform(X) - _onnx(sess, X)).max() < TOL


def test_forest_equivalence():
    _need("scaler.joblib",
          "model_electrical.joblib", "model_electrical.onnx",
          "model_computational.joblib", "model_computational.onnx")
    Z = _scaler().transform(_sample()).astype(np.float32)
    for jb, on, cols in [
        ("model_electrical.joblib", "model_electrical.onnx", [0, 1]),
        ("model_computational.joblib", "model_computational.onnx", [2, 3, 4]),
    ]:
        m = joblib.load(os.path.join(MODELS, jb))
        sess = ort.InferenceSession(os.path.join(MODELS, on))
        Xs = Z[:, cols]
        j = m.decision_function(Xs)
        o = np.asarray(sess.run(None, {sess.get_inputs()[0].name: Xs})[1]).reshape(-1)
        assert np.abs(j - o).max() < TOL_FOREST, f"{on} score mismatch"


def test_autoencoder_equivalence():
    _need("scaler.joblib", "model_autoencoder.joblib", "model_autoencoder.onnx")
    ae = joblib.load(os.path.join(MODELS, "model_autoencoder.joblib"))
    sess = ort.InferenceSession(os.path.join(MODELS, "model_autoencoder.onnx"))
    Z = _scaler().transform(_sample()).astype(np.float32)
    j = ae.predict(Z)
    o = _onnx(sess, Z).reshape(Z.shape)   #ONNX returns (n*5, 1) -> reshape to (n, 5)
    assert np.abs(j - o).max() < TOL


def test_temporal_equivalence():
    _need("scaler.joblib", "model_temporal.joblib", "model_temporal.onnx")
    ae = joblib.load(os.path.join(MODELS, "model_temporal.joblib"))
    sess = ort.InferenceSession(os.path.join(MODELS, "model_temporal.onnx"))
    win = _scaler().transform(_sample(10)).astype(np.float32).reshape(1, -1)  # (1, 50)
    j = ae.predict(win)
    o = _onnx(sess, win).reshape(win.shape)   #ONNX returns (n*50, 1) -> reshape
    assert np.abs(j - o).max() < TOL
