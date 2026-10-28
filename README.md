# AI-Powered Auxiliary Energy Harvesting & Intelligent Power Allocation System for Electric Vehicles

An advanced automotive energy management system designed to harvest auxiliary electrical energy (via regenerative braking, rooftop solar photovoltaics, and experimental suspension vibration harvesters), dynamically convert and allocate that power across prioritized low-voltage vehicle loads, and measurably reduce energy drawn from the main high-voltage traction battery.

---

## 1. Executive Summary & Purpose

In modern electric vehicles (EVs), auxiliary low-voltage loads (sensors, ECUs, telematics, coolant circulation pumps, displays, and infotainment) consume significant continuous electrical power (typically 300 W – 800 W). Historically, this power is supplied entirely by stepping down energy from the main high-voltage traction pack through a central DC-DC converter, shortening vehicle driving range and increasing battery cyclic throughput.

**This system solves this challenge by:**
1. **Monitoring and Estimating Available Auxiliary Energy**: Capturing kinetic energy from deceleration events, solar irradiance from rooftop PV panels, and micro-kinetic vibration energy.
2. **Intelligent Power Allocation**: Dynamically matching usable harvested power to categorized electrical loads ranked by critical priority (Safety & Control first, followed by Telematics, Thermal, Cockpit, and Amenities).
3. **Main Battery Conservation**: Spared energy directly reduces high-voltage pack depletion, preserving State-of-Charge (SoC), extending driving range, and decreasing cyclic ampere-hour (Ah) degradation.
4. **Machine Learning Baseline Forecasting**: Retaining a trained **Gradient Boosting Regressor** pipeline ($R^2 \approx 0.871$) on a real fleet dataset of 10,151 trips to predict baseline traction consumption and calculate equivalent range parity.

---

## 2. System Architecture

```mermaid
graph TD
    subgraph Auxiliary Energy Harvesting
        A1[Regenerative Braking Recovery] -->|Kinematic Model / Input| DC[DC-DC Buck Converter Stage]
        A2[Rooftop Solar PV Generation] -->|MPPT Solar Model| DC
        A3[Vibration Harvester (Optional)] -->|ISO-8608 Research Estimate| DC
    end

    DC -->|Usable Aux Power P_usable = P_gen * η_conv| AL[Intelligent Power Allocation Engine]
    DC -->|Thermal Loss P_loss = P_gen - P_usable| LOSS[Conversion Losses]

    subgraph Prioritized Electrical Loads
        AL -->|Priority 1| L1[Sensors & Drive ECU (85W)]
        AL -->|Priority 2| L2[Telematics & V2X Comms (25W)]
        AL -->|Priority 3| L3[Battery Coolant Pump (65W)]
        AL -->|Priority 4| L4[Displays & Infotainment (110W)]
        AL -->|Priority 5| L5[Cabin Amenities & USB-C (35W)]
    end

    BAT[Main HV Traction Battery] -.->|Uninterruptible Fallback for Shortfall| L1 & L2 & L3 & L4 & L5
    AL -->|Energy Avoided Wh| IMP[Battery Impact & Range Conserved]
```

---

## 3. Mathematical Models & Energy Conservation Laws

### A. Regenerative Braking Kinetic Energy Recovery
$$P_{\text{kinetic}} = m \cdot v \cdot a$$
$$P_{\text{regen}} = P_{\text{kinetic}} \cdot \eta_{\text{motor}} \cdot \eta_{\text{inverter}} \cdot k_{\text{tap}}$$
Where:
- $m$: Vehicle mass (kg)
- $v$: Vehicle velocity ($m/s$)
- $a$: Deceleration rate ($m/s^2$)
- $\eta_{\text{motor}} \cdot \eta_{\text{inverter}}$: Electro-mechanical conversion efficiency ($\approx 82.7\%$)
- $k_{\text{tap}}$: Auxiliary low-voltage bus coupling limit.

### B. Solar Photovoltaic Generation
$$P_{\text{solar}} = A \cdot G \cdot \eta_{\text{cell}} \cdot \eta_{\text{mppt}} \cdot [1 + \gamma (T_{\text{cell}} - 25)] \cdot (1 - \sigma_{\text{shading}})$$
Where:
- $A$: Active rooftop panel area ($\approx 1.85\text{ m}^2$)
- $G$: Solar irradiance ($\text{W/m}^2$, e.g., 750 $\text{W/m}^2$)
- $\eta_{\text{cell}}$: Monocrystalline cell efficiency ($\approx 21.0\%$)
- $\eta_{\text{mppt}}$: Maximum Power Point Tracking efficiency ($\approx 96.0\%$)
- $\gamma$: Thermal derating coefficient ($-0.38\% / ^\circ\text{C}$).

### C. Suspension Vibration Energy Harvesting (Experimental Model)
$$P_{\text{vibe}} = \sum_{wheels} \frac{1}{2} \cdot c_{\text{damper}} \cdot v_{\text{stroke}}^2 \cdot \eta_{\text{transducer}}$$
*Clearly labelled as an experimental research estimate based on ISO-8608 road roughness classification.*

### D. Energy Allocation Conservation Laws
$$\text{Total Harvested Power: } P_{\text{gen}} = P_{\text{regen}} + P_{\text{solar}} + P_{\text{vibe}}$$
$$\text{Usable Auxiliary Power: } P_{\text{usable}} = P_{\text{gen}} \cdot \eta_{\text{dc\_dc}}$$
$$\text{Conversion Thermal Loss: } P_{\text{loss}} = P_{\text{gen}} - P_{\text{usable}}$$
$$\text{Total Electrical Demand: } P_{\text{demand}} = \sum_{i} P_{\text{load}, i}$$
$$\text{Power Balance: } P_{\text{demand}} = P_{\text{allocated\_aux}} + P_{\text{main\_battery}} + P_{\text{unmet}}$$
$$\text{Battery Energy Avoided (Wh): } E_{\text{avoided}} = P_{\text{allocated\_aux}} \cdot \Delta t$$
$$\text{Auxiliary Utilization (\%): } \text{Utilization} = \frac{P_{\text{allocated\_aux}}}{P_{\text{usable}}} \times 100\% \quad (P_{\text{usable}} > 0)$$

### E. Battery Parity Metrics
$$\text{Equivalent Range Conserved (km)} = \frac{E_{\text{avoided}} \text{ (kWh)}}{\text{Fleet Baseline Rate } (0.2215\text{ kWh/km})}$$
$$\text{Ampere-Hour Throughput Avoided (Ah)} = \frac{E_{\text{avoided}} \text{ (Wh)}}{V_{\text{nominal}} \text{ (360 V)}}$$

---

## 4. Prioritized Electrical Loads

| Priority | Load Subsystem | Default Power | Voltage | Critical | Function |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | Sensors & Drive Dynamics Monitoring | 40 W | 12V | Yes | LiDAR, Radar, IMU, wheel speed sensors, BMS |
| **1** | Low-Power Control Electronics (ECU) | 45 W | 12V | Yes | Primary vehicle control unit, CAN/Ethernet gateway |
| **2** | Telematics & Emergency V2X Comms | 25 W | 12V | No | TCU, eCall, GPS positioning, 5G diagnostics |
| **3** | Battery Coolant Circulation Pump | 65 W | 12V | No | Low-voltage auxiliary thermal equalization pump |
| **4** | Digital Instrument Cluster & HUD | 50 W | 12V | No | High-brightness driver display module |
| **4** | Center Infotainment & Cockpit CPU | 60 W | 12V | No | Cockpit computing, navigation, audio amp |
| **5** | Auxiliary Cabin Amenities & USB-C | 35 W | 12V | No | Passenger device charging and ambient lighting |

---

## 5. REST API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health, model integrity, and readiness |
| `GET` | `/api/energy/sources` | Telemetry & parameters for all auxiliary sources |
| `POST` | `/api/energy/sources` | Update source parameters or manual demonstration power |
| `GET` | `/api/energy/loads` | Retrieve all configured auxiliary electrical loads |
| `POST` | `/api/energy/loads` | Add, update, or toggle an electrical load |
| `DELETE`| `/api/energy/loads/<id>`| Remove a custom electrical load definition |
| `POST` | `/api/energy/allocate` | Execute the priority-ranked power allocation engine |
| `GET` | `/api/energy/summary` | Real-time aggregate power, demand, and last allocation |
| `GET` | `/api/battery/impact` | Direct battery energy avoided, range parity, and Ah throughput |
| `POST` | `/api/predict` | Supervised ML prediction of baseline traction energy (GBR) |
| `GET` | `/api/models/metrics` | Model diagnostic benchmarks ($R^2$, RMSE, MAE) |
| `GET` | `/api/analysis/summary`| Statistical summary of 10,151 vehicle trips |
| `GET` | `/api/analysis/visualizations` | Catalog of 13 verified publication research plots |
| `GET` | `/api/history` | Chronological audit logs for allocations and predictions |
| `DELETE`| `/api/history` | Clear stored audit history |
| `GET` | `/api/settings` | Retrieve system settings (efficiency, bus voltage, mode) |
| `POST` | `/api/settings` | Save updated system settings to SQLite database |

---

## 6. How to Run Locally

### Terminal 1: Start Flask Backend
```powershell
# From project root
python app.py
```
*Backend runs at `http://127.0.0.1:5000` with SQLite persistence (`ev_auxiliary_energy.db`).*

### Terminal 2: Start React Frontend
```powershell
cd frontend
npm install
npm run dev
```
*React frontend runs at `http://localhost:3000`.*

---

## 7. Verification & Testing

Run the automated test suite verifying energy conservation and all 10 API endpoints:
```powershell
python test_all_endpoints.py
```

Test production build of React application:
```powershell
cd frontend
npm run build
```

---

## 8. Engineering Assumptions & Limitations

1. **Software Prototype:** This application is a validated engineering software prototype. Physical hardware deployment requires microcontrollers (e.g. CAN bus, STM32, TI TMS320) and bidirectional DC-DC converters.
2. **Measurement Labelling:** If physical transducers are not connected, the interface clearly labels sources as `demonstration_mode`, `verified_model`, or `experimental_estimate`.
3. **Battery Degradation:** Reduced cyclic throughput is presented as a potential operational benefit; long-term cell lifespan extension claims require physical accelerated cycling tests (Maccor/Arbin).
4. **Energy Parity:** Equivalent range conserved is calculated strictly from empirical fleet traction consumption ($0.2215\text{ kWh/km}$) and accounts for all DC-DC conversion losses.
