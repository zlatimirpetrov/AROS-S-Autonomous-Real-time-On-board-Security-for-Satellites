# Project AROS-S
### Autonomous Real-time On-board Security for Satellites
**Zlatimir Petrov | Cybersecurity Student** *May 25, 2026*

---

## System Overview
I developed AROS-S because the communication lag between a satellite and Earth makes real-time security almost impossible. If an attack happens, the hardware could be fried before a ground station even sees the telemetry. I built this middleware to run locally on the payload's Linux kernel so it can intercept threats as they happen. 

It’s designed to flag anomalies like DoS-related CPU spikes or suspicious power draws and instantiate mitigation protocols immediately. By killing a malicious process or forcing a safe-mode transition on-board, I can protect the satellite's systems without having to wait for a command from the ground.

---

## Technical Stack & Environment
I chose this particular stack to achieve a balance between substantial processing capability and the limited resources found in an embedded satellite environment:

* **Runtime Environment:** Using a `python:3.11-slim` base image to minimize disk footprint and reduce the attack surface.
* **Data Engineering:** Utilized **Pandas** and **NumPy** for vectorized telemetry normalization and high-efficiency sensor frame processing.
* **Detection Logic:** Implemented a **Partitioned Isolation Forest** (scikit-learn) for statistical outliers and a custom **Bottleneck Autoencoder** (5-3-5 topology) for behavioral correlations.
* **Security & Networking:** Using **hashlib** for SHA-256 integrity anchoring and the **socket** library for real-time UDP packet analysis.

---

## Cybersecurity
I recently completed a fast-paced development sprint to implement the essential detection logic while maintaining strong architectural integrity.

* **Logic Implementation:** Successfully scripted and validated the ensemble engine.
* **Integrity Anchoring:** Integrated a SHA-256 check into the entrypoint sequence to verify model hashes and prevent artifact tampering.
* **Environment Isolation:** Utilizing Docker `cgroups` to strictly cap resource consumption.

---

## Detection Logic
The system uses a two-layer approach to handle both sudden spikes and subtle behavioral drifts.

### Layer 1: Partitioned Statistical Isolation
I’m using an Isolation Forest to intercept point-anomalies. I partitioned the telemetry into Electrical and Computational subspaces to prevent cross-channel masking.
$$s(x, \psi) = 2^{-\frac{E(h(x))}{c(\psi)}}$$

### Layer 2: Neural Behavioral Reconstruction
To detect subtle exploits, I engineered a bottleneck Autoencoder restricted to just **38 parameters** due to RAM constraints.

---

## Model Tuning and Calibration
I am currently tuning the model parameters to handle noisy NASA telemetry data caused by orbital temperature fluctuations. This refactoring ensures the system distinguishes between normal sensor noise and actual cyber attacks, preventing accidental safe-mode transitions.

---

## 20-Day Roadmap: System Hardening
- [x] **Core Logic Sprint:** `src/` directory, hybrid ML logic, and Docker isolation.
- [ ] **UDP Bus Integration:** Refactoring ingestion to use a live UDP packet analyzer for NASA SMAP telemetry.
- [ ] **Model Calibration:** Calibrating MSE thresholds against noisy orbital datasets.
- [ ] **Performance Refactoring:** Optimizing inference loops with C++ or Cython.

---

## Development Timeline

| Sprint | Technical Task | Status/Deliverable |
| :--- | :--- | :--- |
| **Days 1-5** | Core Logic Sprint | `src/` directory, hybrid ML logic (Done) |
| **Days 6-10** | Live Bus Integration | UDP sockets for real-time packet parsing |
| **Days 11-15** | Telemetry Visualization | Threshold tuning and dashboard UI |
| **Days 16-20** | Hardware Hardening | C++ performance refactoring & stress testing |