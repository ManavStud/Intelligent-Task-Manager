import flet as ft
from flet import BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur
from flet.plotly_chart import PlotlyChart  # Requires Flet 0.28+
import plotly.graph_objects as go
import psutil
import asyncio
import threading
from pathlib import Path
from collections import Counter
import time

#####################################
# 1) Periodic Task Management
#####################################
async def periodic_update(page: ft.Page, app: "SystemDistributionApp"):
    """Runs in a background thread, fetching data and updating the UI every 10 seconds."""
    while True:
        start_time = time.time()
        tasks = fetch_realtime_tasks()
        app.update_task_table(tasks)
        app.update_statistics_chart(tasks)
        page.update()
        elapsed = time.time() - start_time
        # Adjust sleep time to maintain a consistent 10-second interval
        await asyncio.sleep(max(10 - elapsed, 1))  # Minimum 1s sleep to avoid tight loops

def start_realtime_updates(page: ft.Page, app: "SystemDistributionApp"):
    """
    Starts the periodic update in a separate event loop.
    """
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.create_task(periodic_update(page, app))
    t = threading.Thread(target=new_loop.run_forever, daemon=True)
    t.start()

def fetch_realtime_tasks():
    """
    Efficiently fetches process data with minimal attributes.
    Returns a list of tasks with "System" or "Non-System" status.
    """
    tasks = []
    # Limit attributes to reduce memory and CPU usage
    for proc in psutil.process_iter(['pid', 'name', 'username'], ad_value=None):
        try:
            info = proc.info
            user = info.get('username', '').upper()
            # Windows-specific SYSTEM users: NT AUTHORITY\SYSTEM, etc.
            is_system = user in (None, '', 'SYSTEM', 'NT AUTHORITY\\SYSTEM', 'ROOT')
            status = "System" if is_system else "Non-System"
            
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
    # Limit to 100 tasks to reduce memory usage and UI overhead
    return tasks[:100]

#####################################
# 2) Build a Chart from Tasks
#####################################
def build_status_chart(tasks):
    """Creates a Plotly pie chart efficiently using Counter."""
    status_counts = Counter(t["status"] for t in tasks)
    
    labels = list(status_counts.keys())
    values = list(status_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                hoverinfo="label+percent",
                textinfo="percent",
                textfont=dict(size=16, color="white")
            )
        ]
    )
    fig.update_layout(
        title={'text': "System vs. Non-System", 'font': {'size': 20, 'color': 'white'}},
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(size=14, color="white"), orientation="h", y=-0.1),
        showlegend=True,
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
        self.bg_image_path = str(Path(bg_image_path)) if bg_image_path else None

        self.data_rows_container = None
        self.stats_chart = None

    def create_task_table(self):
        header_row = ft.Row(
            controls=[
                ft.Text("Task Name", color="white", weight=ft.FontWeight.BOLD, size=12, width=180),
                ft.Text("Next Run", color="white", weight=ft.FontWeight.BOLD, size=12, width=150),
                ft.Text("Status", color="white", weight=ft.FontWeight.BOLD, size=12, width=100),
                ft.Text("Start Time", color="white", weight=ft.FontWeight.BOLD, size=12, width=150),
                ft.Text("Duration", color="white", weight=ft.FontWeight.BOLD, size=12, width=100),
                ft.Text("PID", color="white", weight=ft.FontWeight.BOLD, size=12, width=150),
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
        status_colors = {"System": "#90caf9", "Non-System": "#a5d6a7"}
        status_color = status_colors.get(task["status"], "white")

        return ft.Row(
            controls=[
                ft.Text(task["name"], color="white", size=12, width=180, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(task["next_run"], color="white", size=12, width=150),
                ft.Text(task["status"], color=status_color, size=12, width=100),
                ft.Text(task["start_time"], color="white", size=12, width=150),
                ft.Text(task["duration"], color="white", size=12, width=100),
                ft.Text(task["first_scheduled"], color="white", size=12, width=150),
            ],
            spacing=10,
        )

    def update_task_table(self, tasks):
        if self.data_rows_container:
            # Batch update to minimize UI redraws
            self.data_rows_container.controls = [self.create_data_row(t) for t in tasks]
            self.data_rows_container.update()

    def create_statistics_chart(self):
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        self.stats_chart = PlotlyChart(fig, expand=True)
        return self.stats_chart

    def update_statistics_chart(self, tasks):
        if self.stats_chart:
            fig = build_status_chart(tasks)
            self.stats_chart.figure = fig
            self.stats_chart.update()

    def build_layout(self):
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
                    ft.Text("Statistics", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    stats_chart_control,
                ],
                spacing=10,
                expand=True
            ),
        )

        row = ft.Row(
            controls=[main_panel, right_panel],
            spacing=10,
            expand=True
        )

        if self.bg_image_path and Path(self.bg_image_path).exists():
            return ft.Stack(
                controls=[
                    ft.Container(
                        expand=True,
                        image_src=self.bg_image_path,
                        image_fit=ft.ImageFit.COVER,
                    ),
                    ft.Container(expand=True, content=row)
                ],
                expand=True
            )
        return ft.Container(expand=True, content=row)

#####################################
# 4) Create a function to return layout
#####################################
def create_system_distribution_layout(glass_bgcolor, container_blur, container_shadow, bg_image_path=None):
    app = SystemDistributionApp(glass_bgcolor, container_blur, container_shadow, bg_image_path)
    layout = app.build_layout()
    return layout, app

# Example usage
if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "System Distribution Viewer"
        page.bgcolor = "#212121"
        layout, app = create_system_distribution_layout(
            glass_bgcolor="#2A2A2A",
            container_blur=ft.Blur(10, 10),
            container_shadow=ft.BoxShadow(blur_radius=10, color="#55000000"),
            bg_image_path=None  # Set a path like "background.jpg" if desired
        )
        page.add(layout)
        start_realtime_updates(page, app)

    ft.app(target=main)
