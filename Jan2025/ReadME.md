

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
