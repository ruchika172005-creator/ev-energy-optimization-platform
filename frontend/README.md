# EV-IEMS React Frontend

Modern, high-performance React (Vite) interface for the **AI-Powered Intelligent Energy Management and Range Optimization System for Electric Vehicles**.

## Quick Start Guide

### 1. Start the Flask Backend (Terminal 1)
In the project root directory:
```powershell
python app.py
```
*Backend runs at `http://127.0.0.1:5000` exposing REST endpoints.*

### 2. Install & Start the React Frontend (Terminal 2)
In the `frontend` folder:
```powershell
cd frontend
npm install
npm run dev
```
*React app starts at `http://localhost:3000` (or `http://localhost:5173`) and connects automatically to the Flask backend.*

## Key Features
- **Executive Dashboard:** Fleet KPI metrics & ML architecture breakdown.
- **Trip Energy Predictor:** Real-time inference with GradientBoostingRegressor & driving range estimation.
- **IEMS Closed-Loop Simulator:** Dynamic comparative evaluation of Baseline, Eco-Heuristic, and Intelligent Adaptive strategies.
- **What-If Sensitivity Analysis:** Sweep analysis of ambient temperature, cruising speed, and climate setpoints.
- **Model Benchmarks:** Leaderboard across Gradient Boosting, Random Forest, Ridge, Decision Tree, and KNN.
- **Research Visualizations:** Interactive gallery of 13 high-resolution publication figures with modal inspection.
- **Audit Logs:** Real-time persistence and history clearing.
