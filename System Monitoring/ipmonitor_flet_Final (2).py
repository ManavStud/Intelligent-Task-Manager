import flet as ft
import psutil
import threading
from datetime import datetime
import logging
import sys

# ----------------------------
# Logging Configuration
# ----------------------------
json_format = (
    '{"timestamp": "%(asctime)s", '
    '"level": "%(levelname)s", '
    '"script": "%(name)s", '
    '"module": "%(module)s", '
    '"funcName": "%(funcName)s", '
    '"lineNo": %(lineno)d, '
    '"message": "%(message)s"}'
)

logger = logging.getLogger("IPMonitor")
logger.setLevel(logging.DEBUG)

# We'll attach a custom handler later to capture logs in the GUI as well.
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(json_format)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ----------------------------
# Color Scheme
# ----------------------------
DARK_BLUE = "#0B0F19"
TEAL_BLUE = "#027B8C"
LIGHT_GRAY = "#D9E2EC"
ACCENT_COLOR = "#03DAC6"
CARD_BG = "#112240"


class FletLogHandler(logging.Handler):
    """
    A custom logging handler to capture logs and insert them into the
    Flet UI DataTable in real-time.
    """
    def __init__(self, ip_monitor_tab):
        super().__init__()
        self.ip_monitor_tab = ip_monitor_tab

    def emit(self, record):
        """
        Whenever a log record is emitted, parse it into JSON format and
        insert it into the logs DataTable.
        """
        try:
            self.ip_monitor_tab.insert_log(record)
        except Exception as e:
            # Fallback in case something goes wrong
            print(f"Error in FletLogHandler.emit: {e}")


class IPMonitorTab:
    def __init__(self, page: ft.Page):
        self.page = page
        self.connections = {}

        logger.info("Initializing IP Monitor Tab")

        # -------------------------------------
        # Left Side: IP Monitor UI
        # -------------------------------------

        # Title styled to match theme
        self.title = ft.Text(
            "IP Monitor",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=TEAL_BLUE,
        )

        # Create AppBar with a title and some padding
        self.app_bar = ft.AppBar(
            title=self.title,
            bgcolor=DARK_BLUE,
            center_title=True,
            elevation=4,
        )

        # ----------------------------
        # IP Monitor: Search & Filter
        # ----------------------------
        # Search Bar styling
        self.search_field = ft.TextField(
            hint_text="Search by IP Address",
            expand=True,
            border_color=ACCENT_COLOR,
            border_width=2,
            border_radius=8,
            filled=True,
            fill_color="#1A2433",
            color=LIGHT_GRAY,
            on_submit=self.filter_table,
        )
        self.search_button = ft.ElevatedButton(
            text="Search",
            bgcolor=ACCENT_COLOR,
            color=DARK_BLUE,
            on_click=self.filter_table,
        )
        self.search_bar = ft.Row(
            controls=[self.search_field, self.search_button],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Dropdown for filter type selection
        self.filter_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Session Data"),
                ft.dropdown.Option("Session Duration"),
            ],
            value="Session Data",
            width=200,
            on_change=self.update_filter_field,
        )

        # Filter Field (dynamic based on dropdown selection)
        self.filter_field = ft.TextField(
            hint_text="Filter by Session Data (e.g., '>1000', '<4000')",
            expand=True,
            border_color=ACCENT_COLOR,
            border_width=2,
            border_radius=8,
            filled=True,
            fill_color="#1A2433",
            color=LIGHT_GRAY,
        )

        # Filter Button
        self.filter_button = ft.ElevatedButton(
            text="Apply Filter",
            bgcolor=ACCENT_COLOR,
            color=DARK_BLUE,
            on_click=self.apply_filters,
        )

        # Filter Bar
        self.filter_bar = ft.Row(
            controls=[
                self.filter_type_dropdown,
                self.filter_field,
                self.filter_button,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Create IPv4 and IPv6 panels wrapped in Cards
        self.ipv4_table = self.create_ip_table("IPv4 Connections")
        self.ipv4_card = ft.Card(
            content=ft.Container(
                content=self.ipv4_table,
                padding=20,
                bgcolor=CARD_BG,
                border_radius=12,
            ),
            elevation=8,
            margin=10,
        )

        self.ipv6_table = self.create_ip_table("IPv6 Connections")
        self.ipv6_card = ft.Card(
            content=ft.Container(
                content=self.ipv6_table,
                padding=20,
                bgcolor=CARD_BG,
                border_radius=12,
            ),
            elevation=8,
            margin=10,
        )

        # -------------------------------------
        # Left Column layout
        # -------------------------------------
        self.left_column = ft.Column(
            controls=[
                self.search_bar,
                self.filter_bar,
                ft.Text("IPv4 Connections", size=20, weight=ft.FontWeight.BOLD, color=LIGHT_GRAY),
                self.ipv4_card,
                ft.Divider(height=2, color=ACCENT_COLOR),
                ft.Text("IPv6 Connections", size=20, weight=ft.FontWeight.BOLD, color=LIGHT_GRAY),
                self.ipv6_card,
            ],
            spacing=20,
            expand=True,
        )

        # -------------------------------------
        # Right Side: Network Logs
        # -------------------------------------
        # We store all logs in a list to help with searching/filtering
        self.logs_records = []

        # Logs search & filter controls
        self.logs_search_field = ft.TextField(
            hint_text="Search logs by text",
            expand=True,
            border_color=ACCENT_COLOR,
            border_width=2,
            border_radius=8,
            filled=True,
            fill_color="#1A2433",
            color=LIGHT_GRAY,
            on_submit=self.filter_logs_table,
        )
        self.logs_search_button = ft.ElevatedButton(
            text="Search",
            bgcolor=ACCENT_COLOR,
            color=DARK_BLUE,
            on_click=self.filter_logs_table,
        )
        self.logs_search_bar = ft.Row(
            controls=[self.logs_search_field, self.logs_search_button],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Filter by log level, message, or timestamp
        self.logs_filter_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Timestamp"),
                ft.dropdown.Option("Level"),
                ft.dropdown.Option("Message"),
            ],
            value="Message",
            width=200,
            on_change=self.update_logs_filter_field,
        )
        self.logs_filter_field = ft.TextField(
            hint_text="Filter logs by message (e.g., 'Connected')",
            expand=True,
            border_color=ACCENT_COLOR,
            border_width=2,
            border_radius=8,
            filled=True,
            fill_color="#1A2433",
            color=LIGHT_GRAY,
        )
        self.logs_filter_button = ft.ElevatedButton(
            text="Apply Filter",
            bgcolor=ACCENT_COLOR,
            color=DARK_BLUE,
            on_click=self.apply_logs_filters,
        )
        self.logs_filter_bar = ft.Row(
            controls=[
                self.logs_filter_type_dropdown,
                self.logs_filter_field,
                self.logs_filter_button,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Create the logs DataTable
        self.logs_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Timestamp", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Level", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Script", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Module", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Func", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Line", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Message", color=LIGHT_GRAY)),
            ],
            rows=[],
            heading_row_color=ft.colors.BLACK12,
            border=ft.border.all(1, LIGHT_GRAY),
        )
        # Wrap logs table in a container with horizontal scroll and fixed height
        self.logs_table_container = ft.Container(
            content=ft.Row(
                controls=[self.logs_table],
                scroll=ft.ScrollMode.ALWAYS,
            ),
            padding=ft.Padding(left=0, top=0, bottom=0, right=10),
            bgcolor=CARD_BG,
            height=300,
            expand=False,
        )

        self.logs_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[self.logs_search_bar, self.logs_filter_bar, self.logs_table_container],
                    spacing=10,
                ),
                padding=20,
                bgcolor=CARD_BG,
                border_radius=12,
            ),
            elevation=8,
            margin=10,
        )

        # Right Column layout
        self.right_column = ft.Column(
            controls=[
                # ft.Text("Search & Filter Logs", size=20, weight=ft.FontWeight.BOLD, color=LIGHT_GRAY),
                # self.logs_search_bar,
                # self.logs_filter_bar,
                ft.Text("Network Logs", size=20, weight=ft.FontWeight.BOLD, color=LIGHT_GRAY),
                self.logs_card,
            ],
            spacing=20,
            expand=True,
        )

        # -------------------------------------
        # Combine left & right columns in a row
        # -------------------------------------
        self.main_content = ft.Row(
            controls=[
                ft.Container(
                    content=self.left_column,
                    expand=True,
                ),
                ft.VerticalDivider(width=2, color=ACCENT_COLOR),
                ft.Container(
                    content=self.right_column,
                    expand=True,
                ),
            ],
            expand=True,
        )

        # Add a dummy sample row so info is visible immediately for IP table
        self.insert_connection("192.168.1.1", {
            'connected_at': datetime.now(),
            'bytes_sent': 12345,
            'bytes_recv': 54321,
            'process_name': "TestProcess",
            'process_id': 1234,
            'security_check': "Safe",
        }, "Connected")

        # Start Monitoring IP Connections in background
        self.monitor_ip_connections()

    # ----------------------------
    # IP Table Creation
    # ----------------------------
    def create_ip_table(self, label_title):
        logger.debug(f"Creating IP table for {label_title}")
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("IP Address", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Status", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Connected At", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Disconnected At", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Session Duration", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Session Data", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Process Name", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Process ID", color=LIGHT_GRAY)),
                ft.DataColumn(ft.Text("Security Check", color=LIGHT_GRAY)),
            ],
            rows=[],
            heading_row_color=ft.colors.BLACK12,
            border=ft.border.all(1, LIGHT_GRAY),
        )
        # Wrap the table in a Row for horizontal scrolling and fix the height
        container = ft.Container(
            content=ft.Row(
                controls=[table],
                scroll=ft.ScrollMode.ALWAYS,
            ),
            padding=ft.Padding(left=0, top=0, bottom=0, right=10),
            bgcolor=CARD_BG,
            height=300,
            expand=False,
        )
        return container

    # ----------------------------
    # IP Table Search & Filter
    # ----------------------------
    def update_filter_field(self, e):
        filter_type = self.filter_type_dropdown.value
        if filter_type == "Session Data":
            self.filter_field.hint_text = "Filter by Session Data (e.g., '>1000', '<4000')"
        elif filter_type == "Session Duration":
            self.filter_field.hint_text = "Filter by Session Duration (e.g., '>0:00:10', '<0:01:00')"
        self.page.update()

    def filter_table(self, e):
        search_text = self.search_field.value.strip()
        if not search_text:
            self.reset_table()
            return

        # Determine if it's IPv4 or IPv6 search
        if "." in search_text:
            table_rows = self.ipv4_table.content.controls[0].rows
        else:
            table_rows = self.ipv6_table.content.controls[0].rows

        for row in table_rows:
            ip_value = row.cells[0].content.value
            row.visible = search_text in ip_value

        self.page.update()

    def apply_filters(self, e):
        filter_type = self.filter_type_dropdown.value
        filter_value = self.filter_field.value.strip()

        all_rows = (
            self.ipv4_table.content.controls[0].rows +
            self.ipv6_table.content.controls[0].rows
        )

        for row in all_rows:
            match = True

            if filter_type == "Session Data":
                # e.g. "Sent: 12345, Received: 54321"
                session_data = row.cells[5].content.value
                # Extract the numeric portion of 'Sent: X'
                try:
                    sent_str = session_data.split(":")[1].split(",")[0].strip()
                    session_data_value = int(sent_str)
                except Exception:
                    session_data_value = 0

                if filter_value.startswith(">"):
                    match = session_data_value > int(filter_value[1:])
                elif filter_value.startswith("<"):
                    match = session_data_value < int(filter_value[1:])
                else:
                    match = session_data_value == int(filter_value)

            elif filter_type == "Session Duration":
                session_duration = row.cells[4].content.value  # "HH:MM:SS"
                if not session_duration:
                    match = False
                else:
                    if filter_value.startswith(">"):
                        match = session_duration > filter_value[1:]
                    elif filter_value.startswith("<"):
                        match = session_duration < filter_value[1:]
                    else:
                        match = (session_duration == filter_value)

            row.visible = match

        self.page.update()

    def reset_table(self):
        for table in [self.ipv4_table, self.ipv6_table]:
            for row in table.content.controls[0].rows:
                row.visible = True
        self.page.update()

    # ----------------------------
    # IP Monitoring
    # ----------------------------
    def monitor_ip_connections(self):
        logger.info("Starting IP connection monitoring in background thread")
        threading.Thread(target=self._monitor_ip_connections, daemon=True).start()

    def _monitor_ip_connections(self):
        while True:
            try:
                current_conns = self.get_foreign_connections()
                logger.debug(f"Current foreign connections fetched: {len(current_conns)}")

                # Check for new connections
                for ip, details in current_conns.items():
                    if ip not in self.connections:
                        logger.info(f"New connection detected: {ip}")
                        self.connections[ip] = details
                        self.insert_connection(ip, details, "Connected")

                # Check for disconnected
                for ip in list(self.connections.keys()):
                    if ip not in current_conns and 'disconnected_at' not in self.connections[ip]:
                        logger.info(f"Connection disconnected: {ip}")
                        self.connections[ip]['disconnected_at'] = datetime.now()
                        net_counters = psutil.net_io_counters()
                        self.connections[ip]['bytes_sent'] = (
                            net_counters.bytes_sent - self.connections[ip]['bytes_sent']
                        )
                        self.connections[ip]['bytes_recv'] = (
                            net_counters.bytes_recv - self.connections[ip]['bytes_recv']
                        )
                        self.insert_connection(ip, self.connections[ip], "Disconnected")

                # Remove disconnected IPs from tracking
                for ip in list(self.connections.keys()):
                    if 'disconnected_at' in self.connections[ip]:
                        logger.debug(f"Removing disconnected IP from tracking: {ip}")
                        del self.connections[ip]

            except Exception as e:
                logger.error(f"Error monitoring IP connections: {e}")

            self.page.update()
            threading.Event().wait(2)

    def get_foreign_connections(self):
        logger.debug("Fetching foreign connections using psutil")
        foreign_conns = {}
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                ip = conn.raddr.ip
                # If multiple connections to same IP, we only track once
                if ip not in foreign_conns:
                    process = psutil.Process(conn.pid) if conn.pid else None
                    process_name = process.name() if process else "Unknown"
                    process_id = conn.pid if conn.pid else "N/A"
                    foreign_conns[ip] = {
                        'connected_at': datetime.now(),
                        'bytes_sent': psutil.net_io_counters().bytes_sent,
                        'bytes_recv': psutil.net_io_counters().bytes_recv,
                        'process_name': process_name,
                        'process_id': process_id,
                        'security_check': self.perform_security_check(ip),
                    }
        logger.debug(f"Fetched {len(foreign_conns)} foreign connections")
        return foreign_conns

    def perform_security_check(self, ip):
        malicious_ips = ["1.1.1.1", "2.2.2.2"]
        return "Malicious" if ip in malicious_ips else "Safe"

    def insert_connection(self, ip, details, status):
        connected_at = details['connected_at'].strftime("%Y-%m-%d %H:%M:%S")
        disconnected_at = (
            details.get('disconnected_at', "").strftime("%Y-%m-%d %H:%M:%S")
            if status == "Disconnected" else ""
        )
        duration = (
            str(details['disconnected_at'] - details['connected_at']).split(".")[0]
            if status == "Disconnected" else ""
        )
        session_data = f"Sent: {details.get('bytes_sent', 0)}, Received: {details.get('bytes_recv', 0)}"
        process_name = details.get('process_name', "Unknown")
        process_id = details.get('process_id', "N/A")
        security_check = details.get('security_check', "Safe")

        # Access the correct DataTable
        if "." in ip:
            table_rows = self.ipv4_table.content.controls[0].rows
        else:
            table_rows = self.ipv6_table.content.controls[0].rows

        # If IP already in table, update
        for row in table_rows:
            if row.cells[0].content.value == ip:
                row.cells[1].content.value = status
                row.cells[2].content.value = connected_at
                row.cells[3].content.value = disconnected_at
                row.cells[4].content.value = duration
                row.cells[5].content.value = session_data
                row.cells[6].content.value = process_name
                row.cells[7].content.value = process_id
                row.cells[8].content.value = security_check
                self.page.update()
                return

        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(ip, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(status, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(connected_at, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(disconnected_at, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(duration, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(session_data, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(process_name, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(process_id, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(security_check, color=LIGHT_GRAY)),
            ]
        )
        table_rows.append(new_row)
        self.page.update()

    # ----------------------------
    # Logs Table Insertion
    # ----------------------------
    def insert_log(self, record):
        """
        Insert a log record into the logs table and keep a copy in `self.logs_records`.
        We use `record` attributes directly for each column.
        """
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        script = record.name
        module = record.module
        func = record.funcName
        line = record.lineno
        msg = record.getMessage()

        # Keep in list for search/filter
        self.logs_records.append({
            "timestamp": ts,
            "level": level,
            "script": script,
            "module": module,
            "funcName": func,
            "lineNo": line,
            "message": msg
        })

        # Insert into DataTable
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(ts, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(level, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(script, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(module, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(func, color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(str(line), color=LIGHT_GRAY)),
                ft.DataCell(ft.Text(msg, color=LIGHT_GRAY)),
            ]
        )
        self.logs_table.rows.append(new_row)
        self.page.update()

    # ----------------------------
    # Logs Table Search & Filter
    # ----------------------------
    def update_logs_filter_field(self, e):
        filter_type = self.logs_filter_type_dropdown.value
        if filter_type == "Timestamp":
            self.logs_filter_field.hint_text = "Filter logs by timestamp (e.g., '2025-02-18')"
        elif filter_type == "Level":
            self.logs_filter_field.hint_text = "Filter logs by level (e.g., INFO, DEBUG, ERROR)"
        else:
            self.logs_filter_field.hint_text = "Filter logs by message (e.g., 'Connected')"
        self.page.update()

    def filter_logs_table(self, e):
        """
        Search logs by text (in any column). If the search field is empty, reset.
        """
        search_text = self.logs_search_field.value.strip().lower()
        if not search_text:
            self.reset_logs_table()
            return

        for i, row_data in enumerate(self.logs_records):
            row = self.logs_table.rows[i]
            combined_text = (
                f"{row_data['timestamp']} {row_data['level']} {row_data['script']} "
                f"{row_data['module']} {row_data['funcName']} {row_data['lineNo']} {row_data['message']}"
            ).lower()
            row.visible = search_text in combined_text

        self.page.update()

    def apply_logs_filters(self, e):
        """
        Filter logs by timestamp, level, or message, depending on dropdown.
        """
        filter_type = self.logs_filter_type_dropdown.value
        filter_value = self.logs_filter_field.value.strip().lower()
        if not filter_value:
            self.reset_logs_table()
            return

        for i, row_data in enumerate(self.logs_records):
            row = self.logs_table.rows[i]
            if filter_type == "Timestamp":
                row.visible = (filter_value in row_data["timestamp"].lower())
            elif filter_type == "Level":
                row.visible = (row_data["level"].lower() == filter_value)
            else:
                row.visible = (filter_value in row_data["message"].lower())

        self.page.update()

    def reset_logs_table(self):
        """
        Reset the logs table to show all rows.
        """
        for row in self.logs_table.rows:
            row.visible = True
        self.page.update()


def main(page: ft.Page):
    page.title = "IP Monitor"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = DARK_BLUE
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.scroll = ft.ScrollMode.AUTO

    # Create IPMonitorTab
    ip_monitor = IPMonitorTab(page)

    # Replace the default logger's handler with our FletLogHandler (in addition to console)
    flet_handler = FletLogHandler(ip_monitor)
    flet_handler.setLevel(logging.DEBUG)
    flet_handler.setFormatter(formatter)
    logger.addHandler(flet_handler)

    # Set the page appbar and add the main content
    page.appbar = ip_monitor.app_bar
    page.add(
        ft.Container(
            content=ip_monitor.main_content,
            padding=20,
            expand=True,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
