

#  Process Monitoring Script

This **Python** script monitors system processes in real time, logging key process information to both a **CSV** file and a **NDJSON**-formatted log. It also detects and alerts on various anomalies, such as:

- **Ghost Ancestry**: A currently running process whose ancestor has ended.  
- **Too Many Children**: A process exceeding a certain child process threshold.  
- **Deep Process Chains**: Processes with ancestry chains longer than a specified depth.  
- **High Spawn Rate**: A parent process creating too many children within a defined time window.  
- **Unauthorized Elevated Privileges**: Processes running with elevated privileges that are **not** on a predefined whitelist.  
- **Anomalous Priority Changes**: Processes that alter their priority level suspiciously.


#  Features

1. **Real-Time Monitoring**  
   Uses the Python `psutil` library to track processes every few seconds (adjustable via `MONITOR_INTERVAL`).

2. **CSV & NDJSON Logging**  
   - **CSV**: Tabular records stored in `process_monitor_log.csv`.
   - **NDJSON**: Line-delimited JSON records stored in `logs/process_monitor.ndjson`.

3. **Alerts & Anomalies**  
   - Detects unauthorized elevation.
   - Checks for unusual process priority changes.
   - Watches for high spawn rates, too many children, deep process chains, and ghost ancestry.

4. **Cross-Platform**  
   - Works on **Windows**, **Linux**, and **macOS** (with minor differences in how privilege elevation is detected).

5. **Graceful Shutdown**  
   - Captures `SIGINT` (Ctrl+C) and (where available) `SIGTERM` signals to cleanly stop monitoring.

---
#  Requirements

1. **Python 3.6+**  
   The script should be compatible with Python 3.6 and above.

2. **psutil** library  
   - Required to gather process information.  
   - Install with `pip install psutil`.

3. **Optional**: Elevated privileges  
   - On some systems, certain process info (priority/user) may require admin/root privileges to read fully.  
   - The script will handle `AccessDenied` errors gracefully if run as a non-privileged user.

4. **Log Directory**  
   - The script defaults to creating a directory named `logs` to store `process_monitor.ndjson`.  
   - Ensure you have write access to the location where the script is running.

---

##  Installation & Setup

1. **Clone or Download** this repository (containing the Python script and this README).  
2. **Install Dependencies**:
   ```bash
   pip install psutil
   ```
3. **(Optional)** If you plan to run on Windows and want to detect privileges accurately, the script uses `ctypes` calls. Python must be installed in a standard location. Similarly, for macOS/Linux, make sure `psutil` can read process attributes.

---

## Configuration

Several **global settings** (tunable constants) appear near the top of the script:

- `MONITOR_INTERVAL`: The delay (in seconds) between process scans. Defaults to `2.0`.
- `MAX_SPAWN_RATE`: Maximum allowed child processes spawned per minute. Defaults to `10`.
- `MAX_CHILD_PROCESSES`: Threshold for too many children. Defaults to `20`.
- `MAX_TREE_DEPTH`: Deep process chain threshold. Defaults to `10`.
- `CSV_FILENAME`: Name of the CSV file for logging. Defaults to `"process_monitor_log.csv"`.
- `LOG_DIR` and `LOG_FILENAME`: Directory and filename for line-delimited JSON logs (`ndjson`). Defaults to `"logs"` and `"process_monitor.ndjson"`.

Other flags:

- `PRIVILEGE_CHANGE_FLAG`: If set to `True`, logs changes in process user privileges.  
- `PRIORITY_CHANGE_FLAG`: If set to `True`, logs changes in process priority level.  

A **whitelist** dictionary, `WHITELIST`, provides a listing of legitimate elevated processes for Windows, Linux, and macOS. You can add or remove entries depending on your environment.

---

## Running the Script

From a terminal:

```bash
python process_monitor.py
```

Or make it executable (Linux/macOS):

```bash
chmod +x process_monitor.py
./process_monitor.py
```

### Script Output

1. **Console/Terminal**  
   - Logs important messages and alerts in NDJSON format (one JSON record per line).  
   - By default, it shows messages at `INFO` level and above.

2. **CSV File**:  
   - `process_monitor_log.csv` is updated each time a process event occurs (creation or final log upon ending).  
   - Contains columns like PID, name, start/end timestamps, ancestry, user, priority, etc.

3. **NDJSON Log File**:  
   - `logs/process_monitor.ndjson` accumulates line-delimited JSON logs for deeper inspection or machine parsing.  
   - Rotates at 5MB (keeping up to 5 backups).

---

## Stopping the Script

- **Ctrl + C** (SIGINT) or sending a **SIGTERM** (where supported) triggers a graceful shutdown.  
- The script logs the final state of each running process to CSV before exiting.

---
Known Issues / Limitations

- Some process attributes may be unavailable without elevated permissions, resulting in `AccessDenied` or partial data.
- The script’s overhead depends on **`MONITOR_INTERVAL`**; setting it too low might increase CPU usage significantly.
- On **Windows**, `SIGTERM` is not natively supported, but the script catches `SIGINT` (Ctrl+C).  
- The **whitelist** approach to detecting unauthorized elevation is simplistic—any not in the whitelist is flagged. Adjust as needed for your environment.

---





*Happy process monitoring!*


#  Log Parser


This **Python** application provides a **graphical interface** (built with **PyQt5**) to load, filter, and analyze logs in **line-delimited JSON** (e.g., `.ndjson`, `.log`) format. It is particularly useful for logs that follow a JSON schema, containing essential fields such as `timestamp`, `level`, `script`, `module`, `funcName`, `lineNo`, and `message`.

## Features

1. **GUI-Based**  
   - Built with **PyQt5** for an intuitive, desktop-based interface.  
   - Notebook-style layout, where the main tab features filtering controls (timeline sliders, text filters, etc.) and the main log table.

2. **Filtering & Searching**  
   - **Search bar** for quick free-text matches.  
   - **Timeline Slider** to limit logs by timestamp range.  
   - **Quick Filters** for common time intervals (Last Hour, Last 24 Hours, etc.).  
   - **Regex** support for filtering messages (`Message Content (Regex)`).  
   - Filter by `Script Name`, `Module Name`, and `Log Level`.

3. **Continuous Polling**  
   - Watches the currently selected log file for new lines every few seconds (configurable).  
   - Automatically appends newly detected log lines to the table if they match current filters.

4. **Color Scheme**  
   - Dark-themed interface for comfortable viewing (and “cyber-security” aesthetic).  
   - Log level–based row coloring: neutral for INFO/DEBUG, greyish for WARNING, red for ERROR/CRITICAL, etc.

5. **Export**  
   - Easily export currently filtered logs to **CSV** or **JSON**.

---

## Requirements

- **Python 3.6+**  
- **PyQt5**  
  ```bash
  pip install PyQt5
  ```
- **pandas** (for exporting CSV)  
  ```bash
  pip install pandas
  ```
- **Log files** in **line-delimited JSON** format, each line containing the minimum fields: `timestamp`, `level`, `script`, `module`, `funcName`, `lineNo`, and `message`.

---

## Installation

1. **Clone or Download** the repository containing `log_parser_gui.py` (or the code snippet in your environment).
2. **Install required libraries**:
   ```bash
   pip install PyQt5 pandas
   ```
3. **Optional**: Adjust color scheme or fonts in the `set_styles()` method if you want a different look.

---

## Running the Application

1. Open a terminal in the script’s directory.
2. Run:
   ```bash
   python log_parser_gui.py
   ```
   or make it executable and run:
   ```bash
   chmod +x log_parser_gui.py
   ./log_parser_gui.py
   ```
3. The GUI will appear, titled “Interactive Log Parser.”

---

## Usage

1. **Load Log File**  
   - Click **“Load Log File”** and pick your `.ndjson` or `.log` file containing line-delimited JSON entries.  
   - The script reads and parses each line, displaying them in the main table if they meet the required fields.

2. **Filtering**  
   - **Search bar**: Quick free-text search on the `message` field.  
   - **Filter Criteria**:
     - **Quick Filters**: “Last Hour,” “Last 24 Hours,” “Last 7 Days,” etc.  
     - **Timeline Sliders**: Drag handles to refine the start and end timestamp.  
     - **Script Name**, **Module Name**, and **Log Level** combos, plus a **Regex** filter for the `message`.
   - Click **“Apply Filters”** to refresh the table with matching logs or **“Reset Filters”** to return to all logs.

3. **Searching**  
   - Type in the top “Search:” box to filter visible logs by substring. This is separate from the advanced filters in the “Filter Criteria” group box.

4. **Automatic Polling**  
   - The script monitors for new lines in your log file periodically (default every 2 seconds).  
   - New lines are appended and tested against your current filters. If they match, they appear in the table.

5. **Export Filtered Logs**  
   - When satisfied with the visible logs, click **“Export Filtered Logs”** to save them.  
   - Choose **CSV** or **JSON** to store the data for further sharing or analysis.

---

## Known Limitations

- **Line-Delimited JSON**: Each line must parse individually as valid JSON. Malformed lines are skipped with an error.
- **Large Files**: For very large log files, initial loading might take time and use substantial memory.
- **Regex**: The message filter requires valid regular expressions or a warning is displayed.
- **Polling**: If the log file grows extremely quickly, you might need to reduce the polling interval or run the script in a more powerful environment.

---

## Contributing

1. **Fork** this repository and modify the code or styling.  
2. **Submit a pull request** describing your changes.  
3. Add more advanced filtering or new columns as needed.

---

## License

This Log Parser GUI is provided under the **MIT License**—feel free to modify and distribute.

---

*Happy log analysis!*


Below is a sample **README.md** file for the **Intelligent Task Manager** application with **NDJSON** logging. It gives an overview of the application’s purpose, features, installation instructions, and usage details.

---

# Intelligent Task Manager

This **Python** application provides a **GUI-based** (Tkinter) Task Manager that displays system processes, allows you to **kill** unwanted processes, monitors overall resource usage, and offers some basic “settings” toggles. It also logs all important events to both the **console** and a **rotating NDJSON log file** using a **JSON-based logging schema**.

## Key Features

1. **Process Display & Sort**  
   - Shows all running processes in a table (`Tkinter` `Treeview`) with columns for **PID**, **Name**, **Executable Path**, **CPU usage**, **Memory usage**, and more.  
   - Allows **sorting** columns by ascending or descending order.

2. **Termination (Kill) Function**  
   - Input a **PID** and terminate (kill) that process.  
   - Logs success or failure to the **NDJSON** log file.

3. **Resource Monitor**  
   - Displays **CPU**, **Memory**, and **Disk** usage in real time using a **green progress bar** for each metric.  
   - Updates once per second in a background thread.

4. **NDJSON Logging**  
   - Uses a **line-delimited JSON** format for each log entry, containing fields such as `timestamp`, `level`, `script`, `module`, `funcName`, `lineNo`, and `message`.  
   - Logs are stored in **`logs/intelligent_task_manager.ndjson`**, rotated up to 5 backups of 5 MB each.  
   - Also logs to the console at `INFO` level and above.

5. **Dark Teal/Blue Theming**  
   - A consistent dark color palette for frames, labels, buttons, and treeviews.

6. **Settings Tab**  
   - Example toggles (microphone/camera) to demonstrate enabling or disabling a feature, with status alerts and logs.

---

## Requirements

- **Python 3.6+**  
- **psutil** library (for process and resource information):  
  ```bash
  pip install psutil
  ```
- **sigcheck** (Optional, Windows-only for signature checking). If it’s absent, the script logs a warning.

---

## Installation

1. **Clone or Download** this repository containing the script `IntelligentTaskManager.py` (or similarly named).
2. **Install Python Dependencies**:
   ```bash
   pip install psutil
   ```
3. **(Optional)** For Windows signature checks:  
   - **[sigcheck](https://docs.microsoft.com/en-us/sysinternals/downloads/sigcheck)** by Sysinternals.  
   - Place `sigcheck.exe` in your **PATH** so the script can call it. Otherwise, it logs a warning.

---

## Usage

1. **Run the Script**:
   ```bash
   python IntelligentTaskManager.py
   ```
   or make it executable:
   ```bash
   chmod +x IntelligentTaskManager.py
   ./IntelligentTaskManager.py
   ```

2. **GUI Features**:
   - **Task Manager** Tab:  
     - Lists all running processes with CPU & memory usage.  
     - **Refresh** button updates the list.  
     - **PID Entry** + **End Task** button kills that process (if permissions allow).  
   - **Resource Monitor** Tab:  
     - Real-time CPU/Memory/Disk usage bars.  
   - **Settings** Tab:  
     - Example toggles for microphone/camera with simple on/off alerts.

3. **Logging**:
   - Logs events (start, refresh, kills, errors, toggles) to:
     - **Console**: `INFO` level or higher.  
     - **NDJSON** file: `logs/intelligent_task_manager.ndjson` at `DEBUG` level and above.

---

## Log Schema

Each line in `intelligent_task_manager.ndjson` is a **JSON object** with fields like:

```json
{
  "timestamp": "2023-05-09 14:12:36",
  "level": "INFO",
  "script": "__main__",
  "module": "IntelligentTaskManager",
  "funcName": "refresh_tasks",
  "lineNo": "123",
  "message": "Refreshing process list..."
}
```

This makes it easy to parse or ingest with log-management tools.

---

## Known Limitations

- **PID Killing** requires appropriate permissions. On some systems, you must be **root/administrator** to kill certain processes.
- Large resource usage changes or many processes may slow down refresh times.  
- Windows-specific signature checks use **sigcheck**—on Linux/macOS, the script simply logs “N/A.”

---

## Contributing

- **Fork** this repository and create a **Pull Request** if you’d like to add new features or fix issues.
- Enhance the color palette in `set_styles()` or add new columns to the process table if needed.

---



*Enjoy managing tasks with this intuitive, log-enabled tool!*
