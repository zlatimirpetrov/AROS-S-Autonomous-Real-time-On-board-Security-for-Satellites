# AROS-S — Autonomous Real-time On-board Security for Satellites

Zlatimir Petrov · Cybersecurity Student · 2026

I built AROS-S because defending a satellite from the ground doesn't really work in real time. By the time suspicious telemetry reaches a ground station and someone reacts, the hardware could already be damaged. So instead of watching from Earth, AROS-S runs on the payload itself and screens the live telemetry stream as it comes in, looking for the fingerprints of an attack: DoS-style CPU spikes, abnormal power draw, or slower sensor-spoofing campaigns that build up over time.

The system detects anomalies, explains which feature drove each one, raises alerts, and records everything to a flight log. It can also respond: when an attack persists, AROS-S sends an authenticated command back to the spacecraft to contain it and then verifies recovery — a simulated closed loop you can toggle on or off. I've kept an honest split between what's implemented and what's still ahead in the roadmap below.

## Demo

https://github.com/user-attachments/assets/8d450139-d414-4765-a8ef-a941a61c188d

> AROS-S flagging a simulated attack on satellite telemetry in real time — the three-layer detector (Isolation Forests + per-packet autoencoder + temporal window) trips the moment the stream goes anomalous, on-board, with no round trip to the ground.

## Where things live

- Model registry (Hugging Face): https://huggingface.co/zlatimirpetrov/aros-s-anomaly-detector
- Telemetry storage bucket (Hugging Face): https://huggingface.co/buckets/zlatimirpetrov/aros-s-detector-storage
- PyPI package: https://pypi.org/project/aros-s/
- ML technical paper (Overleaf): https://www.overleaf.com/read/cjmdsczxpmyy#6d4d37

The detector reads its models either from the local `models/` folder or straight from the Hugging Face registry above. Raw ground-station telemetry logs get synced to the storage bucket.

## How the detection works

AROS-S runs three detectors side by side. The first reacts to sudden, obvious spikes. The second learns what a normal packet looks like and catches ones that break the usual relationships between features. The third watches a short window of packets and catches slow drift that never makes any single packet look wrong. Together they cover fast attacks, corrupted packets, and slow, patient campaigns.

### Layer 1 — Isolation Forests, split by subsystem

Rather than throwing all five telemetry features into one model, I split them into two Isolation Forests so a big spike in one subsystem can't mask a small, deliberate change in another:

- Electrical: `V_bus`, `I_total` — catches power-draining malware or a transmitter being driven too hard.
- Computational: `CPU_load`, `RAM_usage`, `MCU_temp` — catches CPU-exhaustion / DoS behaviour.

Each forest gives every packet a score (`-decision_function`); above its threshold, the packet is treated as anomalous.

### Layer 2 — Bottleneck autoencoder

The second layer is a small 5-3-5 autoencoder (five inputs squeezed through a three-neuron bottleneck and back out to five, about 38 parameters total). Trained only on normal telemetry, it gets good at rebuilding normal packets and bad at rebuilding tampered ones. When someone injects altered data, the reconstruction error (MSE) jumps and trips the alert. Keeping it this small is deliberate — it has to fit a payload's tight memory budget.

### Layer 3 — Temporal window autoencoder

The first two layers look at one packet at a time, so a patient attacker who nudges telemetry gradually — a slow memory leak, for example — can stay inside the normal range on every individual packet and slip past both. The third layer closes that gap. It feeds a sliding window of the last 10 packets into a second small autoencoder (50 inputs → 8 → 50) and scores how well it rebuilds the whole window. A gradual trend is a *shape* that normal windows never have, so the window reconstructs badly and the error spikes — even though no single feature ever left its range. In testing, this layer catches the slow memory-leak attack that both Layer 1 and Layer 2 miss completely.

A packet gets flagged if any layer fires.

### Scaling and integrity

All telemetry is normalised with a `RobustScaler` (median / IQR), which shrugs off random sensor jitter better than a standard mean/std scaler. The same fitted scaler is used everywhere — training, validation, and live inference. That consistency matters more than it sounds: a mismatched scaler silently breaks detection, which is a mistake I made and had to chase down.

Before any model loads, AROS-S hashes each file with SHA-256 and checks it against a known-good `GOLDEN_SIGNATURES` table. If a hash doesn't match, it refuses to start, which blocks a swapped-in or tampered model from ever running.

Inference runs through ONNX Runtime (C++ under the hood) so the models stay fast on constrained hardware.

## Responding to attacks

Detection on its own is only half the job — the whole point of running on the payload is to *act* before the ground could. When AROS-S sees an anomaly persist (three packets in a row, not a single blip, so a one-off false positive can't trip it), it issues a response, watches whether the spacecraft recovers, and escalates if it doesn't.

The response is **proportionate to the threat** — it matches the layer that caught it rather than always slamming the platform into safe-mode:

- electrical anomaly (Forest) → isolate the affected power load
- compute corruption (autoencoder) → terminate the offending process
- slow drift (temporal) → safe-mode transition

Commands go back to the spacecraft over an **authenticated channel**: every command is HMAC-SHA256 signed and timestamped, so a spoofed or replayed command — which would itself be a denial-of-service if it forced safe-mode — is rejected. After acting, AROS-S verifies recovery: if telemetry returns to nominal it confirms the fix; if it's still anomalous after a grace window, it escalates to safe-mode.

The responder is a clean kill-switch — run pure detect-and-log, or the full closed loop:

```bash
python -m src.main --mitigation off   # detect and log only
python -m src.main --mitigation on    # full closed-loop response
```

(or set `AROS_MITIGATION` in `.env`; the CLI flag overrides it). When off, the responder is a no-op and nothing else in the pipeline changes. This is a *simulated* closed loop — on a real payload the command would signal the flight software; here it commands the spacecraft simulator, which authenticates it and returns to a safe state.

## Installing

The package is on PyPI:

```bash
pip install aros-s==0.1.4
```

That gives you the library. To actually run the detector with the simulators and your own config, clone the repo:

```bash
git clone https://github.com/zlatimirpetrov/AROS-S-Autonomous-Real-time-On-board-Security-for-Satellites
cd AROS-S
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Getting it running

If the trained models aren't already in `models/`, build them first:

```bash
python src/prepare_data.py        # baseline nominal telemetry + fits the scaler
python src/nasa_smap_raw.py       # sample NASA SMAP data
python src/recalibrate.py         # trains scaler + both forests + per-packet autoencoder on nominal AND NASA data
python src/train_temporal.py      # trains the Layer 3 temporal-window autoencoder (+ derives TEMP_THR)
python src/convert_to_onnx.py     # exports everything (all five models) to ONNX
```

`recalibrate.py` prints suggested thresholds (the 99th percentile of normal scores) for the first three layers when it finishes. Drop those into `ELEC_THR`, `COMP_THR`, and `MSE_THR` in `live_detector.py` — the values I'm currently running are `0.03`, `0.025`, and `0.95`. `train_temporal.py` prints the temporal threshold the same way; drop it into `TEMP_THR` (currently `6.9`). Then refresh the integrity hashes so they match your freshly built ONNX files:

```bash
python -c "import hashlib;[print(n, hashlib.sha256(open(f'models/{f}','rb').read()).hexdigest()[:8]) for n,f in [('scaler','scaler.onnx'),('elec','model_electrical.onnx'),('comp','model_computational.onnx'),('auto','model_autoencoder.onnx'),('temporal','model_temporal.onnx')]]"
```

Paste those five values into `GOLDEN_SIGNATURES` in `live_detector.py` (or just run `python src/refresh_signatures.py`, which recomputes all of them in place).

Now start the monitor in one terminal:

```bash
python -m src.main
```

and feed it telemetry from another:

```bash
python -m src.nasa_sim        # normal NASA-derived stream — should stay "Nominal"
python -m src.satellite_sim   # attack stream — should light up with anomalies
```

Everything the detector sees is printed live and written to `logs/mission_log_<timestamp>.csv`.

## Network configuration (.env)

The detector and the simulators talk over UDP, and they both read the target address from a `.env` file in the project root:

```
AROS_DETECTOR_HOST=127.0.0.1
AROS_DETECTOR_PORT=5005
```

For everything running on your own machine, `127.0.0.1` (localhost) is what you want, and `5005` is the default port. You'll need to set these yourself — find your local address and the port you want to use, and put them here.

It gets a bit different once the detector runs inside a container. If you launch it under Podman (or Docker), `127.0.0.1` on the host won't reach the detector inside the container. Two ways around it:

- Publish the port when you start the container (`podman run -p 5005:5005/udp ...`) and keep `AROS_DETECTOR_HOST=127.0.0.1`. Easiest option.
- Or find the container's own IP and use that. From inside the container `hostname -I`, or from the host:

  ```bash
  podman inspect -f '{{.NetworkSettings.IPAddress}}' <container_name>
  ```

  then set `AROS_DETECTOR_HOST` to that address.

Whichever you pick, the simulators have to point at the same host and port the detector is bound to, or the packets just go nowhere.

## Running hardened (container)

For a deployment-like run, AROS-S ships a Dockerfile and a `run.sh` (plus a `run.ps1` for Windows) that start it under Podman with the security controls a payload process should have. Build once:

```bash
podman build -t aros-s .
```

then run it hardened:

```bash
./run.sh                   # mitigation on (default)
./run.sh --mitigation off  # detect-and-log only
```

On Windows the equivalent is `.\run.ps1` / `.\run.ps1 --mitigation off`.

What the wrapper enforces, and why:

- **Rootless + non-root** — Podman runs without a root daemon, and the process inside drops to an unprivileged user (`USER satellite_user`). Two layers, not one.
- **Read-only root filesystem** (`--read-only`) — the image can't be modified at runtime. The only writable spots are tmpfs mounts for `/tmp` and `/app/logs`, so the flight log still works while everything else stays immutable. This pairs with the SHA-256 integrity gate: the gate *detects* a swapped model, read-only *prevents* the swap in the first place.
- **No capabilities** (`--cap-drop=ALL`, `--security-opt=no-new-privileges`) — the detector only reads files and opens a UDP socket, so it needs zero Linux capabilities and can't escalate privileges.
- **cgroup limits** (`--memory=256m --cpus=0.5 --pids-limit=64`) — caps worst-case resource use. The detector runs comfortably inside this budget (~105 MB, low CPU), and the same caps bound the CPU-exhaustion attack class AROS-S itself detects: even if something got loose inside the container, it can't starve the host.

One networking note: when the container runs the response loop, it has to reach the spacecraft simulator on the host, so `run.sh` sets `AROS_CMD_HOST=host.containers.internal` and publishes the telemetry port with `-p 5005:5005/udp`. Inside a container, `127.0.0.1` means the container itself, not your machine.

## Choosing where models come from

In `live_detector.py`, the loader can pull models from the local folder or from Hugging Face. Loading locally is the line `local_cached_path = repo_path`; swapping it for `hf_hub_download(repo_id=HF_REPO_ID, filename=repo_path)` pulls the published models from the registry instead. Whichever you use, the `GOLDEN_SIGNATURES` have to match those exact files.

One thing worth remembering: thresholds and signatures are tied to a specific trained model. Every time you recalibrate, re-export the ONNX, recompute the hashes, and re-derive the thresholds — otherwise the detector either refuses to boot or scores against the wrong scale.

## Calibration

The models are trained against both my synthetic nominal data and NASA SMAP-derived telemetry, so the normal orbital ranges and noise are learned as expected behaviour rather than mistaken for attacks. I set the thresholds from the 99th percentile of the normal score distribution instead of hand-picking numbers, which keeps false alarms low while leaving plenty of headroom for real attacks (which score far, far above the line). There's more tuning I want to do here against longer datasets, but the current calibration holds up cleanly on both simulators.

## Roadmap

- [x] Three-layer ML pipeline (dual Isolation Forests + per-packet autoencoder + temporal window autoencoder)
- [x] Temporal layer for slow-drift detection (catches gradual attacks the per-packet layers miss)
- [x] Live UDP telemetry ingestion
- [x] NASA SMAP calibration with percentile-based thresholds
- [x] ONNX export and SHA-256 integrity checking
- [x] Autonomous response — proportionate, HMAC-authenticated commands with recovery verification (simulated closed loop, toggleable)
- [x] Container hardening — rootless runtime, read-only filesystem, cgroup limits, dropped capabilities (Dockerfile + run.sh / run.ps1 included)
- [ ] Ongoing recalibration against larger orbital datasets

## License

See [LICENSE](LICENSE).
