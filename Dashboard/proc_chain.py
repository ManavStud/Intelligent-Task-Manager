import flet as ft
from flet import Colors
import os
import psutil
import datetime
import asyncio
import threading

# -----------------------------------------------------------------------------
# Helper Functions for Process Data
# -----------------------------------------------------------------------------
def get_resource_metrics(pid):
    """
    Given a PID, returns a dict of resource metrics for the process.
    """
    try:
        proc = psutil.Process(pid)
        cpu_usage = proc.cpu_percent(interval=0.1)
        mem_usage = proc.memory_info().rss / (1024 ** 2)  # in MB
        children_count = len(proc.children())
        niceness = proc.nice()
        net = psutil.net_io_counters()
        net_in = net.bytes_recv / (1024 ** 2)
        net_out = net.bytes_sent / (1024 ** 2)
        return {
            "CPU Usage (%)": f"{cpu_usage:.1f}",
            "Memory Usage (MB)": f"{mem_usage:.1f}",
            "Network In (MB)": f"{net_in:.1f}",
            "Network Out (MB)": f"{net_out:.1f}",
            "Children Count": str(children_count),
            "Niceness": str(niceness),
        }
    except Exception as e:
        return {"Error": str(e)}

def get_detailed_process_info():
    """
    Returns a list of process rows for a "Detailed Process Info" table.
    Each row: [PID, Process Name, Start Timestamp, Duration].
    (Duration is a placeholder.)
    """
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            info = proc.info
            pid = info['pid']
            name = info['name']
            start_time = datetime.datetime.fromtimestamp(info['create_time']).strftime("%H:%M:%S")
            duration = "N/A"
            process_list.append([str(pid), name, start_time, duration])
        except Exception:
            continue
    return process_list

def get_top_cpu_processes(count=5):
    """
    Returns a list of (pid, name, cpu_usage) for the top CPU-consuming processes.
    This is a snapshot in time and may vary if the system is busy.
    """
    # The first call to proc.cpu_percent() sets up measurement,
    # so calling it again after a short interval is more accurate.
    # For a quick snapshot, we'll do a single pass here.
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu = proc.cpu_percent(interval=0)  # 0 means no blocking, just last measurement
            processes.append((proc.info['pid'], proc.info['name'], cpu))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Sort by CPU usage descending
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes[:count]

# -----------------------------------------------------------------------------
# Helper Functions for Tree View
# -----------------------------------------------------------------------------
def build_ancestry_tree(pid):
    """Builds a list of flet.Text widgets showing parent processes up to the root."""
    widgets = []
    try:
        proc = psutil.Process(pid)
        ancestry = []
        while True:
            parent = proc.parent()
            if not parent:
                break
            ancestry.append(parent)
            proc = parent
        ancestry.reverse()  # root first
        indent = 0
        for p in ancestry:
            widgets.append(ft.Text(" " * indent + f"{p.name()} (PID: {p.pid})", color="white"))
            indent += 4
    except Exception as e:
        widgets.append(ft.Text(f"Error building ancestry: {e}", color="red"))
    return widgets

def build_progeny_tree(pid, indent=4):
    """Builds a list of flet.Text widgets showing child processes recursively."""
    widgets = []
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=False)
        for child in children:
            widgets.append(ft.Text(" " * indent + f"{child.name()} (PID: {child.pid})", color="white"))
            widgets.extend(build_progeny_tree(child.pid, indent + 4))
    except Exception as e:
        widgets.append(ft.Text(f"Error building progeny: {e}", color="red"))
    return widgets

def create_complete_tree_view(pid):
    """
    Returns a Column with ancestry, selected process line, and progeny.
    """
    ancestry_widgets = [ft.Text("Ancestry:", weight="bold", color="yellow")]
    ancestry_widgets.extend(build_ancestry_tree(pid))
    try:
        proc = psutil.Process(pid)
        current_line = ft.Text(f"Selected: {proc.name()} (PID: {proc.pid})", weight="bold", color="cyan")
    except Exception as e:
        current_line = ft.Text(f"Error retrieving selected process: {e}", color="red")
    progeny_widgets = [ft.Text("Progeny:", weight="bold", color="yellow")]
    progeny_widgets.extend(build_progeny_tree(pid))
    return ft.Column(
        controls=ancestry_widgets + [current_line] + progeny_widgets,
        scroll="auto"
    )

# -----------------------------------------------------------------------------
# ProcessMonitorDashboard
# -----------------------------------------------------------------------------
class ProcessMonitorDashboard:
    def __init__(self, glass_bgcolor, container_blur, container_shadow):
        self.glass_bgcolor = glass_bgcolor
        self.container_blur = container_blur
        self.container_shadow = container_shadow

        # Widget references
        self.pid_text_field = None
        self.tree_view_container = None
        self.resource_table = None
        self.detailed_table = None
        # This replaces the alerts panel with a "Top CPU Processes" table
        self.top_cpu_table = None

        self.layout = self.create_layout()

    def create_layout(self):
        default_pid = os.getpid()
        
        # ---------- TOP-LEFT: PROCESS TREE VIEW ----------
        self.pid_text_field = ft.TextField(
            label="PID",
            label_style=ft.TextStyle(color="white"),
            hint_text="Enter PID",
            value=str(default_pid),
            bgcolor="#273845",
            color="white",
            border_color="white",
            width=250,
            on_submit=self.pid_changed
        )
        self.tree_view_container = ft.Container(
            bgcolor="#2B3B47",
            border_radius=6,
            padding=10,
            expand=True,
            content=create_complete_tree_view(default_pid)
        )
        tree_view_column = ft.Column(
            controls=[
                ft.Text("Process Tree View", size=18, weight=ft.FontWeight.BOLD, color="white"),
                self.pid_text_field,
                self.tree_view_container,
            ],
            spacing=10,
            expand=True
        )
        top_left_container = ft.Container(
            content=tree_view_column,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=10,
            expand=1
        )
        
        # ---------- TOP-RIGHT: RESOURCE ANALYSIS ----------
        resource_metrics = get_resource_metrics(default_pid)
        resource_columns = ["Resource Metric", "Value"]
        resource_data = [[k, v] for k, v in resource_metrics.items()]
        self.resource_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, color="white", size=12)) for col in resource_columns],
            rows=[
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
                )
                for row in resource_data
            ],
            border=ft.border.all(0, "transparent"),
            horizontal_lines=ft.border.BorderSide(1, "#363636"),
            heading_row_color=Colors.with_opacity(0.1, "white"),
            heading_row_height=40,
            data_row_min_height=35,
            data_row_max_height=50,
            column_spacing=20,
        )
        resource_analysis_column = ft.Column(
            controls=[
                ft.Text("Resource Analysis", size=18, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    bgcolor="#2B3B47",
                    border_radius=6,
                    padding=10,
                    expand=True,
                    content=self.resource_table
                )
            ],
            spacing=10,
            expand=True
        )
        top_right_container = ft.Container(
            content=resource_analysis_column,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=10,
            expand=1
        )

        # Combine top-left and top-right in one row
        top_row = ft.Row(
            controls=[top_left_container, top_right_container],
            spacing=10,
            expand=1
        )
        
        # ---------- BOTTOM-LEFT: DETAILED PROCESS INFO ----------
        process_columns = ["PID", "Process Name", "Start Timestamp", "Duration"]
        process_data = get_detailed_process_info()
        self.detailed_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, color="white", size=12)) for col in process_columns],
            rows=[
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
                )
                for row in process_data
            ],
            border=ft.border.all(0, "transparent"),
            horizontal_lines=ft.border.BorderSide(1, "#363636"),
            heading_row_color=Colors.with_opacity(0.1, "white"),
            heading_row_height=40,
            data_row_min_height=35,
            data_row_max_height=50,
            column_spacing=20,
        )
        detailed_process_info_column = ft.Column(
            controls=[
                ft.Text("Detailed Process Info", size=18, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    bgcolor="#2B3B47",
                    border_radius=6,
                    padding=10,
                    expand=True,
                    content=self.detailed_table
                )
            ],
            spacing=10,
            expand=True
        )
        bottom_left_container = ft.Container(
            content=detailed_process_info_column,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=10,
            expand=1
        )
        
        # ---------- BOTTOM-RIGHT: TOP CPU PROCESSES ----------
        # We'll show a table of top CPU-consuming processes.
        self.top_cpu_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("PID", color="white", size=12)),
                ft.DataColumn(ft.Text("Name", color="white", size=12)),
                ft.DataColumn(ft.Text("CPU (%)", color="white", size=12)),
            ],
            rows=[],
            border=ft.border.all(0, "transparent"),
            horizontal_lines=ft.border.BorderSide(1, "#363636"),
            heading_row_color=Colors.with_opacity(0.1, "white"),
            heading_row_height=40,
            data_row_min_height=35,
            data_row_max_height=50,
            column_spacing=20,
        )
        top_cpu_column = ft.Column(
            controls=[
                ft.Text("Top CPU Processes", size=18, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    bgcolor="#2B3B47",
                    border_radius=6,
                    padding=10,
                    expand=True,
                    content=self.top_cpu_table
                )
            ],
            spacing=10,
            expand=True
        )
        bottom_right_container = ft.Container(
            content=top_cpu_column,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=10,
            expand=1
        )

        # Combine bottom-left and bottom-right in one row
        bottom_row = ft.Row(
            controls=[bottom_left_container, bottom_right_container],
            spacing=10,
            expand=1
        )

        # ---------- Final 2×2 Layout ----------
        final_layout = ft.Column(
            controls=[top_row, bottom_row],
            spacing=10,
            expand=True
        )
        return final_layout

    def update_ui(self, page):
        # Read PID or default to current
        try:
            pid = int(self.pid_text_field.value)
        except ValueError:
            pid = os.getpid()
        
        # Update the tree view
        self.tree_view_container.content = create_complete_tree_view(pid)
        
        # Update resource metrics
        resource_metrics = get_resource_metrics(pid)
        resource_data = [[k, v] for k, v in resource_metrics.items()]
        self.resource_table.rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
            )
            for row in resource_data
        ]
        
        # Update detailed process info
        process_data = get_detailed_process_info()
        self.detailed_table.rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
            )
            for row in process_data
        ]
        
        # Update the top CPU processes table
        top_cpu = get_top_cpu_processes(count=5)
        self.top_cpu_table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(pid), color="white", size=12)),
                    ft.DataCell(ft.Text(str(name), color="white", size=12)),
                    ft.DataCell(ft.Text(f"{cpu:.1f}", color="white", size=12))
                ]
            )
            for (pid, name, cpu) in top_cpu
        ]
        
        page.update()

    def timer_update(self, e):
        self.update_ui(e.page)

    def pid_changed(self, e):
        self.update_ui(e.page)

# -----------------------------------------------------------------------------
# Asynchronous Periodic Update (to be started by your main dashboard)
# -----------------------------------------------------------------------------
async def periodic_update(page, process_monitor):
    while True:
        process_monitor.update_ui(page)
        await asyncio.sleep(2)

# -----------------------------------------------------------------------------
# Function to Start Periodic Updates
# -----------------------------------------------------------------------------
def start_proc_chain_updates(page, dashboard):
    new_loop = asyncio.new_event_loop()
    new_loop.create_task(periodic_update(page, dashboard))
    threading.Thread(target=_run_loop, args=(new_loop,), daemon=True).start()

def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# -----------------------------------------------------------------------------
# Exposed Function to Create the Layout and Dashboard Instance
# -----------------------------------------------------------------------------
def create_process_chains_layout(glass_bgcolor, container_blur, container_shadow):
    """
    Returns a tuple: (dashboard_layout, dashboard_instance).
    Import and add the layout to your page, then call
    start_proc_chain_updates(page, dashboard_instance) for periodic updates.
    """
    dashboard = ProcessMonitorDashboard(glass_bgcolor, container_blur, container_shadow)
    return dashboard.layout, dashboard