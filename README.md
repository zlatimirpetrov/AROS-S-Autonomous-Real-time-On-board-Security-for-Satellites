# Project AROS-S
### Autonomous Real-time On-board Security for Satellites
**Zlatimir Petrov | Cybersecurity Student** *June 2026*

---

## Cloud Resources & Repositories
* **Model Registry (Hugging Face):** https://huggingface.co/zlatimirpetrov/aros-s-anomaly-detector
* **Telemetry Storage Bucket (Hugging Face):** https://huggingface.co/buckets/zlatimirpetrov/aros-s-detector-storage

---

## System Overview
I developed AROS-S because the communication lag between a satellite and Earth makes real-time security almost impossible. If an attack happens, the hardware could be fried before a ground station even sees the telemetry. I built this middleware to run locally on the payload's Linux kernel so it can intercept threats as they happen. 

It’s designed to flag anomalies like DoS-related CPU spikes or suspicious power draws and instantiate mitigation protocols immediately. By killing a malicious process or forcing a safe-mode transition on-board, I can protect the satellite's systems without having to wait for a command from the ground.

---

## Technical Stack & Environment
I chose this particular stack to achieve a balance between substantial processing capability and the limited resources found in an embedded satellite environment:

* **Runtime Environment:** Transitioned to a `python:3.11-slim` base image running inside a hardened, rootless **Podman** container architecture to eliminate rootless privilege vulnerabilities and minimize attack surfaces.
* **Data Engineering:** Utilized **Pandas** and **NumPy** for vectorized telemetry normalization, utilizing an integrated `RobustScaler` preprocessing pipeline for noisy sensor frames.
* **Inference Engine:** Migrated the detection engine from heavy, high-overhead Python frameworks to **ONNX Runtime**, compiling raw computational graphs into serial format for ultra-low latency execution via a C++ backend.
* **Cloud Infrastructure:** Integrated **Hugging Face Hub** APIs for remote asset orchestration—maintaining separate pipelines for optimized model binaries and S3-style cloud object buckets for raw ground-station telemetry logging.
* **Security & Networking:** Utilized **hashlib** for localized SHA-256 cryptographic handshakes and the **socket** library for real-time UDP telecommand frame parsing.

---

## Cybersecurity
I recently completed a fast-paced development sprint to implement the essential detection logic while maintaining strong architectural integrity.

* **Logic Implementation:** Successfully engineered and integrated the multi-layer neural and statistical ensemble pipeline.
* **Integrity Anchoring:** Hardcoded a strict cryptographic verification layer within the edge-boot sequence. The system calculates SHA-256 check-sums for all downloaded network assets, blocking model-injection attacks before bytecode initialization.
* **Environment Isolation:** Implemented non-root container isolation policies, restricting OS-level namespace mapping and hard-capping hardware compute boundaries.

---

## Detection Logic
The system uses a two-layer approach to handle both sudden spikes and subtle behavioral drifts.

### Layer 1: Partitioned Statistical Isolation
I’m using an Isolation Forest to intercept point-anomalies. I partitioned the telemetry into Electrical and Computational subspaces to prevent cross-channel masking.
$$s(x, \psi) = 2^{-rac{E(h(x))}{c(\psi)}}$$

### Layer 2: Neural Behavioral Reconstruction
To detect subtle exploits, I engineered a bottleneck Autoencoder restricted to just **38 parameters** due to RAM constraints. It maps spatial relationships across all telemetry parameters concurrently. If the reconstruction Mean Squared Error (MSE) breaches the strict calibrated threshold, a behavioral alert is flagged.

---

## Model Tuning and Calibration
The model parameters and isolation forest boundaries have been completely recalibrated against authentic, noisy NASA SMAP telemetry data. By tuning thresholds to accommodate orbital temperature variations and sensor jitter, the framework maintains zero-false-alarm tolerances—ensuring normal spacecraft operating conditions are never misclassified as a cyber attack, preventing accidental, mission-ending safe-mode triggers.

---

## 20-Day Roadmap: System Hardening
- [x] **Core Logic Sprint:** `src/` directory, hybrid ML logic, and Docker isolation.
- [x] **UDP Bus Integration:** Refactoring ingestion to use a live UDP packet analyzer for NASA SMAP telemetry.
- [x] **Model Calibration:** Calibrating MSE thresholds against noisy orbital datasets.
- [x] **Performance Refactoring:** Optimizing inference loops with C++ execution graphs via serial ONNX runtimes.

---

## Development Timeline

| Sprint | Technical Task | Status/Deliverable |
| :--- | :--- | :--- |
| **Days 1-5** | Core Logic Sprint | `src/` directory, hybrid ML logic, non-root Podman implementation **(Done)** |
| **Days 6-10** | Live Bus Integration | Hardened UDP sockets for live telemetry ingestion & modular framework processing **(Done)** |
| **Days 11-15** | Telemetry Calibration | S3 cloud storage bucket synchronization, RobustScaler tuning, and NASA dataset calibration **(Done)** |
| **Days 16-20** | Hardware Hardening | Serial C++ ONNX graph migration and cryptographic `GOLDEN_SIGNATURES` validation layer **(Done)** |