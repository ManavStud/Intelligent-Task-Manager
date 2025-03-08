import flet as ft
import os
from pathlib import Path
import re
import json
import time
import threading
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from collections import deque

# PlotlyChart is available in Flet >= 0.28
from flet.plotly_chart import PlotlyChart

# Constants
MAX_LIVE_LOGS   = 50
TABLE_PAGE_SIZE = 100

##############################################################################
# Utility to read lines from a file
##############################################################################
def read_all_lines(file_path):
    lines = []
    try:
        # Use UTF-8 encoding explicitly for Windows compatibility
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                lines.append(line.rstrip("\n"))
    except UnicodeDecodeError:
        # Fallback to Windows default encoding if UTF-8 fails
        with open(file_path, "r", encoding="cp1252") as f:
            for line in f:
                lines.append(line.rstrip("\n"))
    except Exception as e:
        print("Error reading file:", e)
    return lines

##############################################################################
# JSON Log Parsing (No changes needed here, but included for completeness)
##############################################################################
class LogEntry:
    def __init__(self, timestamp, level, script, module, funcName, lineNo, message, **kwargs):
        try:
            self.timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except:
            self.timestamp = None
        self.level    = level
        self.script   = script
        self.module   = module
        self.funcName = funcName
        self.lineNo   = lineNo
        self.message  = message
        for k, v in kwargs.items():
            setattr(self, k, v)

def parse_log_line(line):
    try:
        data = json.loads(line)
        required = ["timestamp", "level", "script", "module", "funcName", "lineNo", "message"]
        if not all(k in data for k in required):
            return None
        return data
    except:
        return None

def build_df_from_lines(lines):
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

##############################################################################
# Build a logs-per-hour chart with Plotly (No changes needed)
##############################################################################
def build_logs_per_hour_chart(df):
    if df.empty or "timestamp" not in df.columns:
        return px.bar(title="No data")
    df = df.copy()
    df["hour"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:00")
    group = df.groupby("hour").size().reset_index(name="count")
    group = group.sort_values("hour")
    fig = px.bar(
        group,
        x="hour",
        y="count",
        title="Logs per Hour",
        labels={"hour": "Hour", "count": "Count"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        title_font=dict(color="white"),
    )
    return fig

##############################################################################
# create_logs_tab: main function to build the logs UI
##############################################################################
def create_logs_tab(
    base_path,
    glass_bgcolor,
    container_blur,
    container_shadow,
    accent_color,
    background_color,
    card_color,
    text_color
):
    # Shared state
    global_lock = threading.Lock()
    global_df = pd.DataFrame()
    live_logs_buffer = deque([], maxlen=MAX_LIVE_LOGS)
    log_file_path = None

    # Filter state
    start_datetime = None
    end_datetime   = None

    STAT_COLORS = {
        "total":    "#2196F3",
        "info":     "#4CAF50",
        "warnings": "#FFC107",
        "errors":   "#F44336",
    }

    total_count_text = ft.Text("0", color="white", size=20)
    info_count_text  = ft.Text("0", color="white", size=20)
    warn_count_text  = ft.Text("0", color="white", size=20)
    error_count_text = ft.Text("0", color="white", size=20)

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

    def create_stat_card(icon, label, text_widget, bg_color):
        return ft.Container(
            width=150,
            height=80,
            bgcolor=bg_color,
            border_radius=10,
            padding=10,
            content=ft.Row(
                spacing=5,
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Icon(icon, color="white", size=24),
                    ft.Column(
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(label, color="white", size=12),
                            text_widget
                        ]
                    )
                ]
            )
        )

    chart = None

    def create_logs_chart():
        fig = px.bar(title="Logs per Hour")
        return PlotlyChart(fig, expand=True)

    def update_logs_chart(df):
        fig = build_logs_per_hour_chart(df)
        if chart:
            chart.figure = fig

    main_logs_table = ft.DataTable(
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

    def apply_filters(df):
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
        if search_field.value.strip():
            search_txt = search_field.value.strip().lower()
            mask = mask & df["message"].str.lower().str.contains(search_txt)
        return df[mask]

    def update_main_table(df):
        main_logs_table.rows.clear()
        if df.empty:
            return
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")
        if len(df) > TABLE_PAGE_SIZE:
            df = df.iloc[-TABLE_PAGE_SIZE:]
        for _, row_ in df.iterrows():
            ts_str = row_["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row_["timestamp"]) else ""
            lvl    = (row_["level"] or "").upper()
            row_bg = card_color
            if lvl in ["ERROR", "CRITICAL"]:
                row_bg = "#B22222"
            elif lvl == "WARNING":
                row_bg = "#3A3F3F"
            main_logs_table.rows.append(
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
        df_live_filtered = apply_filters(df_live)
        if df_live_filtered.empty:
            return
        if "timestamp" in df_live_filtered.columns:
            df_live_filtered = df_live_filtered.sort_values("timestamp")
        for _, row_ in df_live_filtered.iterrows():
            ts_str = row_["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row_["timestamp"]) else ""
            lvl    = (row_["level"] or "").upper()
            row_bg = card_color
            if lvl in ["ERROR", "CRITICAL"]:
                row_bg = "#B22222"
            elif lvl == "WARNING":
                row_bg = "#3A3F3F"
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
        df_filtered = apply_filters(df_copy)
        update_stats(df_filtered)
        update_main_table(df_filtered)
        update_live_logs_table()
        update_logs_chart(df_filtered)

    search_field = ft.TextField(label="Search in Messages", hint_text="Search text...", width=250, color=text_color, border_color=accent_color)
    script_field = ft.TextField(label="Script", width=150, color=text_color, border_color=accent_color)
    module_field = ft.TextField(label="Module", width=150, color=text_color, border_color=accent_color)
    message_field= ft.TextField(label="Message (Regex)", width=200, color=text_color, border_color=accent_color)
    level_dropdown=ft.Dropdown(
        label="Level",
        options=[ft.dropdown.Option(x) for x in ["", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]],
        value="",
        width=150,
        color=text_color,
        border_color=accent_color
    )
    time_filter_dd = ft.Dropdown(
        label="Time Filter",
        options=[
            ft.dropdown.Option("Custom"),
            ft.dropdown.Option("Last Hour"),
            ft.dropdown.Option("Last 24 Hours"),
            ft.dropdown.Option("Last 7 Days"),
            ft.dropdown.Option("Last 30 Days"),
        ],
        value="Custom",
        width=150,
        color=text_color,
        border_color=accent_color
    )
    start_label = ft.Text("Start: Not Set", color=text_color)
    end_label   = ft.Text("End: Not Set",   color=text_color)

    load_button  = ft.ElevatedButton("Load File", bgcolor=accent_color, color="white")
    reset_button = ft.ElevatedButton("Reset",     bgcolor=accent_color, color="white")
    export_button= ft.ElevatedButton("Export",    bgcolor=accent_color, color="white")
    apply_button = ft.ElevatedButton("Apply",     bgcolor=accent_color, color="white")

    file_picker = ft.FilePicker()

    def file_picker_result(e: ft.FilePickerResultEvent):
        nonlocal log_file_path, global_df
        if e.files:
            # Normalize path for Windows
            log_file_path = str(Path(e.files[0].path))
            lines = read_all_lines(log_file_path)
            df_part = build_df_from_lines(lines)
            with global_lock:
                global_df = df_part
            apply_all_filters()

    file_picker.on_result = file_picker_result

    def load_file_click(e):
        file_picker.pick_files(allow_multiple=False)

    def reset_click(e):
        nonlocal start_datetime, end_datetime
        start_datetime = None
        end_datetime   = None
        script_field.value  = ""
        module_field.value  = ""
        message_field.value = ""
        level_dropdown.value= ""
        time_filter_dd.value= "Custom"
        start_label.value   = "Start: Not Set"
        end_label.value     = "End: Not Set"
        search_field.value  = ""
        script_field.update()
        module_field.update()
        message_field.update()
        level_dropdown.update()
        time_filter_dd.update()
        start_label.update()
        end_label.update()
        search_field.update()
        apply_all_filters()

    def export_click(e):
        with global_lock:
            df_copy = global_df.copy()
        df_filtered = apply_filters(df_copy)
        if df_filtered.empty:
            print("No logs to export.")
            return
        try:
            df_filtered["timestamp"] = df_filtered["timestamp"].apply(lambda t: t.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(t) else "")
            # Use Windows-friendly path
            out_path = str(Path("exported_logs.csv"))
            df_filtered.to_csv(out_path, index=False, encoding="utf-8-sig")  # UTF-8 with BOM for Windows Excel
            print(f"Exported logs to {out_path}.")
        except Exception as ex:
            print("Export error:", ex)

    def apply_filter_click(e):
        apply_all_filters()

    def time_filter_changed(e):
        nonlocal start_datetime, end_datetime
        now = datetime.now()
        val = time_filter_dd.value
        if val == "Last Hour":
            start_datetime = now - timedelta(hours=1)
            end_datetime   = now
        elif val == "Last 24 Hours":
            start_datetime = now - timedelta(days=1)
            end_datetime   = now
        elif val == "Last 7 Days":
            start_datetime = now - timedelta(days=7)
            end_datetime   = now
        elif val == "Last 30 Days":
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
        apply_all_filters()

    stats_row = ft.Row(
        spacing=10,
        controls=[
            create_stat_card(ft.Icons.LIST,     "Total Logs", total_count_text, STAT_COLORS["total"]),
            create_stat_card(ft.Icons.INFO,     "Infos",      info_count_text,  STAT_COLORS["info"]),
            create_stat_card(ft.Icons.WARNING,  "Warnings",   warn_count_text,  STAT_COLORS["warnings"]),
            create_stat_card(ft.Icons.ERROR,    "Errors",     error_count_text, STAT_COLORS["errors"]),
        ]
    )

    stats_container = ft.Container(
        content=stats_row,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10
    )
    top_controls_container = ft.Container(
        content=ft.Row([load_button, reset_button, export_button], spacing=10),
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10
    )
    filter_controls_container = ft.Container(
        content=ft.Row([search_field, time_filter_dd, apply_button], spacing=10),
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10
    )
    date_labels_container = ft.Container(
        content=ft.Row([start_label, end_label], spacing=20),
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10
    )
    advanced_filters_container = ft.Container(
        content=ft.Row([script_field, module_field, message_field, level_dropdown], spacing=10),
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10
    )

    top_left_col = ft.Column(
        spacing=10,
        controls=[
            top_controls_container,
            stats_container,
            filter_controls_container,
            date_labels_container,
            advanced_filters_container,
        ],
    )

    chart = create_logs_chart()
    chart_container = ft.Container(
        content=chart,
        bgcolor=glass_bgcolor,
        blur=container_blur,
        shadow=container_shadow,
        border_radius=10,
        padding=10,
        width=750,
        height=400,
    )
    top_row = ft.Row(
        spacing=10,
        controls=[
            ft.Container(content=top_left_col, expand=True),
            ft.Container(content=chart_container, expand=False),
        ],
        expand=False
    )

    main_tab = ft.Tab(
        text="Log Table",
        icon=ft.icons.VIEW_LIST,
        content=ft.Container(
            content=ft.ListView(
                controls=[main_logs_table],
                expand=True,  # Expand to fill the container
                auto_scroll=False,  # Optional: Set to True if you want to auto-scroll to the bottom
            ),
            bgcolor=glass_bgcolor,
            blur=container_blur,
            shadow=container_shadow,
            border_radius=10,
            expand=True,
            padding=10,  # Add padding inside the container
        )
    )
    live_tab = ft.Tab(
        text="Live Logs",
        icon=ft.icons.LIVE_TV,
        content=ft.Container(
            content=ft.ListView(
                controls=[live_logs_table],
                expand=True,  # Expand to fill the container
                auto_scroll=True,  # Auto-scroll to bottom for live logs
            ),
            bgcolor=glass_bgcolor,
            blur=container_blur,
            shadow=container_shadow,
            border_radius=10,
            expand=True,
            padding=10,  # Add padding inside the container
        )
    )
    logs_tabs = ft.Tabs(
        tabs=[main_tab, live_tab],
        selected_index=0,
        expand=True
    )
    bottom_container = ft.Container(
        content=logs_tabs,
        expand=True
    )

    main_col = ft.Column(
        spacing=10,
        controls=[
            top_row,
            bottom_container
        ],
        expand=True
    )

    layout = ft.Container(
        content=main_col,
        expand=True,
        bgcolor=None,
        margin=ft.margin.only(left=15)
    )

    def refresh_live_logs_loop():
        nonlocal log_file_path
        while True:
            time.sleep(3)
            if log_file_path:
                lines = read_all_lines(log_file_path)
                last_50 = lines[-MAX_LIVE_LOGS:] if len(lines) >= MAX_LIVE_LOGS else lines
                with global_lock:
                    live_logs_buffer.clear()
                    live_logs_buffer.extend(last_50)
                if layout.page:
                    layout.page.run_thread_safe(_update_live_logs)

    def _update_live_logs():
        with global_lock:
            lines = list(live_logs_buffer)
        df_live = build_df_from_lines(lines)
        df_live_filtered = apply_filters(df_live)
        update_live_logs_table()
        update_logs_chart(df_live_filtered)
        layout.page.update()

    def init_logs_tab(page: ft.Page):
        page.overlay.append(file_picker)
        t = threading.Thread(target=refresh_live_logs_loop, daemon=True)
        t.start()
        page.update()

    load_button.on_click = load_file_click
    reset_button.on_click = reset_click
    export_button.on_click = export_click
    apply_button.on_click = apply_filter_click
    time_filter_dd.on_change = time_filter_changed

    return layout, init_logs_tab

# Example usage (add this to test the code)
if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Logs Viewer"
        layout, init_func = create_logs_tab(
            base_path=".",
            glass_bgcolor="#2A2A2A",
            container_blur=ft.Blur(10, 10),
            container_shadow=ft.BoxShadow(blur_radius=10, color="#55000000"),
            accent_color="#FF5722",
            background_color="#212121",
            card_color="#424242",
            text_color="white"
        )
        page.add(layout)
        init_func(page)

    ft.app(target=main)
