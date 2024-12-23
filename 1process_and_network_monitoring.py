import psutil
import time
import csv
import os
from datetime import datetime
import wmi
import ctypes
import ctypes.wintypes as wintypes
import threading

# Initialize WMI client
wmi_client = wmi.WMI()

# Constants for privileges
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_QUERY = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

# Privilege Lookup structures
class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", ctypes.c_ulong),
        ("HighPart", ctypes.c_long)
    ]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", ctypes.c_ulong),
    ]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", ctypes.c_ulong),
        ("Privileges", LUID_AND_ATTRIBUTES * 1)
    ]

# Load Windows libraries
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

def get_process_privileges(pid):
    privileges = []
    try:
        hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
        if not hProcess:
            return "Access Denied"
        
        hToken = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(hProcess, TOKEN_QUERY, ctypes.byref(hToken)):
            return "Access Denied"

        privileges_buffer = TOKEN_PRIVILEGES()
        return_length = wintypes.DWORD()
        
        if advapi32.GetTokenInformation(hToken, 3, ctypes.byref(privileges_buffer), ctypes.sizeof(privileges_buffer), ctypes.byref(return_length)):
            for i in range(privileges_buffer.PrivilegeCount):
                attr = privileges_buffer.Privileges[i].Attributes
                privilege_status = "Enabled" if attr & SE_PRIVILEGE_ENABLED else "Disabled"
                privileges.append(f"Privilege {i}: {privilege_status}")
        else:
            return "No Privileges"
        
        kernel32.CloseHandle(hToken)
        kernel32.CloseHandle(hProcess)

    except Exception as e:
        return str(e)
    
    return privileges


def get_network_connections():
    """
    Retrieve network connections and their associated process details.
    """
    connections = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            process_pid = conn.pid if conn.pid else "Unknown"
            laddr = conn.laddr if conn.laddr else ("", "")
            raddr = conn.raddr if conn.raddr else ("", "")
            connection = {
                'pid': process_pid,
                'source_ip': laddr[0],
                'source_port': laddr[1] if len(laddr) > 1 else "",
                'destination_ip': raddr[0] if len(raddr) > 0 else "",
                'destination_port_number': raddr[1] if len(raddr) > 1 else "",
                'status': conn.status
            }
            connections.append(connection)
    except Exception as e:
        print(f"Error fetching network connections: {e}")
    return connections

def collect_combined_info(duration_minutes=15):
    """
    Collect detailed process and network connection information.
    """
    process_info = []
    start_time = time.time()
    active_processes = {}

    while time.time() - start_time < duration_minutes * 60:
        network_data = get_network_connections()

        for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'memory_percent', 'io_counters', 'create_time', 'status', 'username']):
            try:
                pid = proc.info['pid']
                privileges = get_process_privileges(pid)
                runtime = time.time() - proc.create_time()
                priority_class = proc.nice()

                parent_proc = proc.parent() if proc.parent() else None
                parent_pid = parent_proc.pid if parent_proc else "N/A"
                parent_name = parent_proc.name() if parent_proc else "N/A"

                io_counters = proc.info['io_counters'] if proc.info.get('io_counters') else None
                bytes_sent = io_counters.write_bytes if io_counters else "N/A"
                bytes_received = io_counters.read_bytes if io_counters else "N/A"

                related_connections = [conn for conn in network_data if conn['pid'] == pid]

                if pid not in active_processes:
                    active_processes[pid] = {'start_time': time.time(), 'end_time': None}

                for conn in related_connections:
                    combined_info = {
                        'pid': pid,
                        'name': proc.info.get('name', ''),
                        'exe': proc.info.get('exe', ''),
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'memory_percent': proc.memory_percent(),
                        'io_counters': str(proc.info.get('io_counters', '')),
                        'create_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S') if proc.info.get('create_time') else '',
                        'status': conn['status'],
                        'username': proc.info.get('username', 'Unknown'),
                        'priority_class': priority_class,
                        'runtime': runtime,
                        'parent_pid': parent_pid,
                        'parent_name': parent_name,
                        'privileges': privileges,
                        'source_ip': conn['source_ip'],
                        'source_port': conn['source_port'],
                        'destination_ip': conn['destination_ip'],
                        'destination_port_number': conn['destination_port_number'],
                        'bytes_sent': bytes_sent,
                        'bytes_received': bytes_received,
                    }
                    process_info.append(combined_info)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

      
        # Check for process termination
        for pid in list(active_processes.keys()):
            if not psutil.pid_exists(pid) and active_processes[pid]['end_time'] is None:
                active_processes[pid]['end_time'] = time.time()

        # Debug: Print active processes to verify updates
        print(f"Active Processes: {active_processes}")

        time.sleep(5)  # Wait for 5 seconds before checking again

    return process_info, active_processes


def save_to_csv(data, active_processes, filename):
    """
    Save collected process and network information to a CSV file.
    """
    headers = [
        'pid', 'name', 'exe', 'cpu_percent', 'memory_percent', 'io_counters', 'create_time', 'username', 'status',
        'priority_class', 'runtime', 'parent_pid', 'parent_name', 'privileges', 'end_time',
        'source_ip', 'destination_ip', 'bytes_sent', 'bytes_received', 'source_port', 'destination_port_number'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            # Fetch `end_time` for the current process
            pid = row['pid']
            end_time = active_processes.get(pid, {}).get('end_time')
            if end_time:
                row['end_time'] = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                row['end_time'] = 'N/A'

            # Debug: Print each row's end_time
            print(f"PID: {pid}, End Time: {row['end_time']}")

            # Write only keys that match the headers
            filtered_row = {key: row.get(key, '') for key in headers}
            writer.writerow(filtered_row)


def background_collection(duration_minutes=15):
    """
    Collect process and network information in the background.
    """
    process_data, active_processes = collect_combined_info(duration_minutes)
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'full_process_network_info151111.csv')
    save_to_csv(process_data, active_processes, desktop_path)
    print(f"Process information has been saved to {desktop_path}")

# Run in a separate thread
def start_background_task():
    thread = threading.Thread(target=background_collection, args=(15,))
    thread.start()

# Start collection
start_background_task()