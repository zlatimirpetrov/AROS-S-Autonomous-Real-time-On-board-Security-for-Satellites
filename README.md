# AROS-S — Autonomous Real-time On-board Security for Satellites

**Zlatimir Petrov · Cybersecurity Student · 2026**

AROS-S is a lightweight, on-board anomaly-detection middleware for satellite payloads.
Because the round-trip lag between a spacecraft and a ground station makes remote,
real-time defence impractical, AROS-S runs **locally on the payload** and screens live
telemetry for cyber-attack signatures (DoS-driven CPU spikes, abnormal power draw,
slow sensor-spoofing campaigns) as the packets arrive.

> **Status:** detection + alerting + flight-recorder logging are implemented.
> Active mitigation (process termination / safe-mode transition) is on the roadmap —
> see [Roadmap](#roadmap).

---

## Model registry

* **Hugging Face model repo:** https://huggingface.co/zlatimirpetrov/aros-s-anomaly-detector

The detector can run models from the local `models/` directory (default) or be pointed at
the Hugging Face registry. See [Configuration](#configuration).

---

## Detection architecture

AROS-S uses a **two-layer hybrid pipeline** so it catches both sudden point anomalies and
slow, coordinated drift.

### Layer 1 — Partitioned Isolation Forests
Two independent Isolation Forests run on separate feature subspaces, which avoids
"cross-channel masking" (a large compute spike hiding a small electrical siphon):

* **Electrical subspace** — `V_bus`, `I_total` (power-draining malware, transmitter overload)
* **Computational subspace** — `CPU_load`, `RAM_usage`, `MCU_temp` (CPU-exhaustion / DoS)

The per-packet anomaly score used by the detector is `-decision_function(x)`; a score above
its threshold means the forest considers the packet anomalous.

### Layer 2 — Bottleneck Autoencoder
A symmetric **5-3-5** `MLPRegressor` autoencoder (5 inputs → 3-neuron bottleneck → 5 outputs,
**38 parameters**) learns the normal correlations between spacecraft state variables. When an
adversary injects altered packets, reconstruction fails and the **Mean Squared Error spikes**
above the alert threshold.

A packet is flagged if **either** layer trips.

### Preprocessing
All telemetry is normalized with a **`RobustScaler`** (median / IQR) so random sensor jitter
doesn't shift the baseline. The *same* scaler is used in training, validation, and live
inference — this consistency is essential (a scaler mismatch silently breaks detection).

### Integrity layer
At boot, AROS-S computes a **SHA-256 checksum** of every model file and compares it against
hardcoded `GOLDEN_SIGNATURES`. Any mismatch halts execution, blocking model-injection /
tampering before the graphs are loaded.

### Inference engine
Models are exported to **ONNX** and executed via **ONNX Runtime** (C++ backend) for
low-latency inference suitable for a constrained payload.

---

## Repository layout

```
src/
  prepare_data.py      # generate baseline nominal telemetry + fit RobustScaler
  nasa_smap_raw.py     # generate sample NASA SMAP-style raw data
  nasa_adapter.py      # map NASA SMAP fields -> AROS-S 5 features
  train_model.py       # train the two Isolation Forests
  train_autoencoder.py # train the 5-3-5 autoencoder
  recalibrate.py       # retrain everything on nominal + NASA regimes, print thresholds
  convert_to_onnx.py   # export all .joblib models -> .onnx
  live_detector.py     # the on-board detector (UDP/CSV ingest, scoring, logging)
  bus_handler.py       # telemetry bus (UDP socket / CSV replay)
  main.py              # entry point -> start_monitor()
  satellite_sim.py     # stream attack telemetry over UDP (red-team sim)
  nasa_sim.py          # stream NASA-derived telemetry over UDP (nominal sim)
  attack_sim.py        # synthesize labelled attack telemetry
models/                # scaler + 2 forests + autoencoder  (.joblib and .onnx)
data/                  # generated telemetry CSVs
logs/                  # mission_log_*.csv flight recordings
```

---

## How to start

### 1. Install
```bash
git clone <your-repo-url>
cd AROS-S
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Build the data and models
If the `models/` folder is not present in the repo, generate it:
```bash
python src/prepare_data.py        # baseline nominal data + scaler
python src/nasa_smap_raw.py       # sample NASA SMAP data
python src/recalibrate.py         # train scaler + forests + autoencoder on BOTH regimes
python src/convert_to_onnx.py     # export models to ONNX
```
`recalibrate.py` prints suggested detection thresholds (99th percentile of normal scores).

### 3. Set the thresholds and integrity hashes
In `src/live_detector.py`:
* paste the thresholds printed by `recalibrate.py` into `ELEC_THR`, `COMP_THR`, `MSE_THR`
  (current working values: `0.03`, `0.025`, `0.95`)
* refresh `GOLDEN_SIGNATURES` with the hashes of your ONNX files:
```bash
python -c "import hashlib;[print(n, hashlib.sha256(open(f'models/{f}','rb').read()).hexdigest()[:8]) for n,f in [('scaler','scaler.onnx'),('elec','model_electrical.onnx'),('comp','model_computational.onnx'),('auto','model_autoencoder.onnx')]]"
```

### 4. Run the detector
In one terminal, start the on-board monitor (listens on UDP `5005`):
```bash
python -m src.main
```
In a second terminal, stream telemetry to it:
```bash
python -m src.nasa_sim        # nominal NASA-derived stream -> should read "Nominal"
python -m src.satellite_sim   # red-team attack stream      -> should flag anomalies
```
Detections print live and are written to `logs/mission_log_<timestamp>.csv`.

---

## Configuration

| Setting | Location | Notes |
|---|---|---|
| `ELEC_THR`, `COMP_THR`, `MSE_THR` | `live_detector.py` | Re-derive after every recalibration |
| `GOLDEN_SIGNATURES` | `live_detector.py` | Must match the ONNX files actually loaded |
| Model source | `live_detector.py` | `local_cached_path = repo_path` loads local `models/`; swap to `hf_hub_download(...)` to pull from the HF registry |
| UDP host/port | `.env` | `AROS_DETECTOR_HOST`, `AROS_DETECTOR_PORT` (default `127.0.0.1:5005`) |

> **Important:** thresholds and `GOLDEN_SIGNATURES` are tied to a specific trained model.
> Whenever you recalibrate, you must re-export ONNX, recompute hashes, and re-derive thresholds,
> or the detector will either halt on the integrity check or score on the wrong scale.

---

## Calibration

The models are recalibrated against both the synthetic nominal regime and **NASA SMAP-derived
telemetry**, so normal orbital noise and the NASA operating ranges are learned as nominal.
Detection thresholds are set from the **99th percentile of the normal score distribution**
rather than hand-tuned, which keeps the false-alarm rate low while preserving attack
sensitivity (injected attacks score far above the threshold).

---

## Roadmap

- [x] Core hybrid ML pipeline (`src/`, dual Isolation Forests + autoencoder)
- [x] Live UDP telemetry ingestion
- [x] NASA SMAP calibration + percentile-based thresholds
- [x] ONNX export + SHA-256 integrity layer
- [ ] Active mitigation (process termination / safe-mode transition)
- [ ] Container hardening (rootless runtime, read-only FS, cgroup limits) — `Dockerfile` provided
- [ ] Continuous re-calibration against extended orbital datasets

---

## License

See [LICENSE](LICENSE).
