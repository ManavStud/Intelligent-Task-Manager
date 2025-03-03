import flet as ft
from flet import Colors, BoxShadow, Offset
import psutil
import time
import threading
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(
    filename='process_monitor.log',  # Log file name
    level=logging.DEBUG,             # Log all messages
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Regex pattern for process name or PID filtering
process_pattern = re.compile(r'(\w+|\d+)')

def create_process_monitoring_layout(glass_bgcolor, container_blur, container_shadow):
    """
    Build and return:
      1) The main process monitoring layout (tabs, logs, etc.).
      2) An init_process_monitor function you call once after adding the layout to your page.

    Usage in your main dashboard:
        layout, init_proc = create_process_monitoring_layout(glass_bgcolor, container_blur, container_shadow)
        page.add(layout)
        init_proc(page)
    """

    # References for updating tables and status text
    running_processes_table_ref = ft.Ref[ft.Container]()
    critical_alerts_table_ref = ft.Ref[ft.Container]()
    process_logs_table_ref = ft.Ref[ft.Container]()
    status_text_ref = ft.Ref[ft.Text]()

    # Data storage for processes, logs, and critical alerts
    processes = {}        # Active processes
    process_logs = []     # Log rows for all processes (6 columns)
    critical_alerts = []  # Critical alerts (4 columns)

    ############################################################################
    # Functions to fetch and update process data
    ############################################################################
    def get_process_data():
        """Fetch live process data using psutil and generate critical alerts."""
        try:
            logger.info("Fetching process data...")
            current_processes = {}
            processes_data = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status'])
            current_time = datetime.now()

            for proc in processes_data:
                try:
                    pid = proc.info['pid']
                    # Skip system processes that cause resource metric errors
                    if pid in (0, 1):
                        continue

                    process_name = proc.info['name'] if proc.info['name'] else "Unknown"
                    # Coerce None to 0.0
                    cpu_usage = proc.info['cpu_percent'] or 0.0
                    memory_usage = proc.info['memory_percent'] or 0.0
                    status = proc.info['status'] if proc.info['status'] else "Running"

                    current_processes[pid] = {
                        'pid': pid,
                        'name': process_name,
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory_usage,
                        'status': status,
                        'started_at': current_time,
                        'security_check': "Safe"
                    }

                    # Detect new processes
                    if pid not in processes:
                        logger.info(f"New process detected: {process_name} (PID: {pid})")
                        processes[pid] = current_processes[pid]
                        log_row = [
                            process_name,
                            str(pid),
                            f"{cpu_usage:.2f}%",
                            f"{memory_usage:.2f}%",
                            status,
                            current_time.strftime("%Y-%m-%d %H:%M:%S")
                        ]
                        process_logs.append(log_row)

                        # Generate a critical alert if usage is very high
                        if cpu_usage > 80 or memory_usage > 80:
                            alert = [
                                process_name,
                                str(pid),
                                f"High Usage: CPU {cpu_usage:.2f}%, Memory {memory_usage:.2f}%",
                                current_time.strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            critical_alerts.append(alert)

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.warning(f"Error processing process: {str(e)} with PID {pid if 'pid' in locals() else 'N/A'}")
                    continue

            # Detect terminated processes
            for pid in list(processes.keys()):
                if pid not in current_processes:
                    logger.info(f"Process terminated: {processes[pid]['name']} (PID: {pid})")
                    terminated_at = datetime.now()
                    log_row = [
                        processes[pid]['name'],
                        str(pid),
                        f"{processes[pid]['cpu_usage']:.2f}%",
                        f"{processes[pid]['memory_usage']:.2f}%",
                        "Terminated",
                        terminated_at.strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    process_logs.append(log_row)
                    alert = [
                        processes[pid]['name'],
                        str(pid),
                        "Process Terminated",
                        terminated_at.strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    critical_alerts.append(alert)
                    del processes[pid]

            # Keep only the last 50 log and alert entries
            process_logs[:] = process_logs[-50:]
            critical_alerts[:] = critical_alerts[-50:]

            running_processes = [
                [
                    proc['name'],
                    f"{proc['cpu_usage']}%",
                    f"{proc['memory_usage']}%",
                    proc['status'],
                    proc['security_check']
                ] for proc in current_processes.values()
            ]

            status = f"Monitoring {len(running_processes)} active processes | {len(critical_alerts)} critical alerts"
            logger.info(status)
            return running_processes, critical_alerts, status

        except Exception as e:
            logger.error(f"Error fetching process data: {str(e)}")
            return [], [], f"Error fetching process data: {str(e)}"

    def update_process_data(page: ft.Page):
        """Update process tables with live data, critical alerts, and logs."""
        logger.info("Updating process data in UI...")
        running_data, alerts_data, status = get_process_data()
        
        # Update status text
        if status_text_ref.current:
            status_text_ref.current.value = status
        
        # Update Running Processes table
        if running_processes_table_ref.current:
            table = running_processes_table_ref.current.content.controls[0]
            table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(
                                    message=str(cell), 
                                    bgcolor="#08CDFF", 
                                    text_style=ft.TextStyle(color="white"), 
                                    padding=5
                                ),
                            )
                        ) for cell in row
                    ]
                ) for row in running_data
            ]

        # Update Critical Alerts table
        if critical_alerts_table_ref.current:
            table = critical_alerts_table_ref.current.content.controls[0]
            table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(
                                    message=str(cell), 
                                    bgcolor="#08CDFF", 
                                    text_style=ft.TextStyle(color="white"), 
                                    padding=5
                                ),
                            )
                        ) for cell in row
                    ]
                ) for row in alerts_data
            ]

        # Update "Process Logs" table (6 columns)
        if process_logs_table_ref.current:
            table = process_logs_table_ref.current.content.controls[0]
            table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(
                                    message=str(cell), 
                                    bgcolor="#08CDFF", 
                                    text_style=ft.TextStyle(color="white"), 
                                    padding=5
                                ),
                            )
                        ) for cell in row
                    ]
                ) for row in process_logs
            ]

        page.update()

    def start_updates(page: ft.Page):
        """Background thread that periodically updates process data."""
        def update_loop():
            logger.info("Starting process data update loop...")
            while True:
                try:
                    update_process_data(page)
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Error in update loop: {str(e)}")
                    time.sleep(5)  # Wait before retrying
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()

    ############################################################################
    # UI Builders
    ############################################################################
    def create_process_table(columns, table_ref=None):
        # Basic DataTable with references
        table = ft.Container(
            content=ft.Column(
                [
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(
                                ft.Container(
                                    content=ft.Text(
                                        col,
                                        color="white",
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=2,
                                        text_align=ft.TextAlign.LEFT,
                                    ),
                                    width=85 if col == "Process Name" else \
                                          70 if col in ["CPU Usage", "Memory Usage", "Alert Description"] else \
                                          55,
                                    tooltip=ft.Tooltip(
                                        message=col,
                                        bgcolor="#08CDFF",
                                        text_style=ft.TextStyle(color="white"),
                                        padding=5,
                                    ),
                                ),
                                numeric=False,
                            ) for col in columns
                        ],
                        rows=[],
                        border=ft.border.all(0, "transparent"),
                        horizontal_lines=ft.border.BorderSide(1, "#363636"),
                        heading_row_color=Colors.with_opacity(0.1, "white"),
                        heading_row_height=45,
                        data_row_min_height=30,
                        data_row_max_height=40,
                        column_spacing=8,
                    )
                ],
                scroll="auto",
                spacing=0,
            ),
            ref=table_ref,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            padding=5,
        )
        return table

    def create_search_filter_bar(title, table_ref, log_type):
        def filter_table(e):
            search_text = e.control.value.strip().lower()
            if not search_text:
                reset_table()
                return
            table = table_ref.current.content.controls[0] if table_ref.current else None
            if not table:
                return
            for row in table.rows:
                combined_text = " ".join(str(cell.content.content.value) for cell in row.cells).lower()
                row.visible = search_text in combined_text
            table.update()

        def reset_table():
            table = table_ref.current.content.controls[0] if table_ref.current else None
            if table:
                for row in table.rows:
                    row.visible = True
                table.update()

        def update_filter_hint(e, search_field):
            filter_type = e.control.value
            hints = {
                "Process Name": f"Search {log_type} by Process Name...",
                "PID": f"Search {log_type} by PID...",
                "CPU Usage": f"Search {log_type} by CPU Usage (e.g., '>50%')...",
                "Memory Usage": f"Search {log_type} by Memory Usage (e.g., '>10%')...",
                "Status": f"Search {log_type} by Status...",
                "Alert Description": f"Search {log_type} by Alert Description..."
            }
            search_field.hint_text = hints[filter_type]
            search_field.update()

        search_field = ft.TextField(
            border=ft.InputBorder.NONE,
            height=35,
            text_size=12,
            bgcolor='transparent',
            color='white',
            hint_text=f"Search {title}...",
            hint_style=ft.TextStyle(color='#6c757d'),
            expand=True,
            content_padding=ft.padding.only(left=8, right=8),
            on_submit=filter_table
        )
        
        filter_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Process Name"),
                ft.dropdown.Option("PID"),
                ft.dropdown.Option("CPU Usage"),
                ft.dropdown.Option("Memory Usage"),
                ft.dropdown.Option("Status"),
                ft.dropdown.Option("Alert Description"),  # For Critical Alerts
            ],
            value="Process Name",
            width=120,
            bgcolor='transparent',
            color='white',
            border_color="#03DAC6",
            on_change=lambda e: update_filter_hint(e, search_field)
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH, color='#6c757d', size=16),
                                search_field
                            ],
                            spacing=5,
                        ),
                        bgcolor=glass_bgcolor,
                        blur=container_blur,
                        border_radius=10,
                        padding=ft.padding.only(left=10, right=10),
                        expand=True,
                    ),
                    ft.Container(
                        content=filter_dropdown,
                        bgcolor=glass_bgcolor,
                        blur=container_blur,
                        border_radius=10,
                        padding=5,
                    ),
                    ft.Container(
                        content=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(text="Newest First"),
                                ft.PopupMenuItem(text="Oldest First"),
                                ft.PopupMenuItem(text="CPU (High to Low)"),
                                ft.PopupMenuItem(text="CPU (Low to High)"),
                            ],
                            icon=ft.Icons.SORT,
                            tooltip="Sort",
                        ),
                        bgcolor=glass_bgcolor,
                        blur=container_blur,
                        border_radius=10,
                        padding=5,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=10,
        )

    # Build column sets
    running_processes_columns = ["Process Name", "CPU Usage", "Memory Usage", "Status", "Security Check"]
    critical_alerts_columns   = ["Process Name", "PID", "Alert Description", "Timestamp"]
    process_logs_columns      = ["Process Name", "PID", "CPU Usage", "Memory Usage", "Status", "Timestamp"]

    # Create references to data tables
    running_processes_panel = ft.Container(
        content=create_process_table(running_processes_columns, table_ref=running_processes_table_ref),
        expand=True,
        visible=True,
    )
    critical_alerts_panel = ft.Container(
        content=create_process_table(critical_alerts_columns, table_ref=critical_alerts_table_ref),
        expand=True,
        visible=False,
    )
    process_logs_table = create_process_table(process_logs_columns, table_ref=process_logs_table_ref)

    def update_tab(e):
        # Toggle between Running Processes and Critical Alerts
        if tabs.selected_index == 0:
            running_processes_panel.visible = True
            critical_alerts_panel.visible = False
        else:
            running_processes_panel.visible = False
            critical_alerts_panel.visible = True
        # (No direct page reference here; main code will call page.update if needed)
        e.page.update()

    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="Running Processes", icon=ft.Icons.PLAY_ARROW),
            ft.Tab(text="Critical Alerts", icon=ft.Icons.WARNING),
        ],
        selected_index=0,
        indicator_color="#03DAC6",
        on_change=update_tab,
    )

    left_panel = ft.Container(
        content=ft.Column([
            ft.Text("Process Monitoring", size=18, weight=ft.FontWeight.BOLD, color="white"),
            tabs,
            running_processes_panel,
            critical_alerts_panel,
        ]),
        expand=True,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=15,
        padding=20,
    )

    right_panel = ft.Container(
        content=ft.Column([
            ft.Text("Process Logs", size=18, weight=ft.FontWeight.BOLD, color="white"),
            process_logs_table,
            ft.Container(height=10),
        ]),
        expand=True,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=15,
        padding=20,
    )

    # Build search bars
    search_bars = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=create_search_filter_bar(
                        "Processes/Alerts",
                        running_processes_table_ref if tabs.selected_index == 0 else critical_alerts_table_ref,
                        "Processes/Alerts"
                    ),
                    expand=1,
                ),
                ft.Container(
                    content=create_search_filter_bar("Process Logs", process_logs_table_ref, "Process Logs"),
                    expand=1,
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_color="white",
                    tooltip="Refresh Now",
                    on_click=lambda e: update_process_data(e.page)
                ),
            ],
            spacing=4,
        ),
        margin=ft.margin.only(left=10, right=10, top=2),
    )

    status_text = ft.Text("Initializing...", color="white", size=12, ref=status_text_ref)

    # Final layout
    layout = ft.Column(
        controls=[
            search_bars,
            ft.Row(
                controls=[left_panel, right_panel],
                spacing=4,
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            status_text
        ],
        spacing=0,
        expand=True,
    )

    def init_process_monitor(page: ft.Page):
        """
        Call this once, after you've added the layout to your page, to:
          1) Start the background updates.
          2) Do the initial data fetch.
        """
        logger.info("Process monitor UI initialized")
        start_updates(page)
        update_process_data(page)
        logger.debug(f"Initial process data: {processes}")

    # Return the layout plus the init function
    return layout, init_process_monitor