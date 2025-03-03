import flet as ft
from flet import Colors, Blur, BlurTileMode, BoxShadow, ShadowBlurStyle, Offset
import os
import psutil
import datetime
import asyncio
import threading
import platform

# ---------------------------------------------------------------------------
# Helper Functions for Data
# ---------------------------------------------------------------------------
MAX_DEPTH = 50  # Prevent infinite recursion if there's a cycle

def get_ancestors_and_dead_parent(pid):
    """
    Returns a tuple: (list_of_living_ancestors, dead_ancestor_pid_or_None).

    - living_ancestors: PIDs of parents up the chain that still exist.
    - dead_ancestor_pid_or_None: the first parent PID we encountered that no longer exists,
      or None if we never hit a missing parent.
    
    Why only one dead ancestor? Because once a parent is missing,
    we can't climb further up to see that parent's parent.
    """
    living_ancestors = []
    dead_ancestor = None

    current_pid = pid
    while True:
        try:
            proc = psutil.Process(current_pid)
            parent = proc.parent()
            if not parent:
                # no more parents
                break
            living_ancestors.append(parent.pid)
            current_pid = parent.pid
        except psutil.NoSuchProcess:
            # This means the parent for current_pid is missing
            dead_ancestor = current_pid
            break
        except Exception:
            break

    return living_ancestors, dead_ancestor

def toggle_section(event, sub_column):
    """
    Toggles the visibility of a sub-column (ancestry or children).
    Changes the arrow from '▶' (collapsed) to '▼' (expanded).
    """
    arrow_container = event.control  # The Container that was clicked
    expanded = arrow_container.data["expanded"]
    arrow_text_obj = arrow_container.content  # The ft.Text inside the container

    if expanded:
        # Collapse
        arrow_text_obj.value = "▶"
        sub_column.visible = False
    else:
        # Expand
        arrow_text_obj.value = "▼"
        sub_column.visible = True

    arrow_container.data["expanded"] = not expanded
    event.page.update()

def build_progeny_node(pid, depth=0):
    """
    Builds a list of Flet controls for the children of `pid`, recursively,
    each behind a toggle arrow.
    """
    controls = []
    if depth >= MAX_DEPTH:
        controls.append(ft.Text(f"Max depth {MAX_DEPTH} reached...", color="red"))
        return controls

    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=False)

        for child in children:
            try:
                cproc = psutil.Process(child.pid)
                grandkids = cproc.children(recursive=False)

                # Arrow container
                arrow_symbol = "▶" if grandkids else "  "
                arrow_container = ft.Container(
                    data={"expanded": False},
                    content=ft.Text(arrow_symbol, color="white", size=12),
                    on_click=None,  # will set if grandkids exist
                )
                sub_column = ft.Column(visible=False)  # hidden by default

                # If this child has further children, set on_click to toggle
                if grandkids:
                    arrow_container.on_click = lambda e, sc=sub_column: toggle_section(e, sc)

                # Recursively build grandchildren
                sub_column.controls.extend(
                    build_progeny_node(child.pid, depth=depth+1)
                )

                row = ft.Row(
                    controls=[
                        arrow_container,
                        ft.Text(
                            f"{cproc.name()} (PID: {cproc.pid})",
                            color="white",
                            size=12
                        )
                    ],
                    spacing=5
                )
                controls.append(row)
                controls.append(sub_column)

            except psutil.NoSuchProcess:
                controls.append(ft.Text(f"Child PID {child.pid} no longer exists", color="red"))
            except Exception as e:
                controls.append(ft.Text(f"Error reading child PID {child.pid}: {e}", color="red"))

    except psutil.NoSuchProcess:
        controls.append(ft.Text(f"PID {pid} no longer exists.", color="red"))
    except Exception as e:
        controls.append(ft.Text(f"Error building progeny for PID {pid}: {e}", color="red"))

    return controls
def build_ancestry_list(pid):
    """
    Returns a list of ft.Text lines for the chain of parents from `pid` up to the root.
    """
    lines = []
    try:
        proc = psutil.Process(pid)
        ancestry = []
        while True:
            parent = proc.parent()
            if not parent:
                break
            ancestry.append(parent)
            proc = parent
        ancestry.reverse()  # root-most parent first

        indent = 0
        for p in ancestry:
            lines.append(
                ft.Text(
                    " " * indent + f"{p.name()} (PID: {p.pid})",
                    color="white",
                    size=12
                )
            )
            indent += 4
    except Exception as e:
        lines.append(ft.Text(f"Error building ancestry: {e}", color="red"))

    return lines
def create_full_tree_view(pid):
    """
    Shows a collapsible "Ancestry" arrow above the selected PID,
    the PID itself in the middle,
    and a collapsible "Progeny" arrow below for child processes (recursively).
    """
    # 1) Arrow + sub-column for ancestry
    ancestry_arrow = ft.Container(
        data={"expanded": False},
        content=ft.Text("▶", color="white", size=12),
        on_click=None
    )
    ancestry_subcol = ft.Column(visible=False)

    # Fill ancestry_subcol with lines about each parent
    ancestry_lines = build_ancestry_list(pid)
    ancestry_subcol.controls.extend(ancestry_lines)

    # If there's at least one parent, enable toggling
    if ancestry_lines:
        ancestry_arrow.on_click = lambda e, sc=ancestry_subcol: toggle_section(e, sc)
        ancestry_label = ft.Text("Ancestry", color="yellow", weight="bold")
    else:
        ancestry_arrow.content.value = "  "  # no arrow if no ancestry
        ancestry_label = ft.Text("No parents", color="gray")

    ancestry_row = ft.Row(
        controls=[
            ancestry_arrow,
            ancestry_label
        ],
        spacing=5
    )

    # 2) Show the selected PID in the middle
    try:
        proc = psutil.Process(pid)
        pid_label = ft.Text(
            f"Selected: {proc.name()} (PID: {pid})",
            color="cyan",
            size=12,
            weight="bold"
        )
    except Exception as e:
        pid_label = ft.Text(f"Error retrieving selected process: {e}", color="red")

    # 3) Arrow + sub-column for progeny
    progeny_arrow = ft.Container(
        data={"expanded": False},
        content=ft.Text("▶", color="white", size=12),
        on_click=None
    )
    progeny_subcol = ft.Column(visible=False)
    # Build child nodes (recursive toggles)
    child_nodes = build_progeny_node(pid, depth=0)
    progeny_subcol.controls.extend(child_nodes)

    # If there are any children, enable toggling
    if child_nodes:
        progeny_arrow.on_click = lambda e, sc=progeny_subcol: toggle_section(e, sc)
        progeny_label = ft.Text("Progeny", color="yellow", weight="bold")
    else:
        progeny_arrow.content.value = "  "  # no arrow
        progeny_label = ft.Text("No children", color="gray")

    progeny_row = ft.Row(
        controls=[
            progeny_arrow,
            progeny_label
        ],
        spacing=5
    )

    # Combine everything in a single Column
    return ft.Column(
        controls=[
            ancestry_row,
            ancestry_subcol,
            pid_label,
            progeny_row,
            progeny_subcol
        ],
        scroll="auto",
        spacing=5
    )

def build_process_node(pid, depth=0):
    """
    Returns a list of Flet controls representing this process + (lazy) children.
    Uses a dropdown arrow to expand/collapse children.
    """
    if depth >= MAX_DEPTH:
        return [ft.Text(f"Max depth {MAX_DEPTH} reached...", color="red")]

    controls = []
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=False)  # direct children only

        # If no children, show a blank arrow placeholder. Otherwise, show an arrow.
        arrow_symbol = "▶" if children else "  "
        arrow_container = ft.Container(
            data={"expanded": False},
            content=ft.Text(arrow_symbol, color="white", size=12),
            on_click=None,  # we'll set on_click only if children exist
        )
        # Sub-column for children, initially hidden
        sub_content = ft.Column(visible=False)

        # If the process has children, define the on_click toggler
        if children:
            arrow_container.on_click = lambda e, sc=sub_content: toggle_section(e, sc, e.page)

        # For each child, recursively build its node
        for child in children:
            sub_content.controls.extend(
                build_process_node(child.pid, depth=depth + 1)
            )

        # Main row: arrow + text for the process
        row = ft.Row(
            controls=[
                arrow_container,
                ft.Text(
                    f"{proc.name()} (PID: {pid})",
                    color="cyan" if depth == 0 else "white",
                    size=12,
                    weight="bold" if depth == 0 else None,
                ),
            ],
            spacing=5,
        )

        # Add row + sub_content to the controls
        controls.append(row)
        controls.append(sub_content)

    except psutil.NoSuchProcess:
        controls.append(ft.Text(f"PID {pid} no longer exists.", color="red"))
    except Exception as e:
        controls.append(ft.Text(f"Error building node for PID {pid}: {e}", color="red"))

    return controls



def get_process_history(pid):
    try:
        proc = psutil.Process(pid)
        create_time = datetime.datetime.fromtimestamp(proc.create_time())
        now = datetime.datetime.now()
        duration = now - create_time
        status = proc.status()
        return {
            "Start Time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Duration": str(duration).split(".")[0],
            "Status": status,
        }
    except Exception as e:
        return {"Error": str(e)}

def get_extra_insights(pid):
    try:
        proc = psutil.Process(pid)
        cmdline = " ".join(proc.cmdline()) if proc.cmdline() else "N/A"
        username = proc.username()
        status = proc.status()
        return {
            "Command Line": cmdline,
            "Username": username,
            "Status": status,
        }
    except Exception as e:
        return {"Error": str(e)}

def get_dll_usage(pid):
    system = platform.system()
    try:
        proc = psutil.Process(pid)
        if system == "Windows" and hasattr(proc, 'memory_maps'):
            modules = proc.memory_maps()
            dll_list = [m.path for m in modules if m.path and m.path.lower().endswith('.dll')]
            return dll_list[:10] if dll_list else ["No DLLs found"]
        elif system == "Linux":
            if hasattr(proc, 'memory_maps'):
                modules = proc.memory_maps()
                so_list = [m.path for m in modules if m.path and m.path.endswith('.so')]
                return so_list[:10] if so_list else ["No shared objects found"]
            return ["No memory_maps or insufficient permissions"]
        elif system == "Darwin":
            if hasattr(proc, 'open_files'):
                files = proc.open_files()
                dylibs = [f.path for f in files if f.path and f.path.endswith('.dylib')]
                return dylibs[:10] if dylibs else ["Limited library info; use 'lsof' externally"]
            return ["Library listing limited on macOS"]
        else:
            return [f"Library listing not supported on {system}"]
    except Exception as e:
        return [f"Error retrieving libraries: {str(e)}"]
def get_ancestry_pids(pid):
    pids = []
    try:
        proc = psutil.Process(pid)
        while True:
            parent = proc.parent()
            if not parent:
                break
            pids.append(parent.pid)
            proc = parent
    except:
        pass
    return pids

def get_progeny_pids(pid):
    pids = []
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=False)
        for child in children:
            pids.append(child.pid)
            pids.extend(get_progeny_pids(child.pid))
    except:
        pass
    return pids

def get_full_tree_pids(pid):
    all_pids = set([pid])
    all_pids.update(get_ancestry_pids(pid))
    all_pids.update(get_progeny_pids(pid))
    return all_pids

def get_resource_metrics(pid):
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

def get_tree_resource_rows(pid):
    all_tree_pids = sorted(get_full_tree_pids(pid))
    rows = []
    for p in all_tree_pids:
        try:
            proc = psutil.Process(p)
            usage = get_resource_metrics(p)
            if "Error" in usage:
                row = [str(p), proc.name(), usage["Error"], "", "", "", "", ""]
            else:
                row = [
                    str(p),
                    proc.name(),
                    usage["CPU Usage (%)"],
                    usage["Memory Usage (MB)"],
                    usage["Network In (MB)"],
                    usage["Network Out (MB)"],
                    usage["Children Count"],
                    usage["Niceness"],
                ]
            rows.append(row)
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            rows.append([str(p), f"Error: {e}", "", "", "", "", "", ""])
    return rows

def get_detailed_process_info():
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            info = proc.info
            pid = info['pid']
            name = info['name']
            start_time = datetime.datetime.fromtimestamp(info['create_time']).strftime("%H:%M:%S")
            duration = "N/A"
            process_list.append([str(pid), name, start_time, duration])
        except:
            continue
    return process_list

def get_top_cpu_processes(count=5):
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu = proc.cpu_percent(interval=0)
            processes.append((proc.info['pid'], proc.info['name'], cpu))
        except:
            pass
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes[:count]

def build_ancestry_tree(pid):
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
        ancestry.reverse()
        indent = 0
        for p in ancestry:
            widgets.append(ft.Text(" " * indent + f"{p.name()} (PID: {p.pid})", color="white"))
            indent += 4
    except Exception as e:
        widgets.append(ft.Text(f"Error building ancestry: {e}", color="red"))
    return widgets

def build_progeny_tree(pid, indent=4):
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
        scroll="auto",
        spacing=2
    )


# -----------------------------------------------------------------------------
# 3. DASHBOARD CLASS
# -----------------------------------------------------------------------------
class ProcessMonitorDashboard:
    def __init__(self, glass_bgcolor, container_blur, container_shadow):
        self.glass_bgcolor = glass_bgcolor
        self.container_blur = container_blur
        self.container_shadow = container_shadow

        self.pid_text_field = None
        self.tree_view_container = None
        self.tree_resource_table = None
        self.detailed_table = None
        self.top_cpu_table = None

        self.layout = self.create_layout()

    def create_layout(self):
        default_pid = os.getpid()

        # ---------- TOP-LEFT: TREE VIEW ----------
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
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
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

        # ---------- TOP-RIGHT: RESOURCE ANALYSIS (TREE) ----------
        self.tree_resource_table = ft.DataTable(
    columns=[
        ft.DataColumn(
            label=ft.Container(
                width=50,
                content=ft.Text("PID", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=140,
                content=ft.Text("Name", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=65,
                content=ft.Text("CPU (%)", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=85,
                content=ft.Text("Mem (MB)", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=90,
                content=ft.Text("Net In (MB)", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=90,
                content=ft.Text("Net Out (MB)", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=70,
                content=ft.Text("Children", color="white", size=12)
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                width=70,
                content=ft.Text("Niceness", color="white", size=12)
            )
        ),
    ],
    rows=[],
    border=ft.border.all(0, "transparent"),
    horizontal_lines=ft.border.BorderSide(1, "#363636"),
    heading_row_color=Colors.with_opacity(0.1, "white"),
    heading_row_height=40,
    data_row_min_height=35,
    data_row_max_height=50,
    column_spacing=8,
)
        resource_table_wrapper = ft.Container(
            content=ft.Row(
                controls=[self.tree_resource_table],
                scroll="auto",  # horizontal scroll if needed
            ),
            expand=True,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            border_radius=6,
            padding=10,
        )
        resource_analysis_column = ft.Column(
            controls=[
                ft.Text("Resource Analysis (Tree)", size=18, weight=ft.FontWeight.BOLD, color="white"),
                resource_table_wrapper,
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
        detailed_table_container = ft.Container(
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            border_radius=6,
            padding=10,
            expand=True,
            content=ft.Column(
                [self.detailed_table],
                scroll="auto",
                expand=True
            )
        )
        detailed_process_info_column = ft.Column(
            controls=[
                ft.Text("Detailed Process Info", size=18, weight=ft.FontWeight.BOLD, color="white"),
                detailed_table_container
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

       
        # -------------- Bottom-right: TABBED PANELS (History, Insights, DLL) --------------
        self.history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Metric", color="white", size=12)),
                ft.DataColumn(ft.Text("Value", color="white", size=12))
            ],
            rows=[]
        )
        history_container = ft.Container(
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            border_radius=6,
            padding=10,
            expand=True,
            content=self.history_table
        )
        history_tab = ft.Tab(text="History", content=history_container)

        self.insights_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Metric", color="white", size=12)),
                ft.DataColumn(ft.Text("Value", color="white", size=12))
            ],
            rows=[]
        )
        insights_container = ft.Container(
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            border_radius=6,
            padding=10,
            expand=True,
            content=self.insights_table
        )
        insights_tab = ft.Tab(text="Insights", content=insights_container)

        self.dll_list = ft.Column(controls=[], scroll="auto")
        dll_container = ft.Container(
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            border_radius=6,
            padding=10,
            expand=True,
            content=self.dll_list
        )
        dll_tab = ft.Tab(text="DLL Usage", content=dll_container)

        tabs = ft.Tabs(tabs=[history_tab, insights_tab, dll_tab], expand=True)
        bottom_right_column = ft.Column(
            controls=[
                ft.Text("Process Details", size=18, weight=ft.FontWeight.BOLD, color="white"),
                tabs
            ],
            spacing=10,
            expand=True
        )
        bottom_right_container = ft.Container(
            content=bottom_right_column,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=10,
            expand=1
        )

        # Combine bottom-left and bottom-right
        bottom_row = ft.Row(
            controls=[bottom_left_container, bottom_right_container],
            spacing=10,
            expand=1
        )

        # Finally, combine top row and bottom row
        final_layout = ft.Column(
            controls=[top_row, bottom_row],
            spacing=10,
            expand=True
        )
        return final_layout

    def update_ui(self, page):
        # Read PID
        try:
            pid = int(self.pid_text_field.value)
        except ValueError:
            pid = os.getpid()

        # Update tree view
        self.tree_view_container.content = create_full_tree_view(pid)    # Update resource usage table
        tree_rows = get_tree_resource_rows(pid)
        self.tree_resource_table.rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
            )
            for row in tree_rows
        ]

        # Update detailed process info
        process_data = get_detailed_process_info()
        self.detailed_table.rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell), color="white", size=12)) for cell in row]
            )
            for row in process_data
        ]

        # -------------- New Tab Panels --------------
        # 1) History
        history_data = get_process_history(pid)
        self.history_table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(k), color="white", size=12)),
                    ft.DataCell(ft.Text(str(v), color="white", size=12))
                ]
            )
            for k, v in history_data.items()
        ]

        # 2) Insights
        insights_data = get_extra_insights(pid)
        self.insights_table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(k), color="white", size=12)),
                    ft.DataCell(ft.Text(str(v), color="white", size=12))
                ]
            )
            for k, v in insights_data.items()
        ]

        # 3) DLL usage
        dll_data = get_dll_usage(pid)
        self.dll_list.controls = [ft.Text(lib_path, color="white", size=12) for lib_path in dll_data]

        # 1) Gather living ancestors + first dead ancestor
        living_ancestors, dead_ancestor = get_ancestors_and_dead_parent(pid)

        # 2) Build a list/dict for the "Process Details" tab
        #    For example, if you have a "History" or "Insights" table:
        details_data = {
            "Living Ancestors": ", ".join(str(p) for p in living_ancestors) if living_ancestors else "None",
            "Dead Ancestor": str(dead_ancestor) if dead_ancestor else "None",
        }

        # 3) Insert those details into whichever table or tab you prefer
        #    Suppose you have self.insights_table with columns ["Metric", "Value"]:
        #    We'll just add them as extra rows:
        existing_rows = []
        # If you already have some rows for Insights, store them:
        # existing_rows = self.insights_table.rows

        new_rows = []
        for k, v in details_data.items():
            new_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(k), color="white", size=12)),
                        ft.DataCell(ft.Text(str(v), color="white", size=12))
                    ]
                )
            )
        self.insights_table.rows = existing_rows + new_rows


        page.update()

    def timer_update(self, e):
        self.update_ui(e.page)

    def pid_changed(self, e):
        self.update_ui(e.page)


# -----------------------------------------------------------------------------
# 4. PERIODIC UPDATING
# -----------------------------------------------------------------------------
async def periodic_update(page, process_monitor):
    while True:
        process_monitor.update_ui(page)
        await asyncio.sleep(2)

def start_proc_chain_updates(page, dashboard):
    new_loop = asyncio.new_event_loop()
    new_loop.create_task(periodic_update(page, dashboard))
    threading.Thread(target=_run_loop, args=(new_loop,), daemon=True).start()

def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# -----------------------------------------------------------------------------
# 5. EXPOSED FUNCTION + MAIN
# -----------------------------------------------------------------------------
def create_process_chains_layout(glass_bgcolor, container_blur, container_shadow):
    """
    Returns (layout, dashboard_instance).
    """
    dashboard = ProcessMonitorDashboard(glass_bgcolor, container_blur, container_shadow)
    return dashboard.layout, dashboard

