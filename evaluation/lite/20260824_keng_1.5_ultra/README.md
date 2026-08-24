# Keng 1.5 Ultra - SWE-bench Lite Evaluation

## Model Overview
- **Model Name**: Keng 1.5 Ultra
- **Architecture**: Deep Reasoning & Agentic Code Architect Engine
- **Platform**: Keng AI Studio
- **Evaluation Benchmark**: SWE-bench Lite (300 Tasks)
- **Submission Date**: 2026-08-24

## System Specifications
- **Inference Engine**: Keng AI Universal Cognitive Engine
- **Hardware Acceleration**: NVIDIA GeForce RTX 3050 (Ampere Tensor Cores, TF32/FP16)
- **CPU**: AMD Ryzen 5 5600H (6 Cores / 12 Threads)
- **Environment**: WSL2 Ubuntu 22.04 / Python 3.10 / Docker Engine

## Evaluation Methodology
The evaluation was executed end-to-end using the official SWE-bench evaluation harness (`swebench.harness.run_evaluation` v5.0.2) with Docker execution environments. For each issue in the dataset, the model produced unified git diff patches that were applied and validated against full regression and unit test suites (`pytest`/`unittest`).

## File Artifacts
- `predictions.json`: Generated git diff patches for all 300 instances of SWE-bench Lite.
- `results.json`: Official test harness execution results and pass rates.
