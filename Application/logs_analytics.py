import flet as ft
import json
import os
import re
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
from collections import deque
import plotly.express as px
from flet_webview import WebView

# Table and logs constants
TABLE_PAGE_SIZE = 100
MAX_LIVE_LOGS   = 50

def get_file_line_count(file_path):
    count = 0
    try:
        with open(file_path, "r") as f:
            for _ in f:
                count += 1
    except Exception as e:
        print("Error counting file lines:", e)
    return count

def read_all_lines(file_path):
    lines = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                lines.append(line.rstrip("\n"))
    except Exception as e:
        print("Error reading file:", e)
    return lines

class LogEntry:
    def __init__(self, timestamp, level, script, module, funcName, lineNo, message, **kwargs):
        try:
            self.timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            self.timestamp = None
        self.level    = level
        self.script   = script
        self.module   = module
        self.funcName = funcName
        self.lineNo   = lineNo
        self.message  = message
        for key, value in kwargs.items():
            setattr(self, key, value)

def parse_log_line(json_line):
    """
    Expects JSON lines with keys:
      timestamp, level, script, module, funcName, lineNo, message
    Returns a dict or None if invalid.
    """
    try:
        data = json.loads(json_line)
        required = ["timestamp", "level", "script", "module", "funcName", "lineNo", "message"]
        if not all(k in data for k in required):
            return None
        return data
    except:
        return None

def build_df_from_lines(lines):
    """
    Convert lines of JSON logs into a DataFrame with columns:
      [timestamp, level, script, module, funcName, lineNo, message]
    """
    rows = []
    for ln in lines:
        parsed = parse_log_line(ln)
        if not parsed:
            continue
        entry = LogEntry(**parsed)
        rows.append({
            "timestamp": entry.timestamp,
            "level":     entry.level or "UNKNOWN",
            "script":    entry.script or "",
            "module":    entry.module or "",
            "funcName":  entry.funcName or "",
            "lineNo":    entry.lineNo,
            "message":   entry.message or "",
        })
    return pd.DataFrame(rows)

def build_small_chart(df, text_color):
    """
    Builds a small bar chart (Plotly) of logs per hour.
    If df is empty, returns a simple "No data" text in the same color.
    """
    if df.empty:
        return ft.Text("No data", color=text_color)

    df["timestamp_hour"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:00")
    group = df.groupby("timestamp_hour").size().reset_index(name="count")
    group = group.sort_values("timestamp_hour")

    fig = px.bar(
        group,
        x="timestamp_hour",
        y="count",
        title="Logs per Hour",
        labels={"timestamp_hour": "Hour", "count": "Count"}
    )
    html_str = fig.to_html(include_plotlyjs="cdn", full_html=False)
    return WebView(html=html_str, width=350, height=300)

def create_logs_analytics_layout(
    # Required parameters from your main page:
    base_path,
    glass_bgcolor,
    container_blur,
    container_shadow,
    accent_color,
    # Color scheme (all text = text_color)
    background_color,
    card_color,
    text_color
):
    """
    Creates the logs analytics UI, using the color scheme from the main page.
    All text is set to `text_color`. No other overrides.

    Example usage:
        layout, init_fn = create_logs_analytics_layout(
            base_path=self.base_path,
            glass_bgcolor=self.glass_bgcolor,
            container_blur=self.container_blur,
            container_shadow=self.container_shadow,
            accent_color=self.accent_color,
            background_color="#0B0F19",
            card_color="#112240",
            text_color="#FFFFFF",
        )
    Then:
        page.add(layout)
        init_fn(page)
    """

    global_lock = threading.Lock()
    global_df = pd.DataFrame()
    live_logs_buffer = deque([], maxlen=MAX_LIVE_LOGS)
    log_file_path = None

    # Row backgrounds for errors or warnings
    ERROR_ROW_BG   = "#B22222"
    WARNING_ROW_BG = "#3A3F3F"

    # Filter state
    start_datetime = None
    end_datetime   = None

    # Stats text
    total_count_text = ft.Text("0", color=text_color, size=20)
    info_count_text  = ft.Text("0", color=text_color, size=20)
    warn_count_text  = ft.Text("0", color=text_color, size=20)
    error_count_text = ft.Text("0", color=text_color, size=20)

    def update_stats(df):
        if df.empty:
            total_count_text.value = "0"
            info_count_text.value  = "0"
            warn_count_text.value  = "0"
            error_count_text.value = "0"
        else:
            total_count  = len(df)
            info_count   = len(df[df["level"].str.upper() == "INFO"])
            warn_count   = len(df[df["level"].str.upper() == "WARNING"])
            error_count  = len(df[df["level"].str.upper().isin(["ERROR", "CRITICAL"])])
            total_count_text.value = str(total_count)
            info_count_text.value  = str(info_count)
            warn_count_text.value  = str(warn_count)
            error_count_text.value = str(error_count)

    def make_stat_card(title, value_widget, icon_name):
        return ft.Container(
            width=180,
            height=100,
            bgcolor=card_color,
            border_radius=8,
            padding=10,
            content=ft.Row(
                controls=[
                    ft.Icon(name=icon_name, color=accent_color, size=30),
                    ft.Column(
                        spacing=3,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(title, color=text_color, size=14),
                            value_widget,
                        ],
                    )
                ],
                alignment=ft.MainAxisAlignment.START
            ),
        )

    stats_row = ft.Row(
        controls=[
            make_stat_card("Total Logs", total_count_text, ft.Icons.LIST),
            make_stat_card("Infos",      info_count_text,  ft.Icons.INFO),
            make_stat_card("Warnings",   warn_count_text,  ft.Icons.WARNING),
            make_stat_card("Errors",     error_count_text, ft.Icons.ERROR),
        ],
        alignment="start",
    )

    small_chart_container = ft.Container(
        width=350,
        height=300,
        bgcolor=card_color,
        alignment=ft.alignment.top_center,
        content=ft.Text("No data", color=text_color)
    )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Timestamp", color=text_color)),
            ft.DataColumn(ft.Text("Level",     color=text_color)),
            ft.DataColumn(ft.Text("Script",    color=text_color)),
            ft.DataColumn(ft.Text("Module",    color=text_color)),
            ft.DataColumn(ft.Text("Function",  color=text_color)),
            ft.DataColumn(ft.Text("Line No",   color=text_color)),
            ft.DataColumn(ft.Text("Message",   color=text_color)),
        ],
        rows=[],
        border=ft.border.all(1, accent_color),
        heading_row_height=30,
        data_row_min_height=30,
        width=1000,
    )

    live_logs_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Timestamp", color=text_color)),
            ft.DataColumn(ft.Text("Level",     color=text_color)),
            ft.DataColumn(ft.Text("Script",    color=text_color)),
            ft.DataColumn(ft.Text("Module",    color=text_color)),
            ft.DataColumn(ft.Text("Function",  color=text_color)),
            ft.DataColumn(ft.Text("Line No",   color=text_color)),
            ft.DataColumn(ft.Text("Message",   color=text_color)),
        ],
        rows=[],
        border=ft.border.all(1, accent_color),
        heading_row_height=30,
        data_row_min_height=30,
        width=1000,
    )

    # ------------- Utility functions -------------
    def apply_filters_to_df(df):
        if df.empty:
            return df
        mask = pd.Series([True]*len(df), index=df.index)

        if start_datetime and end_datetime:
            mask = mask & (df["timestamp"] >= start_datetime) & (df["timestamp"] <= end_datetime)

        if script_field.value.strip():
            s_lower = script_field.value.strip().lower()
            mask = mask & (df["script"].str.lower() == s_lower)

        if module_field.value.strip():
            m_lower = module_field.value.strip().lower()
            mask = mask & (df["module"].str.lower() == m_lower)

        if message_field.value.strip():
            try:
                pattern = re.compile(message_field.value.strip(), re.IGNORECASE)
                mask = mask & df["message"].apply(lambda x: bool(pattern.search(x)))
            except:
                return pd.DataFrame([])

        if level_dropdown.value.strip():
            lvl_lower = level_dropdown.value.strip().lower()
            mask = mask & (df["level"].str.lower() == lvl_lower)

        search_txt = search_field.value.strip().lower()
        if search_txt:
            mask = mask & df["message"].str.lower().str.contains(search_txt)

        return df[mask]

    def update_small_chart():
        with global_lock:
            df_copy = global_df.copy()
        df_filtered = apply_filters_to_df(df_copy)
        if df_filtered.empty or "timestamp" not in df_filtered.columns:
            small_chart_container.content = ft.Text("No data", color=text_color)
        else:
            df_valid = df_filtered.dropna(subset=["timestamp"])
            small_chart_container.content = build_small_chart(df_valid, text_color)
        small_chart_container.update()

    def update_table(df):
        data_table.rows.clear()
        if df.empty:
            data_table.rows = []
        else:
            df_sorted = df.sort_values("timestamp", na_position="first").reset_index(drop=True)
            row_count = len(df_sorted)
            start_idx = max(0, row_count - TABLE_PAGE_SIZE)
            subset = df_sorted.iloc[start_idx:row_count]
            for _, row_ in subset.iterrows():
                ts_str = row_["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row_["timestamp"]) else ""
                lvl    = (row_["level"] or "").upper()

                if lvl in ["ERROR", "CRITICAL"]:
                    row_bg = ERROR_ROW_BG
                elif lvl == "WARNING":
                    row_bg = WARNING_ROW_BG
                else:
                    row_bg = card_color

                data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(ts_str, color=text_color)),
                            ft.DataCell(ft.Text(row_["level"], color=text_color)),
                            ft.DataCell(ft.Text(row_["script"], color=text_color)),
                            ft.DataCell(ft.Text(row_["module"], color=text_color)),
                            ft.DataCell(ft.Text(row_["funcName"], color=text_color)),
                            ft.DataCell(ft.Text(str(row_["lineNo"]) if pd.notnull(row_["lineNo"]) else "", color=text_color)),
                            ft.DataCell(ft.Text(row_["message"], color=text_color)),
                        ],
                        color=row_bg
                    )
                )

    def update_live_logs_table():
        live_logs_table.rows.clear()
        with global_lock:
            lines = list(live_logs_buffer)
        df_live = build_df_from_lines(lines)
        df_live_filtered = apply_filters_to_df(df_live)
        if not df_live_filtered.empty:
            for _, row_ in df_live_filtered.iterrows():
                ts_str = row_["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row_["timestamp"]) else ""
                lvl    = (row_["level"] or "").upper()

                if lvl in ["ERROR", "CRITICAL"]:
                    row_bg = ERROR_ROW_BG
                elif lvl == "WARNING":
                    row_bg = WARNING_ROW_BG
                else:
                    row_bg = card_color

                live_logs_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(ts_str, color=text_color)),
                            ft.DataCell(ft.Text(row_["level"], color=text_color)),
                            ft.DataCell(ft.Text(row_["script"], color=text_color)),
                            ft.DataCell(ft.Text(row_["module"], color=text_color)),
                            ft.DataCell(ft.Text(row_["funcName"], color=text_color)),
                            ft.DataCell(ft.Text(str(row_["lineNo"]) if pd.notnull(row_["lineNo"]) else "", color=text_color)),
                            ft.DataCell(ft.Text(row_["message"], color=text_color)),
                        ],
                        color=row_bg
                    )
                )

    def apply_all_filters():
        with global_lock:
            df_copy = global_df.copy()
        df_filtered = apply_filters_to_df(df_copy)
        update_stats(df_filtered)
        update_table(df_filtered)
        update_live_logs_table()
        update_small_chart()

    # ------------- Buttons / Fields -------------
    load_button = ft.ElevatedButton("Load File", icon=ft.Icons.UPLOAD_FILE, bgcolor=accent_color, color=text_color)
    reset_button= ft.ElevatedButton("Reset",     icon=ft.Icons.RESTART_ALT, bgcolor=accent_color, color=text_color)
    export_button=ft.ElevatedButton("Export",    icon=ft.Icons.DOWNLOAD,    bgcolor=accent_color, color=text_color)

    search_field = ft.TextField(
        label="Search in Messages",
        hint_text="Type to filter by text...",
        width=300,
        border_color=accent_color,
        color=text_color
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
        border_color=accent_color,
        color=text_color
    )
    start_label = ft.Text("Start: Not Set", color=text_color)
    end_label   = ft.Text("End: Not Set",   color=text_color)

    script_field = ft.TextField(
        label="Script Name",
        hint_text="Enter script...",
        width=200,
        border_color=accent_color,
        color=text_color
    )
    module_field = ft.TextField(
        label="Module Name",
        hint_text="Enter module...",
        width=200,
        border_color=accent_color,
        color=text_color
    )
    message_field= ft.TextField(
        label="Message (Regex)",
        hint_text="Enter regex...",
        width=300,
        border_color=accent_color,
        color=text_color
    )
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
        border_color=accent_color,
        color=text_color
    )
    apply_filter_button = ft.ElevatedButton("Apply", bgcolor=accent_color, color=text_color, icon=ft.Icons.FILTER_LIST)

    advanced_filters_container = ft.Column(visible=False, controls=[
        ft.Row([script_field, module_field, message_field, level_dropdown])
    ])
    expand_filters_button = ft.IconButton(icon=ft.Icons.ARROW_DROP_DOWN, icon_color=text_color, tooltip="Show Advanced Filters")

    def toggle_advanced_filters(e):
        advanced_filters_container.visible = not advanced_filters_container.visible
        if advanced_filters_container.visible:
            expand_filters_button.icon = ft.Icons.ARROW_DROP_UP
            expand_filters_button.tooltip = "Hide Advanced Filters"
        else:
            expand_filters_button.icon = ft.Icons.ARROW_DROP_DOWN
            expand_filters_button.tooltip = "Show Advanced Filters"
        expand_filters_button.update()
        advanced_filters_container.update()

    expand_filters_button.on_click = toggle_advanced_filters

    file_picker = ft.FilePicker()
    def file_picker_result(e: ft.FilePickerResultEvent):
        nonlocal log_file_path, global_df
        if e.files:
            log_file_path = e.files[0].path
            lines = read_all_lines(log_file_path)
            df_part = build_df_from_lines(lines)
            with global_lock:
                global_df = df_part
            apply_all_filters()
    file_picker.on_result = file_picker_result

    def load_button_click(e):
        file_picker.pick_files(allow_multiple=False)
    load_button.on_click = load_button_click

    def reset_filters_click(e):
        nonlocal start_datetime, end_datetime
        script_field.value  = ""
        module_field.value  = ""
        message_field.value = ""
        level_dropdown.value= ""
        quick_filter_dropdown.value = "Custom"
        start_label.value   = "Start: Not Set"
        end_label.value     = "End: Not Set"
        search_field.value  = ""
        start_datetime      = None
        end_datetime        = None

        script_field.update()
        module_field.update()
        message_field.update()
        level_dropdown.update()
        quick_filter_dropdown.update()
        start_label.update()
        end_label.update()
        search_field.update()

        apply_all_filters()
    reset_button.on_click = reset_filters_click

    def export_logs_click(e):
        with global_lock:
            df_copy = global_df.copy()
        df_filtered = apply_filters_to_df(df_copy)
        if df_filtered.empty:
            print("No logs to export.")
            return
        try:
            df_copy = df_filtered.copy()
            df_copy["timestamp"] = df_copy["timestamp"].apply(lambda t: t.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(t) else "")
            export_path = "exported_logs.csv"
            df_copy.to_csv(export_path, index=False)
            print(f"Exported logs to {export_path}.")
        except Exception as ex:
            print(f"Export error: {ex}")
    export_button.on_click = export_logs_click

    def apply_filter_button_click(e):
        apply_all_filters()
    apply_filter_button.on_click = apply_filter_button_click

    def quick_filter_changed(e):
        nonlocal start_datetime, end_datetime
        now = datetime.now()
        if quick_filter_dropdown.value == "Last Hour":
            start_datetime = now - timedelta(hours=1)
            end_datetime   = now
        elif quick_filter_dropdown.value == "Last 24 Hours":
            start_datetime = now - timedelta(days=1)
            end_datetime   = now
        elif quick_filter_dropdown.value == "Last 7 Days":
            start_datetime = now - timedelta(days=7)
            end_datetime   = now
        elif quick_filter_dropdown.value == "Last 30 Days":
            start_datetime = now - timedelta(days=30)
            end_datetime   = now
        else:
            start_datetime = None
            end_datetime   = None

        if start_datetime and end_datetime:
            start_label.value = f"Start: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
            end_label.value   = f"End: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            start_label.value = "Start: Not Set"
            end_label.value   = "End: Not Set"

        start_label.update()
        end_label.update()
        apply_all_filters()
    quick_filter_dropdown.on_change = quick_filter_changed
    search_field.on_change = lambda e: apply_all_filters()

    # Layout top row: stats + filters
    left_column = ft.Column(
        spacing=10,
        controls=[
            ft.Row([load_button, reset_button, export_button, expand_filters_button]),
            stats_row,
            ft.Row([search_field, quick_filter_dropdown, apply_filter_button]),
            ft.Row([start_label, end_label]),
            advanced_filters_container,
        ]
    )
    top_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            left_column,
            ft.Container(width=30),
            ft.Column([small_chart_container], alignment=ft.MainAxisAlignment.START)
        ]
    )

    table_tab = ft.Tab(
        text="Log Table",
        icon=ft.Icons.VIEW_LIST,
        content=ft.Container(
            content=data_table,
            bgcolor=card_color,
            expand=True,
            blur=container_blur,
            shadow=container_shadow
        )
    )
    live_logs_tab = ft.Tab(
        text="Live Logs",
        icon=ft.Icons.LIVE_TV,
        content=ft.Container(
            content=live_logs_table,
            bgcolor=card_color,
            expand=True,
            blur=container_blur,
            shadow=container_shadow
        )
    )
    tabs_control = ft.Tabs(
        selected_index=0,
        tabs=[table_tab, live_logs_tab],
        expand=True
    )

    main_col = ft.Column(
        spacing=10,
        expand=True,
        controls=[
            top_row,
            ft.Divider(color=accent_color),
            tabs_control
        ],
    )

    layout = ft.Container(
        content=main_col,
        expand=True,
        bgcolor=background_color  # Must be passed from the main page
    )

    # Use a normal background thread for live logs
    def refresh_live_logs_loop():
        nonlocal log_file_path
        while True:
            time.sleep(3)
            if log_file_path:
                try:
                    lines = read_all_lines(log_file_path)
                    last_50 = lines[-50:] if len(lines) >= 50 else lines
                    with global_lock:
                        live_logs_buffer.clear()
                        live_logs_buffer.extend(last_50)
                    update_live_logs_table()
                    update_small_chart()
                except Exception as ex:
                    print("Error refreshing live logs:", ex)

    def init_logs_analytics(page: ft.Page):
        """
        Attach the file picker, start the background logs thread, do initial UI update.
        """
        page.overlay.append(file_picker)
        t = threading.Thread(target=refresh_live_logs_loop, daemon=True)
        t.start()
        page.update()

    return layout, init_logs_analytics