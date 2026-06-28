---
title: 'AROS-S: Lightweight Onboard Anomaly Detection for Satellite Telemetry'
tags:
  - Python
  - anomaly detection
  - satellite telemetry
  - machine learning
  - cybersecurity
  - ONNX
  - CubeSat
  - edge inference
authors:
  - name: Zlatimir Petrov
    orcid: 0009-0008-4428-4937
    affiliation: 1
affiliations:
  - name: Nikola Vaptsarov Naval Academy, Varna, Bulgaria
    index: 1
date: 28 June 2026
bibliography: paper.bib
---

# Summary

`AROS-S` (Autonomous Real-time On-board Security for Satellites) is a lightweight,
one-class anomaly-detection library for spacecraft telemetry, designed to run on
resource-constrained satellite payload computers. It screens each telemetry packet in
real time with a layered detector — two partitioned Isolation Forests, a compact
per-packet autoencoder, and a sliding-window autoencoder — and flags departures from
learned normal behaviour without requiring labelled attack data. Trained models are
exported to ONNX and verified with a cryptographic integrity check before loading, and
an optional authenticated response-and-recovery loop is included. The library is
packaged for reproducible use (PyPI, Docker) and ships with scripts that reproduce its
evaluation on the public NASA SMAP telemetry benchmark.

# Statement of need

Modern satellites increasingly run general-purpose processors, software-defined radios,
and network stacks, which widens their attack surface. Yet ground-based monitoring is
often too slow to react within the communication gaps of an orbit: by the time
abnormal telemetry reaches an operator, a fault or attack may already have caused harm.
Detecting anomalies onboard is therefore valuable, but two obstacles stand in the way.
First, the deep sequence models that perform well on telemetry benchmarks
[@hundman:2018] are too large for a payload computer. Second, no public dataset of real
in-orbit attacks exists, so supervised classification does not fit.

`AROS-S` addresses this gap with a small, one-class detector that learns what normal
spacecraft state looks like and treats deviations as suspicious, operating within a
CubeSat-class resource budget (kilobyte-scale models, sub-millisecond inference, no
GPU). It gives researchers and CubeSat developers an open, reproducible baseline for
onboard telemetry security, and a foundation for further experimentation on real
hardware. The need for such onboard, resource-aware defences is motivated by a growing
body of work on the cybersecurity of space systems [@falco:2019; @pavur:2022;
@manulis:2021].

# Functionality

`AROS-S` provides:

- **A three-layer one-class detector.** Two Isolation Forests [@liu:2008] are trained on
  disjoint feature groups (electrical and computational subsystems) so that a large
  swing in one subsystem cannot mask a small, deliberate change in another; a
  38-parameter autoencoder catches packets that break learned feature relationships; and
  a sliding-window autoencoder catches slow drift no single packet reveals. The four
  scores are combined with an OR rule.
- **One-class training** on normal data only, with robust (median/IQR) scaling, removing
  the need for labelled attacks.
- **ONNX export and serving** [@onnxruntime] of all models for portability to embedded
  targets, built on scikit-learn estimators [@pedregosa:2011].
- **Model integrity verification:** a SHA-256 digest of every model is checked before it
  is loaded, treating the detector itself as an asset to protect.
- **A simulated authenticated response loop** that signs commands (HMAC) and verifies
  recovery, kept explicitly as a simulation rather than flight software.
- **Reproducible packaging** (PyPI, Docker) and evaluation scripts that reproduce
  results on the NASA SMAP benchmark and against classical one-class baselines
  (Isolation Forest, One-Class SVM, Local Outlier Factor).

# State of the field

Spacecraft telemetry anomaly detection has been approached with reconstruction-based
methods such as autoencoders [@sakurada:2014] and with deep recurrent models that set
strong benchmarks on the NASA SMAP and MSL datasets [@hundman:2018]. `AROS-S`
deliberately trades a small amount of accuracy for a much smaller onboard footprint:
on the SMAP benchmark its reconstruction layer matches the strongest classical
one-class baseline at the smallest model size and lowest per-window latency of the
methods compared, making it suitable for deployment on payload-class hardware rather
than on the ground.

# Acknowledgements

The author thanks the mentors and reviewers who provided feedback on the underlying
research.

# References
