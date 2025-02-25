import flet as ft
from flet import Colors, Blur, BlurTileMode, BoxShadow, ShadowBlurStyle, Offset
import psutil
import time
from datetime import datetime

def create_network_monitoring_layout(glass_bgcolor, container_blur, container_shadow):
    # References to update tables
    ipv4_live_table_ref = ft.Ref[ft.Container]()
    ipv6_live_table_ref = ft.Ref[ft.Container]()
    ipv4_logs_table_ref = ft.Ref[ft.Container]()
    ipv6_logs_table_ref = ft.Ref[ft.Container]()

    # Store connection logs
    connection_logs = {
        "ipv4": [],
        "ipv6": []
    }

    def get_network_data():
        """Fetch live network connections using psutil"""
        connections = psutil.net_connections()
        live_data_ipv4 = []
        live_data_ipv6 = []
        current_time = datetime.now()

        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:  # Only show active connections
                process = psutil.Process(conn.pid) if conn.pid else None
                process_name = process.name() if process else "Unknown"
                
                data_row = [
                    process_name,
                    conn.pid if conn.pid else "N/A",
                    f"{conn.raddr.ip}:{conn.raddr.port}",
                    "Pending",  # Security check placeholder
                    "Active",   # Duration placeholder
                    f"{psutil.net_io_counters().bytes_recv / 1024:.2f} KB",  # Data in
                    f"{psutil.net_io_counters().bytes_sent / 1024:.2f} KB"   # Data out
                ]

                log_row = [
                    process_name,
                    conn.pid if conn.pid else "N/A",
                    f"{conn.raddr.ip}:{conn.raddr.port}",
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Pending",
                    "Active",
                    f"{psutil.net_io_counters().bytes_recv / 1024:.2f} KB",
                    f"{psutil.net_io_counters().bytes_sent / 1024:.2f} KB"
                ]

                if ':' in conn.raddr.ip:  # IPv6
                    live_data_ipv6.append(data_row)
                    connection_logs["ipv6"].append(log_row)
                else:  # IPv4
                    live_data_ipv4.append(data_row)
                    connection_logs["ipv4"].append(log_row)

        # Keep only last 50 logs to prevent memory issues
        connection_logs["ipv4"] = connection_logs["ipv4"][-50:]
        connection_logs["ipv6"] = connection_logs["ipv6"][-50:]

        return live_data_ipv4, live_data_ipv6

    def create_network_table(columns, sample_data=None, table_ref=None):
        if sample_data is None:
            sample_data = []
    
        table = ft.Container(
            content=ft.Column(
            [ft.DataTable(
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
                            width=85 if col == "Process Name" else
                                70 if col in ["IP Address", "Connection Start Timestamp"] else
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
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        str(cell),
                                        color="white",
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    tooltip=ft.Tooltip(
                                        message=str(cell),
                                        bgcolor="#08CDFF",
                                        text_style=ft.TextStyle(color="white"),
                                        padding=5,
                                    ),
                                )
                            ) for cell in row
                        ]
                    ) for row in sample_data
                ],
                border=ft.border.all(0, "transparent"),
                horizontal_lines=ft.border.BorderSide(1, "#363636"),
                heading_row_color=Colors.with_opacity(0.1, "white"),
                heading_row_height=45,
                data_row_min_height=30,
                data_row_max_height=40,
                column_spacing=8,
            )],
            scroll="auto",
            spacing=0,
        ),
        ref=table_ref,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        expand=True,
        padding=5,
    )
        return table

    def create_search_filter_bar(title):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH, color='#6c757d', size=16),
                                ft.TextField(
                                    border=ft.InputBorder.NONE,
                                    height=35,
                                    text_size=12,
                                    bgcolor='transparent',
                                    color='white',
                                    hint_text=f"Search {title}...",
                                    hint_style=ft.TextStyle(color='#6c757d'),
                                    expand=True,
                                    content_padding=ft.padding.only(left=8, right=8),
                                )
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
                        content=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(text="Process Name"),
                                ft.PopupMenuItem(text="PID"),
                                ft.PopupMenuItem(text="IP Address"),
                                ft.PopupMenuItem(text="Duration"),
                                ft.PopupMenuItem(text="Data Transfer"),
                            ],
                            icon=ft.Icons.FILTER_LIST,
                            tooltip="Filter",
                        ),
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
                                ft.PopupMenuItem(text="Data (High to Low)"),
                                ft.PopupMenuItem(text="Data (Low to High)"),
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

    def update_network_data(e):
        """Update network tables with live data"""
        live_ipv4, live_ipv6 = get_network_data()
        
        # Update live tables
        if ipv4_live_table_ref.current:
            ipv4_live_table_ref.current.content.controls[0].rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(message=str(cell), bgcolor="#08CDFF", text_style=ft.TextStyle(color="white"), padding=5)
                            )
                        ) for cell in row
                    ]
                ) for row in live_ipv4
            ]
        
        if ipv6_live_table_ref.current:
            ipv6_live_table_ref.current.content.controls[0].rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(message=str(cell), bgcolor="#08CDFF", text_style=ft.TextStyle(color="white"), padding=5)
                            )
                        ) for cell in row
                    ]
                ) for row in live_ipv6
            ]

        # Update log tables
        if ipv4_logs_table_ref.current:
            ipv4_logs_table_ref.current.content.controls[0].rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(message=str(cell), bgcolor="#08CDFF", text_style=ft.TextStyle(color="white"), padding=5)
                            )
                        ) for cell in row
                    ]
                ) for row in connection_logs["ipv4"]
            ]
        
        if ipv6_logs_table_ref.current:
            ipv6_logs_table_ref.current.content.controls[0].rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(cell), color="white", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                                tooltip=ft.Tooltip(message=str(cell), bgcolor="#08CDFF", text_style=ft.TextStyle(color="white"), padding=5)
                            )
                        ) for cell in row
                    ]
                ) for row in connection_logs["ipv6"]
            ]

        if e.page:
            e.page.update()

    ipv4_live_columns = [
        "Process Name", "PID", "IP Address", "Security Check", 
        "Duration", "Data in", "Data out"
    ]

    ipv6_live_columns = [
        "Process Name", "PID", "IP Address", "Security Check", 
        "Duration", "Data in", "Data out"
    ]

    ipv4_logs_columns = [
        "Process Name", "PID", "IP Address", "Connection Start Timestamp",
        "Security Check", "Duration", "Data in", "Data out"
    ]

    ipv6_logs_columns = [
        "Process Name", "PID", "IP Address", "Connection Start Timestamp",
        "Security Check", "Duration", "Data in", "Data out"
    ]

    left_top_section = ft.Container(
        content=ft.Column([
            ft.Text(
                "Live Network Connections: IPv4",
                size=18,
                weight=ft.FontWeight.BOLD,
                color="white"
            ),
            create_network_table(ipv4_live_columns, table_ref=ipv4_live_table_ref),
        ]),
        expand=True,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=15,
        padding=20,
    )

    left_bottom_section = ft.Container(
        content=ft.Column([
            ft.Text(
                "Live Network Connections: IPv6",
                size=18,
                weight=ft.FontWeight.BOLD,
                color="white"
            ),
            create_network_table(ipv6_live_columns, table_ref=ipv6_live_table_ref),
        ]),
        expand=True,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=15,
        padding=20,
    )

    left_panel = ft.Container(
        content=ft.Column(
            controls=[
                left_top_section,
                left_bottom_section,
            ],
            spacing=10,
            expand=True,
        ),
        expand=1,
        margin=ft.margin.only(left=10, right=2, top=2, bottom=10),
    )

    right_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Network Connections: IPv4",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="white"
                        ),
                        create_network_table(ipv4_logs_columns, table_ref=ipv4_logs_table_ref),
                    ]),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Divider(
                        height=0,
                        color="#14E1F4",
                    ),
                    alignment=ft.alignment.center,
                    width=2000,
                    shadow=BoxShadow(
                        spread_radius=2,
                        blur_radius=10,
                        color="#14E1F4",
                        offset=Offset(0, 0),
                        blur_style=ShadowBlurStyle.OUTER,
                    ),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=10),
                        ft.Text(
                            "Network Connections: IPv6",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="white"
                        ),
                        create_network_table(ipv6_logs_columns, table_ref=ipv6_logs_table_ref),
                    ]),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=1,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=15,
        margin=ft.margin.only(left=2, right=10, top=2, bottom=10),
        padding=20,
    )

    search_bars = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=create_search_filter_bar("Live Connections"),
                    expand=1,
                ),
                ft.Container(
                    content=create_search_filter_bar("Network Connections"),
                    expand=1,
                ),
            ],
            spacing=4,
        ),
        margin=ft.margin.only(left=10, right=10, top=2),
    )

    # Create the main layout
    layout = ft.Column(
        controls=[
            search_bars,
            ft.Row(
                controls=[
                    left_panel,
                    right_panel,
                ],
                spacing=4,
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=0,
        expand=True,
    )

    # Add an update mechanism
    def start_updates(page):
        while True:
            update_network_data(ft.ControlEvent(page=page, control=None, data=None))
            time.sleep(5)  # Update every 5 seconds

    # Start the updates when the page loads
    layout.on_load = lambda e: ft.Page.go_async(e.page, start_updates)

    return layout

# Note: You'll need to install psutil if you haven't already
# Run: pip install psutil