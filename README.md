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

## Containerization & Environment Hardening
Operating in an embedded space payload requires strict operational isolation. Standard container runtimes present a massive risk if a malicious process achieves root escalation. To counter this, AROS-S enforces an enterprise-grade sandboxing environment:

* **Rootless Podman Architecture:** Built on top of a `python:3.11-slim` base image, the entire stack runs entirely in user-space without root privileges. If an adversary compromises the detector runtime, they remain trapped inside an unprivileged user namespace, completely unable to break out to the host flight computer kernel.
* **Linux Namespace Isolation & CGroups:** We restrict access using precise kernel boundaries—isolating network (`net`), process IDs (`pid`), and mount points (`mnt`). Linux Control Groups (`cgroups v2`) are locked down to strictly cap RAM and CPU ceilings, preventing any algorithmic resource exhaustion (DoS) from starving critical flight control systems.
* **Read-Only Root Filesystem:** The container runtime mounts the application source directory as read-only. Temporary logs and execution frames are isolated to a transient `tmpfs` RAM disk, neutralizing persistent file-injection attacks at the container boundary.

---

## Technical Stack & Engine Framework
I chose this particular stack to achieve a balance between substantial processing capability and the limited resources found in an embedded satellite environment:

* **Data Engineering:** Utilized **Pandas** and **NumPy** for vectorized telemetry normalization, utilizing an integrated `RobustScaler` preprocessing pipeline for noisy sensor frames.
* **Inference Engine:** Migrated the detection engine from heavy, high-overhead Python frameworks to **ONNX Runtime**, compiling raw computational graphs into serial format for ultra-low latency execution via a C++ backend.
* **Cloud Infrastructure:** Integrated **Hugging Face Hub** APIs for remote asset orchestration—maintaining separate pipelines for optimized model binaries and S3-style cloud object buckets for raw ground-station telemetry logging.
* **Security & Networking:** Utilized **hashlib** for localized SHA-256 cryptographic handshakes and the **socket** library for real-time UDP telecommand frame parsing.

---

## Cybersecurity & Integrity Anchoring
I recently completed a fast-paced development sprint to implement the essential detection logic while maintaining strong architectural integrity.

* **Logic Implementation:** Successfully engineered and integrated the multi-layer neural and statistical ensemble pipeline.
* **Integrity Anchoring:** Hardcoded a strict cryptographic verification layer within the edge-boot sequence. The system calculates SHA-256 check-sums for all downloaded network assets, blocking model-injection attacks before bytecode initialization.
* **Environment Isolation:** Implemented non-root container isolation policies, restricting OS-level namespace mapping and hard-capping hardware compute boundaries.

---

## Detection Logic & Machine Learning Architecture
The system uses a two-layer hybrid machine learning pipeline running in tandem to track sudden structural shifts and subtle, slow-moving behavioral drifts simultaneously.

### Layer 1: Partitioned Statistical Isolation (Isolation Forest)
I am using a multi-instance **Isolation Forest** (iForest) to instantly trap point anomalies like malicious command execution or single-packet spikes. 
Instead of processing all telemetry under a single high-dimensional model, the parameters are completely isolated into independent mathematical subspaces:
* **Electrical Subspace:** Monitors voltage vectors and total current consumption (`V_bus`, `I_total`) to isolate power-draining malware or transmitter overloads.
* **Computational Subspace:** Tracks system load variables (`CPU_load`, `RAM_usage`, `MCU_temp`) to immediately identify CPU exhaustion attacks.

By partitioning features, we eliminate "cross-channel masking"—a vulnerability where massive computational spikes trick a model into missing minor but devastating electrical siphoning. The isolation path-length math maps directly to an anomaly score:
$$s(x, \psi) = 2^{-\frac{E(h(x))}{c(\psi)}}$$

### Layer 2: Neural Behavioral Reconstruction (Bottleneck Autoencoder)
To track complex, highly coordinated cyber campaigns (like advanced persistent threats tricking sensor inputs over time), AROS-S routes data into a custom **Deep Bottleneck Autoencoder**.
* **The Topology:** Designed with a symmetric **5-3-5 layer topology** (5 inputs $\rightarrow$ 3 bottleneck features $\rightarrow$ 5 reconstructed outputs).
* **Embedded Optimization:** The model structure is aggressively optimized to compress features down to just **38 parameters** to conform to the payload’s strict static RAM limitations.
* **Mathematical Enforcement:** The network forces data through an ultra-tight bottleneck, forcing it to learn the core physical correlations of nominal spacecraft state vectors. When an adversary injects synthetic or altered packets, the network fails to reconstruct the corrupted signatures accurately. This structural failure causes the Mean Squared Error (MSE) to spike, immediately tripping the alert threshold.

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