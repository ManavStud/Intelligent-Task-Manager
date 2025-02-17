import flet as ft
import json
import os
import re
import pandas as pd
import threading
import time
from datetime import datetime, timedelta



# ----------------------------
# Configurable constants
# ----------------------------
CHUNK_SIZE = 100         # lines to load for each "older logs" chunk
TABLE_PAGE_SIZE = 100    # number of lines to SHOW in the table
LOG_FILE_PATH = None     # set when user picks file

DARK_BLUE = "#0B0F19"
TEAL_BLUE = "#027B8C"
DARK_RED = "#B22222"
LIGHT_GRAY = "#D9E2EC"
ENTRY_BG = "#1C2B36"
FRAME_BG = "#022B3A"
CARD_BG = "#18202C"
TEXT_LIGHT = "#FFFFFF"

def get_file_line_count(file_path):
    count = 0
    try:
        with open(file_path, "r") as f:
            for _ in f:
                count += 1
    except:
        pass
    return count

def read_lines_in_range(file_path, start_line, end_line):
    lines = []
    try:
        with open(file_path, "r") as f:
            idx = 0
            for line in f:
                if idx >= end_line:
                    break
                if idx >= start_line:
                    lines.append(line.rstrip("\n"))
                idx += 1
    except Exception as e:
        print("Error reading file range:", e)
    return lines

def tail_file(file_path, on_new_line_callback):
    """
    Continuously watch the file for new lines appended (tail -f).
    Calls on_new_line_callback(line) for each new line.
    """
    with open(file_path, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            on_new_line_callback(line.rstrip("\n"))

class LogEntry:
    def __init__(self, timestamp, level, script, module, funcName, lineNo, message, **kwargs):
        try:
            self.timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            self.timestamp = None
        self.level = level
        self.script = script
        self.module = module
        self.funcName = funcName
        self.lineNo = lineNo
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

def parse_log_line(json_line):
    try:
        log_json = json.loads(json_line)
        required = ["timestamp", "level", "script", "module", "funcName", "lineNo", "message"]
        if not all(k in log_json for k in required):
            return None
        return log_json
    except:
        return None

def build_df_from_lines(lines):
    data = []
    for ln in lines:
        parsed = parse_log_line(ln)
        if not parsed:
            continue
        entry = LogEntry(**parsed)
        data.append({
            "timestamp": entry.timestamp,
            "level": entry.level or "UNKNOWN",
            "script": entry.script or "",
            "module": entry.module or "",
            "funcName": entry.funcName or "",
            "lineNo": entry.lineNo,
            "message": entry.message or "",
        })
    return pd.DataFrame(data)

def main(page: ft.Page):
    page.title = "Lazy-load + Tail + Full-data Chart, Partial Table"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = DARK_BLUE
    page.scroll = "adaptive"
    page.window_resizable = True

    # The master DataFrame that includes older lines + tailed lines
    global_df = pd.DataFrame()

    # Track how many older lines remain
    older_line_index = 0
    log_file_path = None

    # Filter state
    start_datetime = None
    end_datetime = None

    # --------------------------------------
    # Stats Row
    # --------------------------------------
    total_count_text = ft.Text("0", color=LIGHT_GRAY, size=20)
    info_count_text = ft.Text("0", color=LIGHT_GRAY, size=20)
    warn_count_text = ft.Text("0", color=LIGHT_GRAY, size=20)
    error_count_text = ft.Text("0", color=LIGHT_GRAY, size=20)

    def process_chart_data(df):
        # Time series data
        time_series = df.groupby([pd.Grouper(key='timestamp', freq='H'), 'level']).size().unstack(fill_value=0)
        
        # Level distribution
        level_counts = df['level'].value_counts()
        
        # Module analysis
        module_stats = df.groupby(['module', 'level']).size().unstack(fill_value=0)
        
        return {
            'timeSeries': time_series.to_dict('records'),
            'levelDistribution': level_counts.to_dict(),
            'moduleAnalysis': module_stats.to_dict('records')
    }

    def update_stats(df):
        if df.empty:
            total_count_text.value = "0"
            info_count_text.value = "0"
            warn_count_text.value = "0"
            error_count_text.value = "0"
            page.update()
            return

        total_count = len(df)
        info_count = len(df[df["level"].str.upper() == "INFO"])
        warn_count = len(df[df["level"].str.upper() == "WARNING"])
        error_count = len(df[df["level"].str.upper().isin(["ERROR","CRITICAL"])])

        total_count_text.value = str(total_count)
        info_count_text.value = str(info_count)
        warn_count_text.value = str(warn_count)
        error_count_text.value = str(error_count)
        page.update()

    def make_stat_card(title, value_widget, icon_name):
        return ft.Container(
            width=180,
            height=100,
            bgcolor=CARD_BG,
            border_radius=8,
            padding=10,
            content=ft.Row(
                controls=[
                    ft.Icon(name=icon_name, color=TEAL_BLUE, size=30),
                    ft.Column(
                        spacing=3,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(title, color=LIGHT_GRAY, size=14),
                            value_widget,
                        ],
                    )
                ],
                alignment="start"
            ),
        )

    stats_row = ft.Row(
        controls=[
            make_stat_card("Total Logs", total_count_text, ft.icons.LIST),
            make_stat_card("Infos", info_count_text, ft.icons.INFO),
            make_stat_card("Warnings", warn_count_text, ft.icons.WARNING),
            make_stat_card("Errors", error_count_text, ft.icons.ERROR),
        ],
        alignment="spaceBetween",
    )

    # --------------------------------------
    # Filters & search
    # --------------------------------------
    search_field = ft.TextField(
        label="Search in Messages",
        hint_text="Type to filter by text...",
        width=300,
        border_color=TEAL_BLUE,
        color=LIGHT_GRAY
    )
    quick_filter_dropdown = ft.Dropdown(
        label="Time Filter",
        options=[
            ft.dropdown.Option("Custom"),
            ft.dropdown.Option("Last Hour"),
            ft.dropdown.Option("Last 24 Hours"),
            ft.dropdown.Option("Last 7 Days"),
            ft.dropdown.Option("Last 30 Days"),
        ],
        value="Custom",
        width=200,
        border_color=TEAL_BLUE,
        color=LIGHT_GRAY
    )
    start_label = ft.Text("Start: Not Set", color=LIGHT_GRAY)
    end_label = ft.Text("End: Not Set", color=LIGHT_GRAY)

    script_field = ft.TextField(label="Script Name", hint_text="Enter script...", width=200,
                                border_color=TEAL_BLUE, color=LIGHT_GRAY)
    module_field = ft.TextField(label="Module Name", hint_text="Enter module...", width=200,
                                border_color=TEAL_BLUE, color=LIGHT_GRAY)
    message_field = ft.TextField(label="Message (Regex)", hint_text="Enter regex...", width=300,
                                 border_color=TEAL_BLUE, color=LIGHT_GRAY)
    level_dropdown = ft.Dropdown(
        label="Log Level",
        options=[
            ft.dropdown.Option(""),
            ft.dropdown.Option("INFO"),
            ft.dropdown.Option("DEBUG"),
            ft.dropdown.Option("WARNING"),
            ft.dropdown.Option("ERROR"),
            ft.dropdown.Option("CRITICAL")
        ],
        value="",
        width=150,
        border_color=TEAL_BLUE,
        color=LIGHT_GRAY
    )
    apply_filter_button = ft.ElevatedButton("Apply", bgcolor=TEAL_BLUE, color=LIGHT_GRAY, icon=ft.icons.FILTER_LIST)

    advanced_filters_container = ft.Column(
        visible=False,
        controls=[
            ft.Row([script_field, module_field, message_field, level_dropdown, apply_filter_button]),
        ]
    )
    expand_filters_button = ft.IconButton(
        icon=ft.icons.ARROW_DROP_DOWN,
        icon_color=LIGHT_GRAY,
        tooltip="Show Advanced Filters",
    )

    def toggle_advanced_filters(e):
        advanced_filters_container.visible = not advanced_filters_container.visible
        if advanced_filters_container.visible:
            expand_filters_button.icon = ft.icons.ARROW_DROP_UP
            expand_filters_button.tooltip = "Hide Advanced Filters"
        else:
            expand_filters_button.icon = ft.icons.ARROW_DROP_DOWN
            expand_filters_button.tooltip = "Show Advanced Filters"
        page.update()

    expand_filters_button.on_click = toggle_advanced_filters

    # --------------------------------------
    # DataTable & Chart
    # --------------------------------------
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Timestamp", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Level", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Script", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Module", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Function", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Line No", color=LIGHT_GRAY)),
            ft.DataColumn(ft.Text("Message", color=LIGHT_GRAY)),
        ],
        rows=[],
        border=ft.border.all(1, TEAL_BLUE),
        heading_row_height=30,
        data_row_min_height=30,
        width=1000,
    )

    chart_container = ft.Container(
        bgcolor=FRAME_BG,
        expand=True,  # Let it grow with window
        content=ft.Text("No logs loaded yet...", color=LIGHT_GRAY)
    )

    # Lazy-load older lines
    load_older_button = ft.ElevatedButton("Load Older Logs", bgcolor=TEAL_BLUE, color=LIGHT_GRAY)

    # Standard: load file, reset, export
    load_button = ft.ElevatedButton("Load File", icon=ft.icons.UPLOAD_FILE, bgcolor=TEAL_BLUE, color=LIGHT_GRAY)
    reset_button = ft.ElevatedButton("Reset", icon=ft.icons.RESTART_ALT, bgcolor=TEAL_BLUE, color=LIGHT_GRAY)
    export_button = ft.ElevatedButton("Export", icon=ft.icons.DOWNLOAD, bgcolor=TEAL_BLUE, color=LIGHT_GRAY)

    # --------------------------------------
    # Functions
    # --------------------------------------
    def apply_filters_to_df(df):
        """
        Return a filtered subset of df, including the search field, advanced fields, and time range.
        """
        if df.empty:
            return df

        mask = pd.Series([True]*len(df), index=df.index)

        # Time
        if start_datetime and end_datetime:
            mask = mask & (df["timestamp"] >= start_datetime) & (df["timestamp"] <= end_datetime)
        # Script
        if script_field.value.strip():
            s_lower = script_field.value.strip().lower()
            mask = mask & (df["script"].str.lower() == s_lower)
        # Module
        if module_field.value.strip():
            m_lower = module_field.value.strip().lower()
            mask = mask & (df["module"].str.lower() == m_lower)
        # Message (regex)
        if message_field.value.strip():
            try:
                pattern = re.compile(message_field.value.strip(), re.IGNORECASE)
                mask = mask & df["message"].apply(lambda x: bool(pattern.search(x)))
            except:
                return pd.DataFrame([])  # invalid regex => none
        # Level
        if level_dropdown.value.strip():
            lvl_lower = level_dropdown.value.strip().lower()
            mask = mask & (df["level"].str.lower() == lvl_lower)
        # Search
        search_txt = search_field.value.strip().lower()
        if search_txt:
            mask = mask & df["message"].str.lower().str.contains(search_txt)

        return df[mask]

    def update_chart(df):
        """
        Draws a line chart representing log counts per hour using Flet's CustomPaint.
        """
        # If no data, show a message.
        if df.empty:
            chart_container.content = ft.Text("No logs to display.", color=LIGHT_GRAY)
            page.update()
            return

        # Remove rows without valid timestamps and sort.
        df_valid = df.dropna(subset=["timestamp"]).copy()
        df_valid = df_valid.sort_values("timestamp")

        # Group the logs by hour, counting logs in each hour.
        grouped = df_valid.set_index("timestamp").groupby(pd.Grouper(freq="H")).size().reset_index(name="count")
        if grouped.empty:
            chart_container.content = ft.Text("No data for chart.", color=LIGHT_GRAY)
            page.update()
            return

        # Create a list of counts for each hourly bin.
        counts = grouped["count"].tolist()

        # Define the drawing function for the CustomPaint widget.
        def draw_line_chart(canvas: ft.Canvas, size: ft.Size):
            data = counts
            n = len(data)
            if n < 2:
                return  # Not enough data points to draw a line
            spacing = size.width / (n - 1)
            max_val = max(data)
            min_val = min(data)
            range_val = max_val - min_val if max_val != min_val else 1
            top_margin = 10
            bottom_margin = 10
            chart_height = size.height - top_margin - bottom_margin

            # Start a new path at the first data point.
            path = ft.Path()
            x0 = 0
            y0 = top_margin + chart_height * (1 - (data[0] - min_val) / range_val)
            path.moveTo(ft.Offset(x0, y0))
            
            # Draw lines for each subsequent point.
            for i in range(1, n):
                x = i * spacing
                y = top_margin + chart_height * (1 - (data[i] - min_val) / range_val)
                path.lineTo(ft.Offset(x, y))
            
            # Define the paint style.
            paint = ft.Paint(color="blue", stroke_width=3, style=ft.PaintStyle.STROKE)
            canvas.drawPath(path, paint)

        # Update the chart_container with a new CustomPaint widget that draws our line chart.
        chart_container.content = ft.CustomPaint(expand=True, paint=draw_line_chart)
        page.update()


    # ------------------------------------------------
    # Example of how update_chart is called in your app:
    # (Inside your apply_all_filters function, for instance.)
    def apply_all_filters():
        """
        1) Filter the entire global_df
        2) Update chart with the entire filtered dataset
        3) Update table and stats accordingly.
        """
        df_filtered = apply_filters_to_df(global_df)
        update_stats(df_filtered)      # update stats row
        update_chart(df_filtered)      # update the line chart instead of a Plotly chart
        update_table(df_filtered)      # update the log table

    # ... (Rest of your main application code: table, file picker, tailing, etc.) ...

    def main(page: ft.Page):
        global global_df, chart_container
        page.title = "Lazy-load + Tail + Full-data Chart, Partial Table"
        page.bgcolor = DARK_BLUE
        page.theme_mode = ft.ThemeMode.DARK
        page.scroll = "adaptive"
        page.window_resizable = True

        # Setup your global DataFrame for logs.
        global_df = pd.DataFrame()

        # [Your UI setup code...]
        # For example, your stats row, filter fields, data table, etc.
        
        # Create a container for the chart (as defined above) and add it to the "Analytics" tab.
        chart_section = ft.Container(
            bgcolor=FRAME_BG,
            expand=True,
            content=ft.ReactComponent("LogAnalyticsDashboard")
        )
        
        # Create your tabs, one for the log table and one for Analytics.
        table_tab = ft.Tab(
            text="Log Table",
            icon=ft.Icons.VIEW_LIST,
            content=ft.Container(content=data_table, bgcolor=FRAME_BG, expand=True)
        )
        chart_tab = ft.Tab(
            text="Analytics",
            icon=ft.Icons.SHOW_CHART,
            content=chart_section
        )
        tabs_control = ft.Tabs(
            selected_index=0,
            tabs=[table_tab, chart_tab],
            expand=True
        )
        
        # Combine everything in your layout.
        main_col = ft.Column(
            spacing=10,
            expand=True,
            controls=[
                stats_row,
                ft.Divider(color=TEAL_BLUE),
                filter_section,
                ft.Divider(color=TEAL_BLUE),
                tabs_control
            ],
        )
        
        # Optionally, include your navigation panel and wrap the main layout in a Row.
        layout_row = ft.Row(
            controls=[
                ft.Container(expand=True, content=main_col),
                # your navigation panel container
            ],
            expand=True,
            spacing=20,
        )
        
        page.add(layout_row)
        page.update()


    def update_table(df):
        """
        Show only a SUBSET of the entire filtered dataset in the table for performance.
        e.g., the LAST TABLE_PAGE_SIZE rows sorted by timestamp ascending (or descending).
        """
        data_table.rows.clear()
        if df.empty:
            page.snackbar_text = "No logs to display in table."
            page.update()
            return

        # Sort ascending by timestamp
        df_sorted = df.sort_values("timestamp", na_position="first").reset_index(drop=True)

        # We'll show the last TABLE_PAGE_SIZE rows
        # so the user sees the newest lines if we want that.
        row_count = len(df_sorted)
        start_idx = max(0, row_count - TABLE_PAGE_SIZE)
        subset = df_sorted.iloc[start_idx:row_count]

        for _, row in subset.iterrows():
            ts_str = ""
            if pd.notnull(row["timestamp"]):
                ts_str = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            lvl = (row["level"] or "").upper()
            if lvl in ["ERROR","CRITICAL"]:
                bg = DARK_RED
            elif lvl == "WARNING":
                bg = "#3A3F3F"
            else:
                bg = ENTRY_BG

            data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(ts_str, color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(row["level"], color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(row["script"], color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(row["module"], color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(row["funcName"], color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(str(row["lineNo"]) if pd.notnull(row["lineNo"]) else "", color=LIGHT_GRAY)),
                        ft.DataCell(ft.Text(row["message"], color=LIGHT_GRAY)),
                    ],
                    color=bg
                )
            )

        page.update()

    def apply_all_filters():
        """
        1) Filter entire global_df
        2) Update chart with ENTIRE filtered dataset
        3) Show only a subset in the table for performance
        4) Update stats
        """
        df_filtered = apply_filters_to_df(global_df)
        update_stats(df_filtered)      # reflect total count, info, warn, error
        update_chart(df_filtered)      # use entire dataset for the chart
        update_table(df_filtered)      # only partial subset in the table

    # Tailing
    def on_new_tail_line(line):
        parsed = parse_log_line(line)
        if not parsed:
            return
        entry = LogEntry(**parsed)
        row = {
            "timestamp": entry.timestamp,
            "level": entry.level or "UNKNOWN",
            "script": entry.script or "",
            "module": entry.module or "",
            "funcName": entry.funcName or "",
            "lineNo": entry.lineNo,
            "message": entry.message or "",
        }
        def append_line():
            nonlocal global_df
            new_df = pd.DataFrame([row])
            global_df = pd.concat([global_df, new_df], ignore_index=True)
            # Re-filter so table & chart update
            apply_all_filters()
        page.call_later(append_line)

    def start_tail_thread():
        t = threading.Thread(target=tail_file, args=(log_file_path, on_new_tail_line), daemon=True)
        t.start()

    # "Load Older Logs" button
    def load_older_logs_click(e):
        nonlocal older_line_index, global_df
        if not log_file_path:
            page.snackbar_text = "No file loaded."
            page.update()
            return
        if older_line_index <= 0:
            page.snackbar_text = "No more older lines."
            page.update()
            return
        start_line = max(0, older_line_index - CHUNK_SIZE)
        lines = read_lines_in_range(log_file_path, start_line, older_line_index)
        older_line_index = start_line
        if not lines:
            page.snackbar_text = "No older lines found."
            page.update()
            return
        df_part = build_df_from_lines(lines)
        global_df = pd.concat([df_part, global_df], ignore_index=True)
        page.snackbar_text = f"Loaded {len(lines)} older lines."
        page.update()
        apply_all_filters()

    load_older_button.on_click = load_older_logs_click

    # File picker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def file_picker_result(e: ft.FilePickerResultEvent):
        nonlocal log_file_path, older_line_index, global_df
        if e.files:
            log_file_path = e.files[0].path
            total_lines = get_file_line_count(log_file_path)
            older_line_index = total_lines  # start from bottom

            # load the newest chunk
            start_line = max(0, older_line_index - CHUNK_SIZE)
            lines = read_lines_in_range(log_file_path, start_line, older_line_index)
            older_line_index = start_line

            df_part = build_df_from_lines(lines)
            global_df = df_part

            page.snackbar_text = f"Loaded initial {len(lines)} lines from the file."
            page.update()

            # start tail
            start_tail_thread()
            apply_all_filters()

    file_picker.on_result = file_picker_result

    def load_log_file_click(e):
        file_picker.pick_files(allow_multiple=False)
    load_button.on_click = load_log_file_click

    # Reset
    def reset_filters_click(e):
        nonlocal start_datetime, end_datetime
        script_field.value = ""
        module_field.value = ""
        message_field.value = ""
        level_dropdown.value = ""
        quick_filter_dropdown.value = "Custom"
        start_label.value = "Start: Not Set"
        end_label.value = "End: Not Set"
        search_field.value = ""
        start_datetime = None
        end_datetime = None
        page.snackbar_text = "Filters reset."
        page.update()
        apply_all_filters()
    reset_button.on_click = reset_filters_click

    # Export
    def export_logs_click(e):
        df_filtered = apply_filters_to_df(global_df)
        if df_filtered.empty:
            page.snackbar_text = "No logs to export."
            page.update()
            return
        try:
            df_copy = df_filtered.copy()
            df_copy["timestamp"] = df_copy["timestamp"].apply(
                lambda t: t.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(t) else ""
            )
            export_path = "exported_logs.csv"
            df_copy.to_csv(export_path, index=False)
            page.snackbar_text = f"Exported logs to {export_path}."
            page.update()
        except Exception as ex:
            page.snackbar_text = f"Export error: {ex}"
            page.update()
    export_button.on_click = export_logs_click

    # Quick Filter
    def quick_filter_changed(e):
        nonlocal start_datetime, end_datetime
        now = datetime.now()
        if quick_filter_dropdown.value == "Last Hour":
            start_datetime = now - timedelta(hours=1)
            end_datetime = now
        elif quick_filter_dropdown.value == "Last 24 Hours":
            start_datetime = now - timedelta(days=1)
            end_datetime = now
        elif quick_filter_dropdown.value == "Last 7 Days":
            start_datetime = now - timedelta(days=7)
            end_datetime = now
        elif quick_filter_dropdown.value == "Last 30 Days":
            start_datetime = now - timedelta(days=30)
            end_datetime = now
        else:
            start_datetime = None
            end_datetime = None

        if start_datetime and end_datetime:
            start_label.value = f"Start: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
            end_label.value = f"End: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            start_label.value = "Start: Not Set"
            end_label.value = "End: Not Set"

        page.update()
        apply_all_filters()
    quick_filter_dropdown.on_change = quick_filter_changed

    def search_changed(e):
        apply_all_filters()
    search_field.on_change = search_changed

    def apply_filter_button_click(e):
        apply_all_filters()
    apply_filter_button.on_click = apply_filter_button_click

    # Layout
    page.appbar = ft.AppBar(
    bgcolor=FRAME_BG,
    center_title=False,
    title=ft.Row(
        controls=[
            # Placeholder for deepcytes logo; replace this container with ft.Image if you have a logo asset.
            ft.Container(
                width=40,
                height=40,
                bgcolor=LIGHT_GRAY,
                border_radius=8,
                alignment=ft.alignment.center,
                content=ft.Text("Logo", color=FRAME_BG, size=12)
            ),
            ft.Text("Deepcytes", color=TEXT_LIGHT, size=24, weight="bold"),
        ],
        spacing=10,
    ),
    actions=[
        # User profile icon on the right
        ft.IconButton(
            icon=ft.icons.ACCOUNT_CIRCLE,
            icon_color=LIGHT_GRAY,
            tooltip="User Profile"
        )
    ]
)


    top_row = ft.Row([load_button, load_older_button, reset_button, export_button, expand_filters_button])
    time_row = ft.Row([quick_filter_dropdown, ft.Row([start_label, end_label])])
    filter_section = ft.Column(
        spacing=10,
        controls=[
            top_row,
            ft.Row([search_field]),
            time_row,
            advanced_filters_container
        ]
    )

    table_container = ft.Container(
        content=data_table,
        bgcolor=FRAME_BG,
        expand=True
    )
    chart_section = ft.Container(
        bgcolor=FRAME_BG,
        expand=True,
        content=chart_container
    )

    table_tab = ft.Tab(
        text="Log Table",
        icon=ft.icons.VIEW_LIST,
        content=table_container
    )
    chart_tab = ft.Tab(
        text="Analytics",
        icon=ft.icons.SHOW_CHART,
        content=chart_section
    )

    tabs_control = ft.Tabs(
        selected_index=0,
        tabs=[table_tab, chart_tab],
        expand=True
    )

    main_col = ft.Column(
        spacing=10,
        expand=True,
        controls=[
            stats_row,
            ft.Divider(color=TEAL_BLUE),
            filter_section,
            ft.Divider(color=TEAL_BLUE),
            tabs_control
        ],
    )
    

    page.add(main_col)
    page.update()

ft.app(target=main)
