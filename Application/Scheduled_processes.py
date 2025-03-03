import flet as ft
from flet import BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur
from flet.plotly_chart import PlotlyChart  # Requires Flet 0.28+
import plotly.graph_objects as go
import psutil
import asyncio
import threading
import os

#####################################
# 1) Periodic Task Management
#####################################
async def periodic_update(page: ft.Page, app: "SystemDistributionApp"):
    """Runs in a background thread, fetching data and updating the UI every 5 seconds."""
    while True:
        tasks = fetch_realtime_tasks()
        app.update_task_table(tasks)
        app.update_statistics_chart(tasks)
        page.update()
        await asyncio.sleep(5)

def start_realtime_updates(page: ft.Page, app: "SystemDistributionApp"):
    """
    Starts the periodic update in a separate event loop so it doesn't block the main thread.
    Call this after you've added the returned layout to your main page.
    """
    new_loop = asyncio.new_event_loop()
    new_loop.create_task(periodic_update(page, app))
    t = threading.Thread(target=_run_loop, args=(new_loop,), daemon=True)
    t.start()

def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def fetch_realtime_tasks():
    """
    Returns a list of tasks, each with status="System" or "Non-System"
    based on the process username. We'll rely on psutil to get 'username'.
    """
    tasks = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            info = proc.info
            user = info.get('username', None)
            if user is None:
                status = "System"
            elif "SYSTEM" in user.upper() or user.lower() == "root":
                status = "System"
            else:
                status = "Non-System"
            
            tasks.append({
                "name": info['name'] or "Unknown",
                "next_run": "N/A",
                "status": status,
                "start_time": "N/A",
                "duration": "N/A",
                "first_scheduled": f"PID: {info['pid']}",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return tasks

#####################################
# 2) Build a Chart from Tasks
#####################################
def build_status_chart(tasks):
    """
    Returns a Plotly pie chart figure showing how many tasks are "System" vs "Non-System".
    """
    status_counts = {}
    for t in tasks:
        st = t["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

    labels = list(status_counts.keys())
    values = list(status_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                hoverinfo="label+percent+value",
                textinfo="percent",
                textfont=dict(size=16, color="white")
            )
        ]
    )
    fig.update_layout(
        title={
            'text': "System vs. Non-System Processes",
            'font': {'size': 24, 'color': 'white'}  # Larger title font
            },
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(size=24, color="white"))  # Increase legend font size if desired
    )
    return fig

#####################################
# 3) SystemDistributionApp Class
#####################################
class SystemDistributionApp:
    def __init__(self, glass_bgcolor, container_blur, container_shadow, bg_image_path=None):
        self.glass_bgcolor = glass_bgcolor
        self.container_blur = container_blur
        self.container_shadow = container_shadow
        self.bg_image_path = bg_image_path or ""

        self.data_rows_container = None
        self.stats_chart = None

    def create_task_table(self):
        header_row = ft.Row(
            controls=[
                ft.Container(content=ft.Text("Task Name", color="white", weight=ft.FontWeight.BOLD, size=12), width=180),
                ft.Container(content=ft.Text("Next Run Time", color="white", weight=ft.FontWeight.BOLD, size=12), width=150),
                ft.Container(content=ft.Text("Status", color="white", weight=ft.FontWeight.BOLD, size=12), width=100),
                ft.Container(content=ft.Text("Start Time", color="white", weight=ft.FontWeight.BOLD, size=12), width=150),
                ft.Container(content=ft.Text("Duration", color="white", weight=ft.FontWeight.BOLD, size=12), width=100),
                ft.Container(content=ft.Text("First Scheduled", color="white", weight=ft.FontWeight.BOLD, size=12), width=150),
            ],
            spacing=10,
        )
        table_header = ft.Container(
            content=header_row,
            padding=10,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
        )

        self.data_rows_container = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        table_data = ft.Container(
            content=self.data_rows_container,
            expand=True,
            border_radius=ft.border_radius.only(bottom_left=5, bottom_right=5),
            padding=ft.padding.only(right=10),
        )

        return ft.Container(
            content=ft.Column(
                controls=[table_header, table_data],
                spacing=0,
                expand=True,
            ),
            bgcolor=self.glass_bgcolor,
            blur=Blur(2, 2, BlurTileMode.REPEATED),
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            expand=True,
        )

    def create_data_row(self, task):
        status_colors = {
            "System": "#90caf9",
            "Non-System": "#a5d6a7",
        }
        status_color = status_colors.get(task["status"], "white")

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(content=ft.Text(task["name"], color="white", size=12), width=180),
                    ft.Container(content=ft.Text(task["next_run"], color="white", size=12), width=150),
                    ft.Container(content=ft.Text(task["status"], color=status_color, size=12), width=100),
                    ft.Container(content=ft.Text(task["start_time"], color="white", size=12), width=150),
                    ft.Container(content=ft.Text(task["duration"], color="white", size=12), width=100),
                    ft.Container(content=ft.Text(task["first_scheduled"], color="white", size=12), width=150),
                ],
                spacing=10,
            ),
            padding=10,
            border_radius=5,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
        )

    def update_task_table(self, tasks):
        new_data_rows = [self.create_data_row(t) for t in tasks]
        if self.data_rows_container:
            self.data_rows_container.controls = new_data_rows

    def create_statistics_chart(self):
        fig = go.Figure()
        fig.update_layout(
            title="System vs. Non-System Processes",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        self.stats_chart = PlotlyChart(fig, expand=True)
        return self.stats_chart

    def update_statistics_chart(self, tasks):
        fig = build_status_chart(tasks)
        if self.stats_chart:
            self.stats_chart.figure = fig

    def build_layout(self):
        """
        Builds and returns a container that holds the table on the left
        and the donut chart on the right.
        """
        # Main panel (table)
        table_container = self.create_task_table()
        main_panel = ft.Container(
            expand=2,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            margin=ft.margin.all(10),
            padding=20,
            content=table_container
        )

        # Right panel (stats)
        stats_chart_control = self.create_statistics_chart()
        right_panel = ft.Container(
            expand=1,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            margin=ft.margin.all(10),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("Statistics", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    stats_chart_control,
                ],
                spacing=20,
                expand=True
            ),
        )

        # Combined row
        row = ft.Row(
            controls=[main_panel, right_panel],
            spacing=10,
            expand=True
        )

        # Optionally add a background image
        if self.bg_image_path:
            background = ft.Container(
                expand=True,
                image_src=self.bg_image_path,
                image_fit=ft.ImageFit.COVER,
            )
            return ft.Stack(
                controls=[
                    background,
                    ft.Container(expand=True, content=row)
                ],
                expand=True
            )
        else:
            return ft.Container(
                expand=True,
                content=row
            )

#####################################
# 4) Create a function to return layout
#####################################
def create_system_distribution_layout(glass_bgcolor, container_blur, container_shadow, bg_image_path=None):
    """
    Creates the "system vs. non-system" distribution layout.
    Returns (layout, app_instance).
    """
    app = SystemDistributionApp(glass_bgcolor, container_blur, container_shadow, bg_image_path)
    layout = app.build_layout()
    return layout, app