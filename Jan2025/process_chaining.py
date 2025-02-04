#!/usr/bin/env python3
"""
Process Monitoring Script With Alerting
- Tracks processes in real time with psutil
- Preserves ended processes in memory to keep ancestry
- Logs to CSV and NDJSON-formatted log files
- Alerts on "ghost" ancestry: a living process that descended from a dead ancestor
- Alerts on user-defined anomalies (e.g., too many children, deep chains, high spawn rate)
- Monitors and flags anomalous changes in process privileges and priorities
- Flags unauthorized elevated privileges based on a whitelist
"""

import psutil
import time
import csv
import signal
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import deque
import platform
import ctypes
import json
import os

# Global settings
MONITOR_INTERVAL = 2.0            # seconds
MAX_SPAWN_RATE = 10               # children per parent in the last minute
MAX_CHILD_PROCESSES = 20          # total children to trigger alert
MAX_TREE_DEPTH = 10               # if deeper than this, alert as a "deep chain"
CSV_FILENAME = "process_monitor_log.csv"
LOG_DIR = "logs"
LOG_FILENAME = os.path.join(LOG_DIR, "process_monitor.ndjson")  # NDJSON log
RUNNING = True

# Anomalous thresholds for privilege and priority changes
PRIVILEGE_CHANGE_FLAG = True
PRIORITY_CHANGE_FLAG = True

# Whitelist of legitimate elevated processes
WHITELIST = {
    "Windows": {
        "svchost.exe",
        "explorer.exe",
        "services.exe",
        "taskhostw.exe",
        "system",
        "wininit.exe",
        "csrss.exe",
        "lsass.exe",
        # Add other legitimate elevated processes as needed
    },
    "Linux": {
        "init",
        "systemd",
        "sshd",
        "cron",
        "bash",
        # Add other legitimate elevated processes as needed
    },
    "Darwin": {  # macOS
        "launchd",
        "kernel_task",
        "syslogd",
        "mds",
        # Add other legitimate elevated processes as needed
    }
}

# process_info structure:
# {
#   (pid, create_time): {
#       'pid': int,
#       'name': str,
#       'ppid': int,
#       'start_time': datetime,
#       'end_time': datetime or None,
#       'children': set of child_keys,
#       'spawn_times': deque of datetimes,
#       'ancestry': list of ancestor pids,
#       'user': str,
#       'priority': int,
#       'initial_elevated': bool,  # To track privilege escalation
#   }
# }
process_info = {}


def setup_logging():
    """
    Set up logging configuration so that it follows the NDJSON schema:
    Each line is one JSON object containing:
    {
      "timestamp": "%(asctime)s",
      "level": "%(levelname)s",
      "script": "%(name)s",
      "module": "%(module)s",
      "funcName": "%(funcName)s",
      "lineNo": "%(lineno)d",
      "message": "%(message)s"
    }
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Capture all levels of logs

    # Define the JSON schema format
    json_format = (
        '{"timestamp": "%(asctime)s", '
        '"level": "%(levelname)s", '
        '"script": "%(name)s", '
        '"module": "%(module)s", '
        '"funcName": "%(funcName)s", '
        '"lineNo": "%(lineno)d", '
        '"message": "%(message)s"}'
    )

    # Create a formatter that uses the schema above
    formatter = logging.Formatter(fmt=json_format, datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)  # Print INFO and above to console
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Ensure the logs directory exists on Windows and other platforms
    os.makedirs(LOG_DIR, exist_ok=True)

    # Rotating file handler (NDJSON file)
    fh = RotatingFileHandler(LOG_FILENAME, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(logging.DEBUG)  # Log all levels to file
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


# Initialize logger
logger = setup_logging()


def signal_handler(signum, frame):
    """
    Graceful termination handler for SIGINT/SIGTERM.
    """
    global RUNNING
    logger.info("Caught termination signal. Stopping monitoring...")
    RUNNING = False


def get_process_key(pid, create_time):
    """
    Generate a unique key for a process based on PID and create_time.
    """
    return (pid, create_time)


def init_csv_file(filename):
    """
    Initialize or overwrite the CSV file with a header row.
    """
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "PID",
                "Name",
                "PPID",
                "Start Time",
                "End Time",
                "Current Spawn Rate (last 1 min)",
                "Total Children",
                "Ancestry",
                "User",
                "Priority"
            ])
        logger.info(f"Initialized CSV file: {filename}")
    except Exception as e:
        logger.error(f"Failed to initialize CSV file {filename}: {e}")


def log_process_state(pid, info):
    """
    Log the current state of a process to the CSV file.
    """
    try:
        with open(CSV_FILENAME, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)

            end_time_str = info['end_time'].strftime("%Y-%m-%d %H:%M:%S") if info['end_time'] else ""
            current_spawn_rate = get_current_spawn_rate(info['spawn_times'])
            ancestry_str = "->".join(map(str, info.get('ancestry', [])))  # e.g. "1->123->456"
            user = info.get('user', '')
            priority = info.get('priority', '')

            writer.writerow([
                pid,
                info['name'],
                info['ppid'],
                info['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
                end_time_str,
                current_spawn_rate,
                len(info['children']),
                ancestry_str,
                user,
                priority
            ])
        logger.debug(f"Logged process state: PID={pid}, Name={info['name']}")
    except Exception as e:
        logger.error(f"Failed to log process state for PID {pid}: {e}")


def get_current_spawn_rate(spawn_times):
    """
    Returns how many children were spawned in the last 60 seconds.
    Removes old timestamps from the left of the deque.
    """
    now = datetime.now()
    while spawn_times and (now - spawn_times[0]).total_seconds() > 60:
        spawn_times.popleft()
    return len(spawn_times)


def collect_initial_processes():
    """
    Gather all currently running processes at startup
    and build parent-child relationships + ancestry.
    """
    logger.info("Collecting initial processes...")
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'create_time']):
        try:
            pid = proc.info['pid']
            ppid = proc.info['ppid']
            name = proc.info['name']
            ctime = datetime.fromtimestamp(proc.info['create_time'])
            key = get_process_key(pid, ctime)

            # Retrieve user and priority
            try:
                user = proc.username()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                user = "N/A"

            try:
                priority = proc.nice()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                priority = "N/A"

            if key not in process_info:
                # Determine if process is elevated
                elevated = False
                system = platform.system()
                if system == "Windows":
                    elevated = is_elevated_windows(proc)
                else:
                    elevated = is_elevated_unix(proc)

                # Check if elevated and not whitelisted
                if elevated and name.lower() not in [w.lower() for w in WHITELIST.get(system, [])]:
                    message = f"Unauthorized elevated privileges detected at startup: PID={pid}, Name={name}, User={user}"
                    logger.warning(message)

                process_info[key] = {
                    'pid': pid,
                    'name': name,
                    'ppid': ppid,
                    'start_time': ctime,
                    'end_time': None,
                    'children': set(),
                    'spawn_times': deque(),
                    'ancestry': [],
                    'user': user,
                    'priority': priority,
                    'initial_elevated': elevated
                }

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Failed to access process info: {e}")

    # Build parent-child relationships
    for key, info in process_info.items():
        ppid = info['ppid']
        parent_keys = [k for k in process_info if k[0] == ppid]
        for parent_key in parent_keys:
            process_info[parent_key]['children'].add(key)

    # Build ancestry
    for key in process_info:
        process_info[key]['ancestry'] = build_ancestry(key)

    logger.info(f"Initial process collection complete. Total processes tracked: {len(process_info)}")


def build_ancestry(key):
    """
    Return a list of ancestor pids leading up to a root (or until PPID=0 or unknown).
    Example: [1, 42, 100] if 100->42->1 is the chain above pid.
    """
    lineage = []
    current_key = key
    visited = set()

    while current_key in process_info and current_key not in visited:
        visited.add(current_key)
        parent_pid = process_info[current_key]['ppid']
        if parent_pid == 0:
            break
        parent_keys = [k for k in process_info if k[0] == parent_pid]
        if not parent_keys:
            break
        parent_key = parent_keys[0]
        if parent_key in lineage:
            logger.error(
                f"Circular ancestry detected: Process {key[0]} has ancestor PID={parent_key[0]} already in lineage."
            )
            break
        lineage.append(parent_key)
        current_key = parent_key

    lineage_pids = [k[0] for k in lineage]
    lineage_pids.reverse()
    return lineage_pids


def is_elevated_windows(proc):
    """
    Determines if a process is running with elevated privileges on Windows.
    """
    try:
        PROCESS_QUERY_INFORMATION = 0x0400
        TOKEN_QUERY = 0x0008
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, proc.pid)
        if not handle:
            return False
        token = ctypes.c_void_p()
        if not ctypes.windll.advapi32.OpenProcessToken(handle, TOKEN_QUERY, ctypes.byref(token)):
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        elevation = ctypes.c_ulong()
        size = ctypes.c_ulong()
        # TokenElevation = 20
        ctypes.windll.advapi32.GetTokenInformation(
            token, 20, ctypes.byref(elevation), ctypes.sizeof(elevation), ctypes.byref(size)
        )
        ctypes.windll.advapi32.CloseHandle(token)
        ctypes.windll.kernel32.CloseHandle(handle)
        return elevation.value == 1
    except:
        return False


def is_elevated_unix(proc):
    """
    Determines if a process is running with elevated privileges on Unix-like systems.
    """
    try:
        return proc.uids().real == 0
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def detect_elevated_privileges(pid, proc):
    """
    Detects if a process has elevated privileges and is not whitelisted.
    """
    system = platform.system()

    if system == "Windows":
        elevated = is_elevated_windows(proc)
    else:
        elevated = is_elevated_unix(proc)

    process_name = proc.name().lower()

    if elevated and process_name not in [name.lower() for name in WHITELIST.get(system, [])]:
        message = f"Unauthorized elevated privileges detected: PID={pid}, Name={proc.name()}, User={proc.username()}"
        logger.warning(message)


def detect_priority_anomalies(pid, proc, priority):
    """
    Detects if a process has anomalous priority levels.
    """
    system = platform.system()
    anomaly = False
    anomaly_details = {}

    if system == "Windows":
        # On Windows, psutil uses constants for classes:
        # psutil.NORMAL_PRIORITY_CLASS, psutil.HIGH_PRIORITY_CLASS, etc.
        high_priorities = {psutil.HIGH_PRIORITY_CLASS, psutil.REALTIME_PRIORITY_CLASS}
        if priority in high_priorities:
            anomaly = True
            anomaly_details = {
                'priority_level': priority,
                'description': 'High or Realtime priority class'
            }
    else:
        # On Unix, priority = niceness (int). Lower is higher priority.
        if isinstance(priority, int):
            if priority < -10:
                anomaly = True
                anomaly_details = {
                    'niceness': priority,
                    'description': 'Unusually high priority (low niceness)'
                }
            elif priority > 10:
                anomaly = True
                anomaly_details = {
                    'niceness': priority,
                    'description': 'Unusually low priority (high niceness)'
                }

    if anomaly:
        message = (f"Anomalous priority detected: PID={pid}, Priority={priority}, "
                   f"Description={anomaly_details['description']}")
        logger.warning(message)


def update_processes():
    """
    Periodically called:
    - detect new processes
    - detect ended processes
    - maintain parent-child links
    - maintain ancestry
    - monitor privilege and priority changes
    """
    current_pids = set()

    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'create_time']):
        try:
            pid = proc.info['pid']
            ppid = proc.info['ppid']
            name = proc.info['name']
            ctime = datetime.fromtimestamp(proc.info['create_time'])
            key = get_process_key(pid, ctime)

            # Retrieve user and priority
            try:
                user = proc.username()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                user = "N/A"

            try:
                priority = proc.nice()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                priority = "N/A"

            current_pids.add(pid)

            # New process
            if key not in process_info:
                system = platform.system()
                if system == "Windows":
                    elevated = is_elevated_windows(proc)
                else:
                    elevated = is_elevated_unix(proc)

                if elevated and name.lower() not in [w.lower() for w in WHITELIST.get(system, [])]:
                    message = f"Unauthorized elevated privileges detected: PID={pid}, Name={name}, User={user}"
                    logger.warning(message)

                process_info[key] = {
                    'pid': pid,
                    'name': name,
                    'ppid': ppid,
                    'start_time': ctime,
                    'end_time': None,
                    'children': set(),
                    'spawn_times': deque(),
                    'ancestry': [],
                    'user': user,
                    'priority': priority,
                    'initial_elevated': elevated
                }

                # Add to parent's children set
                parent_keys = [k for k in process_info if k[0] == ppid]
                for parent_key in parent_keys:
                    process_info[parent_key]['children'].add(key)
                    process_info[parent_key]['spawn_times'].append(datetime.now())

                process_info[key]['ancestry'] = build_ancestry(key)

                logger.info(f"New process detected -> PID: {pid}, Name: {name}, PPID: {ppid}, User: {user}, Priority: {priority}")

                # Check privileges / anomalies
                detect_elevated_privileges(pid, proc)
                detect_priority_anomalies(pid, proc, priority)

            else:
                # Existing process
                existing_info = process_info[key]
                anomalies_detected = False

                # Check user change
                if PRIVILEGE_CHANGE_FLAG and existing_info.get('user') != user:
                    message = (f"Privilege change detected: PID={pid}, "
                               f"Old User={existing_info.get('user')}, New User={user}")
                    logger.warning(message)
                    anomalies_detected = True

                # Check priority change
                if PRIORITY_CHANGE_FLAG and existing_info.get('priority') != priority:
                    message = (f"Priority change detected: PID={pid}, "
                               f"Old Priority={existing_info.get('priority')}, New Priority={priority}")
                    logger.warning(message)
                    anomalies_detected = True

                if anomalies_detected:
                    existing_info['user'] = user
                    existing_info['priority'] = priority

                # Re-check privileges / anomalies
                detect_elevated_privileges(pid, proc)
                detect_priority_anomalies(pid, proc, priority)

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Failed to access process info: {e}")


def detect_anomalies():
    """
    Check various anomaly conditions:
    - High spawn rate
    - Too many children
    - Deep chain
    - Ghost ancestry
    """
    # 1) High spawn rate & too many children
    for key, info in process_info.items():
        if info['end_time'] is None:
            spawn_rate = get_current_spawn_rate(info['spawn_times'])
            if spawn_rate > MAX_SPAWN_RATE:
                message = f"High spawning rate: PID={info['pid']}, Rate={spawn_rate} > {MAX_SPAWN_RATE}"
                logger.warning(message)

            num_children = len(info['children'])
            if num_children > MAX_CHILD_PROCESSES:
                message = (f"Process {info['pid']} ({info['name']}) has too many children "
                           f"({num_children} > {MAX_CHILD_PROCESSES})")
                logger.warning(message)

    # 2) Deep chain check
    for key, info in process_info.items():
        if info['end_time'] is not None:
            continue
        depth = get_max_chain_depth(key)
        if depth > MAX_TREE_DEPTH:
            message = (f"Deep chain detected starting at PID={info['pid']} ({info['name']}), "
                       f"Depth={depth} > {MAX_TREE_DEPTH}")
            logger.warning(message)

    # 3) Ghost ancestry check
    for key, info in process_info.items():
        if info['end_time'] is None:
            ghost_ancestor = get_ended_ancestor(key)
            if ghost_ancestor is not None:
                ga_info = process_info[ghost_ancestor]
                message = (f"Process {info['pid']} ({info['name']}) is alive but has an ended ancestor "
                           f"{ga_info['pid']} ({ga_info['name']}).")
                logger.warning(message)


def get_max_chain_depth(start_key):
    """
    Iterative DFS to compute the max depth from this pid downwards.
    """
    if start_key not in process_info:
        return 0
    visited = set()
    stack = [(start_key, 1)]
    max_depth = 1

    while stack:
        current_key, depth = stack.pop()
        if current_key in visited:
            continue
        visited.add(current_key)
        max_depth = max(max_depth, depth)
        children = process_info[current_key]['children'] if current_key in process_info else []
        for child_key in children:
            stack.append((child_key, depth + 1))

    return max_depth


def get_ended_ancestor(key):
    """
    Return the first ended ancestor's PID if any exist, else None.
    """
    if key not in process_info:
        return None

    for ancestor_pid in process_info[key]['ancestry']:
        ancestor_keys = [k for k in process_info if k[0] == ancestor_pid]
        for ancestor_key in ancestor_keys:
            if process_info[ancestor_key]['end_time'] is not None:
                return ancestor_key[0]
    return None


def print_process_tree():
    """
    Print a simple hierarchical tree of all processes we know about
    (both alive and ended).
    """
    roots = []
    for key, info in process_info.items():
        ppid = info['ppid']
        if ppid not in [k[0] for k in process_info] or ppid == 0:
            roots.append(key)

    roots.sort()
    logger.info("=== Process Tree (Including Ended Processes) ===")
    for root_key in roots:
        print_tree_recursive(root_key, 0)
    logger.info("=== End of Process Tree ===")


def print_tree_recursive(key, level):
    if key not in process_info:
        return
    info = process_info[key]
    indent = "  " * level
    ended_marker = " [ENDED]" if info['end_time'] else ""
    message = f"{indent}- PID={info['pid']}, Name={info['name']}{ended_marker}"
    logger.info(message)

    children = sorted(info['children'], key=lambda x: x[0])
    for child_key in children:
        print_tree_recursive(child_key, level + 1)


def main():
    global RUNNING

    # Attempt to register both SIGINT and SIGTERM where supported
    # On Windows, SIGTERM may not be available
    try:
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl + C
        signal.signal(signal.SIGTERM, signal_handler)  # Graceful termination (Unix)
    except AttributeError:
        # Windows typically doesn't define SIGTERM
        signal.signal(signal.SIGINT, signal_handler)

    logger.info("Initializing CSV file...")
    init_csv_file(CSV_FILENAME)

    logger.info("Collecting initial processes...")
    collect_initial_processes()

    logger.info("Starting process monitoring...")
    while RUNNING:
        try:
            update_processes()
            detect_anomalies()
            time.sleep(MONITOR_INTERVAL)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            time.sleep(MONITOR_INTERVAL)

    # On exit, log the final state for any processes that remain
    logger.info("Finalizing...")
    for key, info in list(process_info.items()):
        pid = info['pid']
        if info['end_time'] is None:
            info['end_time'] = datetime.now()
        log_process_state(pid, info)

    print_process_tree()
    logger.info(f"Monitoring stopped. CSV data available in: {CSV_FILENAME}")
    logger.info(f"NDJSON log data available in: {LOG_FILENAME}")


if __name__ == "__main__":
    main()
