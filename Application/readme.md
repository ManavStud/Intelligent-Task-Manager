#  Intelligent Task Manager

A cross-platform task management and monitoring application built with Flet. This project integrates multiple modules for process monitoring, network monitoring, scheduled process distribution, device management, and logs analytics—all within a single, cohesive UI.

Table of Contents
	•	Features
	•	Prerequisites
	•	Installation
	•	Project Structure
	•	Usage
	•	Configuration
	•	Troubleshooting
	•	Contributing
	•	License

⸻
Features
	1.	Process Monitoring
	•	Real-time CPU, Memory usage, status, and security checks.
	•	Critical alerts for high usage or terminated processes.
	•	A separate logs panel for detailed process logs.
	2.	Network Monitoring
	•	Displays live network connections (IPv4 & IPv6) with usage stats.
	•	Logs panel for network-related events.
	•	Background thread for updates without blocking the UI.
	3.	Scheduled Processes (System Distribution)
	•	Pie or bar charts (via Plotly) showing system vs. non-system tasks.
	•	Periodic updates with minimal overhead on all platforms.
	4.	Process Chains
	•	Visual representation of process ancestry and resource usage.
	•	Automatic updates in a background thread.
	5.	Device Manager
	•	Manage USB, Bluetooth, Camera, Microphone, and Wi-Fi devices.
	•	Simple toggles and status indicators.
	•	Some functionality requires administrator privileges (especially on Windows).
	6.	Logs Analytics
	•	Read and parse JSON-based log files.
	•	Filter logs by date, level, script, module, or message (regex).
	•	Real-time “live logs” reading from a file, with a bar chart of logs/hour.
	•	Color-coded stat cards for total logs, info, warnings, and errors.

⸻

Prerequisites
	1.	Python 3.8+
	2.	Flet 0.28+ (to use PlotlyChart for charts)

pip install flet==0.28.0


	3.	Pandas for DataFrame operations in logs analytics.

pip install pandas


	4.	Plotly for chart generation.

pip install plotly


	5.	Psutil for process, CPU, and memory usage.

pip install psutil


	6.	(Optional) On Windows, some device manager functions (USB, camera) require administrator privileges.

⸻

Installation
	1.	Clone the repository:

git clone https://github.com/YourUsername/Intelligent-Task-Manager.git
cd Intelligent-Task-Manager


	2.	Install the required dependencies:

pip install -r requirements.txt

(Or install the packages individually as listed in Prerequisites.)

	3.	(Optional) If you need to manage devices on Windows, run PowerShell as admin or run the Python script with elevated privileges.

⸻

##  Project Structure

A simplified view of the relevant files:

Intelligent-Task-Manager/
│
├── Applications/
│   ├── integrated.py        # The main entry point (DesktopApp) integrating all tabs
│   ├── proc_mon.py          # Process Monitoring code
│   ├── network_monitor.py   # Network Monitoring code
│   ├── Scheduled_processes.py
│   ├── proc_chain.py        # Process Chains logic
│   ├── device_manager.py    # External device manager UI
│   ├── logs_analytics.py    # Logs analytics script (Log reading, charting, filtering)
│   └── ...
├── assets/
│   ├── Background.png
│   ├── logo.png
│   ├── ...
├── requirements.txt         # Python dependencies
├── README.md                # (This file)
└── ...

##  Key Modules:
	•	integrated.py: Main application, containing DesktopApp class.
	•	logs_analytics.py: Builds the “Logs” tab, uses PlotlyChart for logs/hour chart.
	•	device_manager.py: Device Manager UI for USB, Bluetooth, Wi-Fi, camera, microphone.
	•	proc_mon.py, network_monitor.py, Scheduled_processes.py, proc_chain.py: Other specialized modules integrated into the main app.

⸻

##  Usage
	1.	Run the main integrated app:

python Applications/integrated.py

This launches the Flet app in a new browser window (or in a desktop window if you run with flet.app() in desktop mode).

	2.	Tabs:
	•	Process Monitor: Real-time CPU/memory usage and logs.
	•	Network Connections: IPv4/IPv6 usage, live logs.
	•	Scheduled Processes: Distribution of system vs. non-system tasks.
	•	Process Chains: Hierarchical view of processes.
	•	Device Manager: Control USB, Bluetooth, camera, mic, Wi-Fi.
	•	System Logs: Load a JSON-based log file, see stats, bar chart, and filtered tables.
	3.	Logs:
	•	Click Load File to pick a JSON log file.
	•	Watch the chart update in real-time (top-right).
	•	View logs in either the main logs tab or the live logs tab.

⸻

Configuration
	•	Paths: The application references self.base_path for assets. Update self.base_path in integrated.py if your assets folder is elsewhere.
	•	Colors: You can customize the accent color (self.accent_color), background (self.dark_bg), card color (self.dark_card), etc., in DesktopApp.__init__().
	•	Intervals: Threads typically update every 3–5 seconds. Adjust these intervals in the relevant background loops (e.g., time.sleep(3)).



