# Intelligent Task Manager

A cross-platform task management and monitoring application built with [Flet](https://flet.dev). This project integrates multiple modules for process monitoring, network monitoring, scheduled process distribution, device management, and logs analytics—all within a single, cohesive UI.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

1. **Process Monitoring**  
   - Real-time CPU and Memory usage, status, and security checks.  
   - Critical alerts for high usage or terminated processes.  
   - Dedicated logs panel for detailed process logs.

2. **Network Monitoring**  
   - Displays live network connections (IPv4 & IPv6) with usage stats.  
   - Background thread updates without blocking the UI.  
   - Separate logs panel for network events.

3. **Scheduled Processes (System Distribution)**  
   - Pie or bar charts (via Plotly) showing system vs. non-system tasks.  
   - Periodic updates with minimal overhead across platforms.

4. **Process Chains**  
   - Hierarchical (tree) view of processes and their ancestry.  
   - Automatic resource usage updates in a background thread.

5. **Device Manager**  
   - Manage USB, Bluetooth, Camera, Microphone, and Wi-Fi devices.  
   - Some actions require administrator privileges on Windows.

6. **Logs Analytics**  
   - Read and parse JSON-based logs.  
   - Filter logs by date, level, script, module, or message (regex).  
   - Live logs feature for tailing a log file in real-time.  
   - Bar chart of logs per hour (PlotlyChart).  
   - Color-coded stat cards for total logs, info, warnings, errors.

---

## Prerequisites

1. **Python 3.8+**  
2. **Flet 0.28+**  
   ```bash
   pip install flet==0.28.0

	3.	pandas for DataFrame operations (logs analytics).

pip install pandas


	4.	Plotly for chart generation.

pip install plotly


	5.	psutil for process, CPU, and memory usage.

pip install psutil


	6.	(Optional) Elevated privileges on Windows for certain device manager functions.

⸻

Installation
	1.	Clone the repository:

git clone https://github.com/YourUsername/Intelligent-Task-Manager.git
cd Intelligent-Task-Manager


	2.	Install dependencies:

pip install -r requirements.txt

or install them individually as per Prerequisites.

	3.	(Optional) For device manager features on Windows, run the script with administrator privileges.

⸻

Project Structure

## A simplified view of key files:
    Intelligent-Task-Manager/
    │
    ├── Applications/
    │   ├── integrated.py           # Main entry point (DesktopApp) that integrates all modules
    │   ├── proc_mon.py             # Process Monitoring code
    │   ├── network_monitor.py      # Network Monitoring code
    │   ├── Scheduled_processes.py  # Scheduled process distribution code
    │   ├── proc_chain.py           # Process chaining/ancestry logic
    │   ├── device_manager.py       # Device Manager UI
    │   ├── logs_analytics.py       # Logs analytics script (Log reading, charting, filtering)
    │   └── ...
    ├── assets/
    │   ├── Background.png
    │   ├── logo.png
    │   └── ...
    ├── requirements.txt
    ├── README.md                   # This file
    └── ...

Key Modules:
	•	integrated.py: Main application, containing DesktopApp class with all tabs integrated.
	•	logs_analytics.py: Builds the “Logs” tab using PlotlyChart for logs/hour chart.
	•	device_manager.py: UI for controlling USB, Bluetooth, Wi-Fi, camera, microphone.
	•	proc_mon.py, network_monitor.py, Scheduled_processes.py, proc_chain.py: Specialized modules integrated into the main app.

⸻

Usage
	1.	Run the main integrated app:

python Applications/integrated.py

This launches the Flet app in a new browser window or in a desktop window (depending on your environment).

	2.	Tabs:
	•	Process Monitor: CPU/memory usage, status, alerts, process logs.
	•	Network Connections: IPv4/IPv6 usage, live logs, background updates.
	•	Scheduled Processes: Real-time distribution of system vs. non-system tasks.
	•	Process Chains: Tree-based process ancestry and resource usage.
	•	Device Manager: Control USB, Bluetooth, camera, microphone, Wi-Fi.
	•	System Logs: Load a JSON-based log file, see stats & charts, live logs feature.
	3.	Logs:
	•	Use Load File to pick a JSON log file.
	•	A bar chart of logs per hour appears in the top-right.
	•	Filter logs by time, level, script, module, or regex.
	•	Watch live logs update in real-time (bottom “Live Logs” tab).

⸻

Configuration
	•	Paths: Update self.base_path in integrated.py if your assets folder is in a different location.
	•	Colors: Modify self.dark_bg, self.dark_card, self.accent_color, etc., in DesktopApp.__init__() to customize the theme.
	•	Intervals: Adjust background thread sleep intervals (e.g., time.sleep(3)) in the relevant modules if you want faster or slower updates.

⸻

Troubleshooting
	1.	No chart: Ensure you have Flet 0.28+ and Plotly installed.
	2.	Permission issues on Windows for device manager tasks: Try running as admin.
	3.	Process or network metrics missing: Some calls require elevated privileges or may be blocked by antivirus.
	4.	Logs not loading: Confirm your JSON lines have the required keys (timestamp, level, etc.).

⸻

Contributing
	1.	Fork the repository.
	2.	Create a new branch (e.g., feature/new-function).
	3.	Commit changes with a clear message.
	4.	Push to your fork.
	5.	Open a Pull Request describing your changes.

⸻

License

This project is licensed under the MIT License. See the LICENSE file for details.

