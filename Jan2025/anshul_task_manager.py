import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import subprocess
import threading
import time

class IntelligentTaskManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Intelligent Task Manager")
        self.geometry("1200x700")

        # We'll override this background color in set_styles()
        self.configure(bg="#f5f5f5")

        # Title label (styled later in set_styles)
        self.title_label = tk.Label(
            self,
            text="Intelligent Task Manager",
            font=("Helvetica", 24, "bold"),
            bg="#007acc",
            fg="white",
            pady=10
        )
        self.title_label.pack(fill=tk.X)

        # Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Tracking sort states for columns
        self.sort_states = {}

        # Create the tabs
        self.task_manager_tab()
        self.resource_monitor_tab()
        self.settings_tab()

        # Base ttk styling
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 10), rowheight=30)
        style.configure("TButton", font=("Helvetica", 10))

        # Now apply the dark teal/blue color scheme
        self.set_styles()

    def task_manager_tab(self):
        task_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(task_frame, text="Task Manager")

        ttk.Label(task_frame, text="Running Processes", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.tree = ttk.Treeview(
            task_frame,
            columns=(
                "Name", "PID", "Executable Path", "User", "CWD", "Command-Line Arguments",
                "Open Files", "CPU %", "Memory %", "Connections", "Signed", "Publisher"
            ),
            show="headings",
            height=20
        )

        columns = [
            ("Name", 200),
            ("PID", 80),
            ("Executable Path", 200),
            ("User", 100),
            ("CWD", 200),
            ("Command-Line Arguments", 150),
            ("Open Files", 120),
            ("CPU %", 80),
            ("Memory %", 80),
            ("Connections", 100),
            ("Signed", 100),
            ("Publisher", 200)
        ]

        for col, width in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=width)
            self.sort_states[col] = None

        # Remove default gray tag so processes use the default Treeview background
        # Instead, we only configure tags for special states
        # self.tree.tag_configure('gray', background='lightgray')

        self.tree.tag_configure('green', background='lightgreen')
        self.tree.tag_configure('red', background='lightcoral')
        self.tree.tag_configure('yellow', background='lightyellow')

        self.tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(task_frame)
        button_frame.pack(pady=10)

        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_tasks, style="TButton")
        refresh_button.grid(row=0, column=0, padx=10)

        ttk.Label(button_frame, text="Enter PID to terminate:").grid(row=0, column=1, padx=5)
        self.pid_entry = ttk.Entry(button_frame, width=10)
        self.pid_entry.grid(row=0, column=2, padx=5)

        kill_button = ttk.Button(button_frame, text="End Task", command=self.kill_process, style="TButton")
        kill_button.grid(row=0, column=3, padx=10)

        # Initial load of tasks
        self.refresh_tasks()

    def sort_column(self, col):
        data = [(self.tree.item(child)['values'], child) for child in self.tree.get_children()]

        # Decide the sort direction
        if self.sort_states[col] is None or self.sort_states[col] == 'default':
            # Sort ascending
            data.sort(key=lambda x: x[0][self.tree.cget('columns').index(col)])
            self.sort_states[col] = 'ascending'
        elif self.sort_states[col] == 'ascending':
            # Sort descending
            data.sort(key=lambda x: x[0][self.tree.cget('columns').index(col)], reverse=True)
            self.sort_states[col] = 'descending'
        else:
            # Return to default -> refresh entire list
            self.refresh_tasks()
            self.sort_states[col] = 'default'
            return

        for index, (_, child) in enumerate(data):
            self.tree.move(child, '', index)

    def refresh_tasks(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Re-populate
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username', 'cwd', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                name = proc.info['name'] or "N/A"
                pid = proc.info['pid']
                exe_path = proc.info['exe'] or "N/A"
                user = proc.info['username'] or "N/A"
                cwd = proc.info['cwd'] or "N/A"
                cmd_args = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else "N/A"
                cpu = f"{proc.info['cpu_percent']}%"
                mem_value = proc.info['memory_percent'] if proc.info['memory_percent'] else 0
                memory = f"{mem_value:.2f}%"
                open_files = len(proc.open_files()) if proc.open_files() else 0
                connections = len(proc.connections()) if proc.connections() else 0

                signed_status = self.is_signed(exe_path) if exe_path != "N/A" else "N/A"
                publisher = self.get_publisher(exe_path) if exe_path != "N/A" else "N/A"

                # Default tag = '' so it uses the normal background
                tag = ''
                # Then colorize only if conditions match
                if self.is_malleable_process(name):
                    tag = 'yellow'
                elif signed_status == "Yes":
                    tag = 'green'
                elif signed_status == "No":
                    tag = 'red'

                self.tree.insert(
                    "",
                    tk.END,
                    values=(name, pid, exe_path, user, cwd, cmd_args, open_files, cpu, memory,
                            connections, signed_status, publisher),
                    tags=(tag,)
                )

            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    def get_process_path(self, pid):
        try:
            process = psutil.Process(pid)
            return process.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_publisher(self, file_path):
        try:
            result = subprocess.run(['sigcheck', '-q', '-nobanner', file_path], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "Publisher" in line:
                    return line.split(':', 1)[1].strip() or "Unknown"
            return "Unknown"
        except FileNotFoundError:
            print("Error: 'sigcheck' not found. Ensure it's installed and in your PATH.")
            return "Error"
        except Exception as e:
            print(f"Error retrieving publisher for {file_path}: {e}")
            return "Error"

    def is_signed(self, file_path):
        try:
            result = subprocess.run(['sigcheck', '-q', file_path], capture_output=True, text=True)
            if "Signed" in result.stdout:
                return "Yes"
            elif "Unsigned" in result.stdout:
                return "No"
            else:
                return "Unknown"
        except FileNotFoundError:
            print("Error: 'sigcheck' not found. Ensure it's installed and in your PATH.")
            return "Error"
        except Exception as e:
            print(f"Error checking signature for {file_path}: {e}")
            return "Error"

    def is_malleable_process(self, process_name):
        malleable_processes = [
            "cmd.exe", "powershell.exe", "python.exe", "pythonw.exe", "wscript.exe", "cscript.exe",
            "mshta.exe", "rundll32.exe", "java.exe", "regsvr32.exe", "schtasks.exe", "wmic.exe",
            "certutil.exe", "powershell_ise.exe", "scrcons.exe", "gcc", "cl.exe", "dllhost.exe"
        ]
        return process_name.lower() in malleable_processes

    def kill_process(self):
        pid = self.pid_entry.get()
        if pid.isdigit():
            try:
                os.kill(int(pid), 9)
                messagebox.showinfo("Success", f"Process with PID {pid} terminated.")
                self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to terminate process: {e}")
        else:
            messagebox.showwarning("Warning", "Please enter a valid PID.")

    def resource_monitor_tab(self):
        resource_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(resource_frame, text="Resource Monitor")

        ttk.Label(resource_frame, text="System Resource Usage", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.add_green_resource_bar(resource_frame, "CPU Usage", "cpu")
        self.add_green_resource_bar(resource_frame, "Memory Usage", "memory")
        self.add_green_resource_bar(resource_frame, "Disk Usage", "disk")

        threading.Thread(target=self.update_resources, daemon=True).start()

    def add_green_resource_bar(self, parent, label_text, resource_type):
        label = ttk.Label(parent, text=f"{label_text}: 0%", font=("Helvetica", 12))
        label.pack(pady=5)

        canvas_frame = tk.Frame(parent)
        canvas_frame.pack(pady=5)

        canvas = tk.Canvas(canvas_frame, width=400, height=30, bg="white", highlightthickness=1, highlightbackground="#d9d9d9")
        canvas.pack()

        bar = canvas.create_rectangle(0, 0, 0, 30, fill="#00cc44")
        setattr(self, f"{resource_type}_label", label)
        setattr(self, f"{resource_type}_bar", bar)
        setattr(self, f"{resource_type}_canvas", canvas)

    def update_resources(self):
        while True:
            self.update_green_bar("cpu", psutil.cpu_percent())
            self.update_green_bar("memory", psutil.virtual_memory().percent)
            self.update_green_bar("disk", psutil.disk_usage('/').percent)
            time.sleep(1)

    def update_green_bar(self, resource_type, usage):
        label = getattr(self, f"{resource_type}_label")
        bar = getattr(self, f"{resource_type}_bar")
        canvas = getattr(self, f"{resource_type}_canvas")

        canvas_width = 400
        fill_width = (usage / 100) * canvas_width
        canvas.coords(bar, 0, 0, fill_width, 30)

        label.config(text=f"{resource_type.capitalize()} Usage: {usage}%")

    def settings_tab(self):
        settings_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_frame, text="Settings")

        ttk.Label(settings_frame, text="Settings", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.add_toggle(settings_frame, "Enable Microphone", "mic")
        self.add_toggle(settings_frame, "Enable Camera", "cam")

    def add_toggle(self, parent, text, var_name):
        var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent,
            text=text,
            variable=var,
            command=lambda: self.toggle_feature(var_name, var)
        ).pack(pady=5)
        setattr(self, f"{var_name}_var", var)

    def toggle_feature(self, feature_name, var):
        status = "enabled" if var.get() else "disabled"
        messagebox.showinfo(f"{feature_name.capitalize()}", f"{feature_name.capitalize()} {status}.")

    # ---------------------------------------------------------------------
    #  APPLY DARK TEAL/BLUE COLOR SCHEME
    # ---------------------------------------------------------------------
    def set_styles(self):
        """
        Applies a dark teal/blue color scheme to the entire application,
        including frames, labels, buttons, entries, and treeviews.
        """

        # Define color constants
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
        style.theme_use("clam")

        # Main window background
        self.configure(bg=DARK_BLUE)

        # Title label
        self.title_label.configure(bg=TEAL_BLUE, fg=LIGHT_GRAY)

        # Notebook
        style.configure("TNotebook", background=FRAME_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=FRAME_BG, foreground=LIGHT_GRAY)
        style.map("TNotebook.Tab",
                  background=[("selected", TEAL_BLUE)],
                  foreground=[("selected", LIGHT_GRAY)])

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

        # Treeview
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
