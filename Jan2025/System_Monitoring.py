import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import subprocess
from datetime import datetime

class IntelligentTaskManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Intelligent Task Manager")
        self.geometry("1200x700")

        # Title Label (styled later in set_styles)
        self.title_label = tk.Label(
            self,
            text="Intelligent Task Manager",
            font=("Helvetica", 24, "bold"),
            pady=10,
        )
        self.title_label.pack(fill=tk.X)

        # Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Add Tabs
        self.task_manager_tab()
        self.resource_monitor_tab()
        self.security_commands_tab()
        self.backend_commands_tab()
        self.ip_monitor_tab()

        # Configure ttk style and apply color scheme
        style = ttk.Style(self)
        style.theme_use("clam")
        self.set_styles()

        # Load Tasks Initially
        self.refresh_tasks()

    # ==============================
    # TASK MANAGER TAB
    # ==============================
    def task_manager_tab(self):
        self.task_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.task_frame, text="Task Manager")

        # Header
        header_frame = ttk.Frame(self.task_frame)
        header_frame.pack(fill=tk.X, pady=10)
        ttk.Label(header_frame, text="Running Processes", font=("Helvetica", 16, "bold")).pack(side=tk.LEFT, padx=10)

        # Search Bar
        search_frame = ttk.Frame(self.task_frame)
        search_frame.pack(fill=tk.X, pady=10)
        ttk.Label(search_frame, text="Search:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        search_button = ttk.Button(search_frame, text="Search", command=self.search_tasks)
        search_button.pack(side=tk.LEFT, padx=5)

        clear_button = ttk.Button(search_frame, text="Clear", command=self.refresh_tasks)
        clear_button.pack(side=tk.LEFT, padx=5)

        # Task List Table
        table_frame = ttk.Frame(self.task_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.tree = ttk.Treeview(
            table_frame,
            columns=(
                "Name", "PID", "Executable Path", "User", "CWD", "Command-Line Arguments",
                "Open Files", "CPU %", "Memory %", "Connections"
            ),
            show="headings",
            height=20,
        )
        columns = [
            ("Name", 200), ("PID", 80), ("Executable Path", 200), ("User", 100),
            ("CWD", 200), ("Command-Line Arguments", 150), ("Open Files", 120),
            ("CPU %", 80), ("Memory %", 80), ("Connections", 100),
        ]
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Refresh and Kill Buttons
        button_frame = ttk.Frame(self.task_frame)
        button_frame.pack(pady=10)
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_tasks)
        refresh_button.grid(row=0, column=0, padx=10)

        ttk.Label(button_frame, text="Enter PID to terminate:").grid(row=0, column=1, padx=5)
        self.pid_entry = ttk.Entry(button_frame, width=10)
        self.pid_entry.grid(row=0, column=2, padx=5)

        kill_button = ttk.Button(button_frame, text="End Task", command=self.kill_process)
        kill_button.grid(row=0, column=3, padx=10)

    def refresh_tasks(self):
        self.search_entry.delete(0, tk.END)
        self.populate_tasks()

    def populate_tasks(self, filter_text=""):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for proc in psutil.process_iter(["pid", "name", "exe", "username", "cwd", "cmdline", "cpu_percent", "memory_percent"]):
            try:
                name = proc.info["name"] or "N/A"
                pid = proc.info["pid"]
                exe_path = proc.info["exe"] or "N/A"
                user = proc.info["username"] or "N/A"
                cwd = proc.info["cwd"] or "N/A"
                cmd_args = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else "N/A"

                cpu_value = proc.info["cpu_percent"] if proc.info["cpu_percent"] is not None else 0
                cpu = f"{cpu_value}%"

                mem_value = proc.info["memory_percent"] if proc.info["memory_percent"] is not None else 0
                memory = f"{mem_value:.2f}%"

                open_files = len(proc.open_files()) if proc.open_files() else 0
                connections = len(proc.net_connections()) if proc.net_connections() else 0

                row = [name, str(pid), exe_path, user, cwd, cmd_args, str(open_files), cpu, memory, str(connections)]
                if filter_text.lower() in " ".join(row).lower():
                    self.tree.insert("", tk.END, values=row)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    def search_tasks(self):
        filter_text = self.search_entry.get()
        self.populate_tasks(filter_text)

    def kill_process(self):
        pid = self.pid_entry.get()
        if pid.isdigit():
            try:
                os.kill(int(pid), 9)  # '9' is like SIGKILL on Unix; on Windows it'll attempt to force-kill
                messagebox.showinfo("Success", f"Process with PID {pid} terminated.")
                self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to terminate process: {e}")
        else:
            messagebox.showwarning("Warning", "Please enter a valid PID.")

    # ==============================
    # RESOURCE MONITOR TAB
    # ==============================
    def resource_monitor_tab(self):
        self.resource_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.resource_frame, text="Resource Monitor")

        header_frame = ttk.Frame(self.resource_frame)
        header_frame.pack(fill=tk.X, pady=10)
        ttk.Label(header_frame, text="System Resource Usage", font=("Helvetica", 16, "bold")).pack(side=tk.LEFT, padx=10)

        self.add_resource_bar(self.resource_frame, "CPU Usage", "cpu")
        self.add_resource_bar(self.resource_frame, "Memory Usage", "memory")
        self.add_resource_bar(self.resource_frame, "Disk Usage", "disk")

        self.after(1000, self.update_resources)

    def add_resource_bar(self, parent, label_text, resource_type):
        frame = ttk.Frame(parent, padding=5)
        frame.pack(fill=tk.X, pady=5)
        label = ttk.Label(frame, text=f"{label_text}: 0%", font=("Helvetica", 12))
        label.pack(side=tk.LEFT, padx=5)

        canvas = tk.Canvas(frame, width=300, height=20, highlightthickness=1)
        canvas.pack(side=tk.LEFT, padx=5)
        bar = canvas.create_rectangle(0, 0, 0, 20, fill="#007f0e")
        setattr(self, f"{resource_type}_label", label)
        setattr(self, f"{resource_type}_bar", bar)
        setattr(self, f"{resource_type}_canvas", canvas)

    def update_resources(self):
        self.update_resource_bar("cpu", psutil.cpu_percent())
        self.update_resource_bar("memory", psutil.virtual_memory().percent)
        self.update_resource_bar("disk", psutil.disk_usage("/").percent)
        self.after(1000, self.update_resources)

    def update_resource_bar(self, resource_type, usage):
        label = getattr(self, f"{resource_type}_label")
        bar = getattr(self, f"{resource_type}_bar")
        canvas = getattr(self, f"{resource_type}_canvas")

        canvas_width = 300
        fill_width = (usage / 100) * canvas_width
        canvas.coords(bar, 0, 0, fill_width, 20)
        label.config(text=f"{resource_type.capitalize()} Usage: {usage}%")

    # ==============================
    # SECURITY COMMANDS TAB
    # ==============================
    def security_commands_tab(self):
        self.security_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.security_frame, text="Security Commands")

        # Left Side: Command Buttons
        button_frame = ttk.Frame(self.security_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        commands = [
            ("List Scheduled Tasks", "schtasks /query /FO LIST"),
        ]
        for label, command in commands:
            btn = ttk.Button(button_frame, text=label, command=lambda cmd=command: self.run_command(cmd), width=20)
            btn.pack(pady=5, fill=tk.X)

        # Right Side: Output Area
        output_frame = ttk.Frame(self.security_frame)
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scheduled_tasks_tree = ttk.Treeview(
            output_frame,
            columns=("Task Name", "Next Run Time", "Status", "Start Time", "Duration", "Timestamp"),
            show="headings",
            height=20,
        )
        columns = [
            ("Task Name", 200), ("Next Run Time", 150), ("Status", 100),
            ("Start Time", 150), ("Duration", 150), ("Timestamp", 150)
        ]
        for col, width in columns:
            self.scheduled_tasks_tree.heading(col, text=col)
            self.scheduled_tasks_tree.column(col, width=width, anchor="center")
        self.scheduled_tasks_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def run_command(self, command):
        if "schtasks" in command:
            self.list_scheduled_tasks(command)

    def list_scheduled_tasks(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                tasks = []
                current_task = {}
                for line in lines:
                    if ":" in line:
                        key, value = map(str.strip, line.split(":", 1))
                        current_task[key] = value
                    elif line.strip() == "":
                        if current_task:
                            tasks.append(current_task)
                            current_task = {}
                # Clear existing rows
                for item in self.scheduled_tasks_tree.get_children():
                    self.scheduled_tasks_tree.delete(item)
                # Insert new rows
                for task in tasks:
                    task_name = task.get("TaskName", "").strip()
                    next_run_time = task.get("Next Run Time", "").strip()
                    status = task.get("Status", "").strip()
                    start_time = task.get("Start Time", "").strip()
                    duration = self.calculate_duration(start_time) if start_time else "N/A"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.scheduled_tasks_tree.insert(
                        "", tk.END, values=(task_name, next_run_time, status, start_time, duration, timestamp)
                    )
            else:
                messagebox.showerror("Error", f"Failed to fetch scheduled tasks: {result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def calculate_duration(self, start_time):
        """Calculate the duration since the task started."""
        try:
            start_datetime = datetime.strptime(start_time, "%I:%M:%S %p")
            now_datetime = datetime.now()
            duration = now_datetime - start_datetime.replace(
                year=now_datetime.year, month=now_datetime.month, day=now_datetime.day
            )
            return str(duration).split(".")[0]
        except ValueError:
            return "N/A"

    # ==============================
    # BACKEND COMMANDS TAB
    # ==============================
    def backend_commands_tab(self):
        self.backend_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.backend_frame, text="Backend Commands")

        # Scrollable Frame for All Processes
        all_processes_frame = ttk.Frame(self.backend_frame, padding=5)
        all_processes_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(all_processes_frame, text="All Processes", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        all_scroll_frame = ttk.Frame(all_processes_frame)
        all_scroll_frame.pack(fill=tk.BOTH, expand=True)
        all_scroll_canvas = tk.Canvas(all_scroll_frame, highlightthickness=0)
        all_scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        all_scrollbar = ttk.Scrollbar(all_scroll_frame, orient=tk.VERTICAL, command=all_scroll_canvas.yview)
        all_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        all_scroll_canvas.configure(yscrollcommand=all_scrollbar.set)
        all_scroll_canvas.bind("<Configure>", lambda e: all_scroll_canvas.configure(scrollregion=all_scroll_canvas.bbox("all")))
        all_inner_frame = ttk.Frame(all_scroll_canvas)
        all_scroll_canvas.create_window((0, 0), window=all_inner_frame, anchor="nw")

        self.all_backend_tree = ttk.Treeview(
            all_inner_frame,
            columns=("PID", "Name", "Command", "Start Time", "Duration", "Status", "Source File"),
            show="headings",
            height=10,
        )
        columns = [
            ("PID", 80), ("Name", 150), ("Command", 250),
            ("Start Time", 150), ("Duration", 100), ("Status", 100), ("Source File", 150)
        ]
        for col, width in columns:
            self.all_backend_tree.heading(col, text=col)
            self.all_backend_tree.column(col, width=width, anchor="center")
        self.all_backend_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollable Frame for System32 Processes
        system32_frame = ttk.Frame(self.backend_frame, padding=5)
        system32_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(system32_frame, text="System32 Processes", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        system32_scroll_frame = ttk.Frame(system32_frame)
        system32_scroll_frame.pack(fill=tk.BOTH, expand=True)
        system32_scroll_canvas = tk.Canvas(system32_scroll_frame, highlightthickness=0)
        system32_scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        system32_scrollbar = ttk.Scrollbar(system32_scroll_frame, orient=tk.VERTICAL, command=system32_scroll_canvas.yview)
        system32_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        system32_scroll_canvas.configure(yscrollcommand=system32_scrollbar.set)
        system32_scroll_canvas.bind("<Configure>", lambda e: system32_scroll_canvas.configure(scrollregion=system32_scroll_canvas.bbox("all")))
        system32_inner_frame = ttk.Frame(system32_scroll_canvas)
        system32_scroll_canvas.create_window((0, 0), window=system32_inner_frame, anchor="nw")

        self.system32_backend_tree = ttk.Treeview(
            system32_inner_frame,
            columns=("PID", "Name", "Command", "Start Time", "Duration", "Status", "Source File"),
            show="headings",
            height=10,
        )
        for col, width in columns:
            self.system32_backend_tree.heading(col, text=col)
            self.system32_backend_tree.column(col, width=width, anchor="center")
        self.system32_backend_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.processes_info = {}
        self.monitor_backend_commands()

    def monitor_backend_commands(self):
        try:
            current_processes = {
                proc.info["pid"]: proc.info
                for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"])
            }
            # Clear existing rows
            for item in self.all_backend_tree.get_children():
                self.all_backend_tree.delete(item)
            for item in self.system32_backend_tree.get_children():
                self.system32_backend_tree.delete(item)

            # Update process info
            for pid, proc_info in current_processes.items():
                if pid not in self.processes_info:
                    self.processes_info[pid] = {
                        "start_time": datetime.fromtimestamp(proc_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
                        "duration": "Active",
                        "status": "Active",
                        "source_file": proc_info["cmdline"][0] if proc_info["cmdline"] else "N/A"
                    }
                # Calculate duration for active processes
                if self.processes_info[pid]["status"] == "Active":
                    start_time = datetime.strptime(self.processes_info[pid]["start_time"], "%Y-%m-%d %H:%M:%S")
                    duration = datetime.now() - start_time
                    self.processes_info[pid]["duration"] = str(duration).split(".")[0]

                # Insert into the correct tree
                tree = self.system32_backend_tree if "System32" in self.processes_info[pid]["source_file"] else self.all_backend_tree
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        pid,
                        proc_info["name"],
                        " ".join(proc_info["cmdline"]) if proc_info["cmdline"] else "N/A",
                        self.processes_info[pid]["start_time"],
                        self.processes_info[pid]["duration"],
                        self.processes_info[pid]["status"],
                        self.processes_info[pid]["source_file"]
                    )
                )

            # Mark processes that have ended as inactive
            for pid in list(self.processes_info.keys()):
                if pid not in current_processes:
                    self.processes_info[pid]["status"] = "Inactive"
                    self.processes_info[pid]["duration"] = "N/A"
        except Exception as e:
            print(f"Error monitoring backend commands: {e}")

        self.after(5000, self.monitor_backend_commands)

    # ==============================
    # IP MONITOR TAB
    # ==============================
    def ip_monitor_tab(self):
        self.ip_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.ip_frame, text="IP Monitor")

        # IPv4 Table
        ipv4_frame = ttk.Frame(self.ip_frame, padding=5)
        ipv4_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(ipv4_frame, text="IPv4 Connections", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        ipv4_scroll_frame = ttk.Frame(ipv4_frame)
        ipv4_scroll_frame.pack(fill=tk.BOTH, expand=True)
        ipv4_scroll_canvas = tk.Canvas(ipv4_scroll_frame, highlightthickness=0)
        ipv4_scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ipv4_scrollbar = ttk.Scrollbar(ipv4_scroll_frame, orient=tk.VERTICAL, command=ipv4_scroll_canvas.yview)
        ipv4_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ipv4_scroll_canvas.configure(yscrollcommand=ipv4_scrollbar.set)
        ipv4_scroll_canvas.bind("<Configure>", lambda e: ipv4_scroll_canvas.configure(scrollregion=ipv4_scroll_canvas.bbox("all")))
        ipv4_inner_frame = ttk.Frame(ipv4_scroll_canvas)
        ipv4_scroll_canvas.create_window((0, 0), window=ipv4_inner_frame, anchor="nw")

        self.ipv4_tree = ttk.Treeview(
            ipv4_inner_frame,
            columns=("IP Address", "Status", "Connected At", "Disconnected At", "Session Duration", "Session Data"),
            show="headings",
            height=10,
        )
        columns = [
            ("IP Address", 150), ("Status", 100), ("Connected At", 150),
            ("Disconnected At", 150), ("Session Duration", 150), ("Session Data", 200)
        ]
        for col, width in columns:
            self.ipv4_tree.heading(col, text=col)
            self.ipv4_tree.column(col, width=width, anchor="center")
        self.ipv4_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # IPv6 Table
        ipv6_frame = ttk.Frame(self.ip_frame, padding=5)
        ipv6_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(ipv6_frame, text="IPv6 Connections", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        ipv6_scroll_frame = ttk.Frame(ipv6_frame)
        ipv6_scroll_frame.pack(fill=tk.BOTH, expand=True)
        ipv6_scroll_canvas = tk.Canvas(ipv6_scroll_frame, highlightthickness=0)
        ipv6_scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ipv6_scrollbar = ttk.Scrollbar(ipv6_scroll_frame, orient=tk.VERTICAL, command=ipv6_scroll_canvas.yview)
        ipv6_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ipv6_scroll_canvas.configure(yscrollcommand=ipv6_scrollbar.set)
        ipv6_scroll_canvas.bind("<Configure>", lambda e: ipv6_scroll_canvas.configure(scrollregion=ipv6_scroll_canvas.bbox("all")))
        ipv6_inner_frame = ttk.Frame(ipv6_scroll_canvas)
        ipv6_scroll_canvas.create_window((0, 0), window=ipv6_inner_frame, anchor="nw")

        self.ipv6_tree = ttk.Treeview(
            ipv6_inner_frame,
            columns=("IP Address", "Status", "Connected At", "Disconnected At", "Session Duration", "Session Data"),
            show="headings",
            height=10,
        )
        for col, width in columns:
            self.ipv6_tree.heading(col, text=col)
            self.ipv6_tree.column(col, width=width, anchor="center")
        self.ipv6_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.connections = {}
        self.monitor_ip_connections()

    def monitor_ip_connections(self):
        try:
            current_conns = self.get_foreign_connections()
            # Check for new connections
            for ip, details in current_conns.items():
                if ip not in self.connections:
                    self.connections[ip] = details
                    self.insert_connection(ip, details, "Connected")
            # Check for disconnected
            for ip in list(self.connections.keys()):
                if ip not in current_conns and 'disconnected_at' not in self.connections[ip]:
                    self.connections[ip]['disconnected_at'] = datetime.now()
                    self.connections[ip]['bytes_sent'] = psutil.net_io_counters().bytes_sent - self.connections[ip]['bytes_sent']
                    self.connections[ip]['bytes_recv'] = psutil.net_io_counters().bytes_recv - self.connections[ip]['bytes_recv']
                    self.insert_connection(ip, self.connections[ip], "Disconnected")
            # Remove disconnected IPs
            for ip in list(self.connections.keys()):
                if 'disconnected_at' in self.connections[ip]:
                    del self.connections[ip]
        except Exception as e:
            print(f"Error monitoring IP connections: {e}")

        self.after(2000, self.monitor_ip_connections)

    def get_foreign_connections(self):
        """Fetch currently active foreign connections."""
        foreign_conns = {}
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                ip = conn.raddr.ip
                if ip not in foreign_conns:
                    foreign_conns[ip] = {
                        'connected_at': datetime.now(),
                        'bytes_sent': psutil.net_io_counters().bytes_sent,
                        'bytes_recv': psutil.net_io_counters().bytes_recv
                    }
        return foreign_conns

    def insert_connection(self, ip, details, status):
        connected_at = details['connected_at'].strftime("%Y-%m-%d %H:%M:%S")
        disconnected_at = ""
        duration = ""
        if status == "Disconnected":
            disconnected_at = details['disconnected_at'].strftime("%Y-%m-%d %H:%M:%S")
            duration = str(details['disconnected_at'] - details['connected_at']).split(".")[0]
        session_data = f"Sent: {details.get('bytes_sent', 0)}, Received: {details.get('bytes_recv', 0)}"

        # Determine if IPv4 or IPv6
        tree = self.ipv4_tree if "." in ip else self.ipv6_tree

        # Check if the IP already exists
        for item in tree.get_children():
            if tree.item(item, "values")[0] == ip:
                tree.item(item, values=(ip, status, connected_at, disconnected_at, duration, session_data))
                return
        tree.insert("", tk.END, values=(ip, status, connected_at, disconnected_at, duration, session_data))

    # =========================
    #  APPLY COLOR SCHEME HERE
    # =========================
    def set_styles(self):
        """
        Applies the specified color palette to the Tkinter/ttk widgets.
        """
        # Define color palette
        DARK_BLUE = "#04091E"          # Dark Blue
        TEAL_BLUE = "#027B8C"          # Muted Teal Blue
        CYAN_BLUE = "#008FBF"          # Muted Cyan Blue
        DARK_GREEN = "#228B22"         # Dark Green
        DARK_RED = "#B22222"           # Dark Red
        LIGHT_GRAY = "#D9E2EC"         # White/Light Gray
        ENTRY_BG = "#1C2B36"           # Slightly lighter than DARK_BLUE for contrast
        FRAME_BG = "#022B3A"           # Slightly different shade for frames
        BUTTON_ACTIVE_BG = "#025E73"   # Darker teal for active state
        TREEVIEW_BG = "#1C2B36"        # Background for Treeview
        TREEVIEW_TEXT = "#D9E2EC"      # Text color for Treeview
        TREEVIEW_HEADER_BG = TEAL_BLUE
        TREEVIEW_HEADER_FG = LIGHT_GRAY

        # Create or retrieve the current ttk Style
        style = ttk.Style(self)
        style.theme_use("clam")  # Base theme before we override

        # Main window background
        self.configure(bg=DARK_BLUE)

        # Title label background / foreground
        self.title_label.configure(bg=TEAL_BLUE, fg=LIGHT_GRAY)

        # Notebook
        style.configure("TNotebook", background=FRAME_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=FRAME_BG, foreground=LIGHT_GRAY)
        style.map("TNotebook.Tab",
                  background=[("selected", TEAL_BLUE)],
                  foreground=[("selected", LIGHT_GRAY)]
                 )

        # Frames
        style.configure("TFrame", background=FRAME_BG)

        # Labels
        style.configure("TLabel", background=FRAME_BG, foreground=LIGHT_GRAY)

        # Buttons
        style.configure("TButton",
                        background=TEAL_BLUE,
                        foreground=LIGHT_GRAY,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="none")
        style.map("TButton",
                  background=[("active", BUTTON_ACTIVE_BG), ("pressed", BUTTON_ACTIVE_BG)],
                  foreground=[("active", LIGHT_GRAY), ("pressed", LIGHT_GRAY)]
                 )

        # Entry
        style.configure("TEntry",
                        fieldbackground=ENTRY_BG,
                        foreground=LIGHT_GRAY,
                        bordercolor=TEAL_BLUE)

        # Treeview (tables)
        style.configure("Treeview",
                        background=TREEVIEW_BG,
                        foreground=TREEVIEW_TEXT,
                        fieldbackground=TREEVIEW_BG,
                        borderwidth=1,
                        rowheight=25)
        style.configure("Treeview.Heading",
                        background=TREEVIEW_HEADER_BG,
                        foreground=TREEVIEW_HEADER_FG,
                        borderwidth=1,
                        font=("Helvetica", 12, "bold"))
        style.map("Treeview.Heading",
                  background=[("active", CYAN_BLUE), ("pressed", CYAN_BLUE)],
                  foreground=[("active", LIGHT_GRAY), ("pressed", LIGHT_GRAY)]
                 )
        style.map("Treeview",
                  background=[("selected", CYAN_BLUE)],
                  foreground=[("selected", LIGHT_GRAY)])


if __name__ == "__main__":
    app = IntelligentTaskManager()
    app.mainloop()
