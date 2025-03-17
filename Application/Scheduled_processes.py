import flet as ft
from flet import BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur
import plotly.graph_objects as go
import psutil
import asyncio
import threading
import os
import platform
import math
import datetime
import time

# Ensure Windows-only execution
if platform.system() != "Windows":
    raise SystemExit("This application is designed to run on Windows only.")

#####################################
# 1) Periodic Task Management
#####################################
async def periodic_update(page: ft.Page, app):
    """Runs in a background thread, fetching data and updating the UI every 5 seconds."""
    while True:
        try:
            tasks = fetch_realtime_tasks()
            app.update_task_table(tasks)
            app.update_statistics_chart(tasks)
            page.update()
        except Exception as e:
            print(f"Error in periodic update: {e}")
        finally:
            await asyncio.sleep(5)

def start_realtime_updates(page: ft.Page, app):
    """
    Starts the periodic update in a separate event loop so it doesn't block the main thread.
    """
    try:
        new_loop = asyncio.new_event_loop()
        new_loop.create_task(periodic_update(page, app))
        t = threading.Thread(target=_run_loop, args=(new_loop,), daemon=True)
        t.start()
        print("Realtime updates started for Scheduled Processes (Windows)")
        return True
    except Exception as e:
        print(f"Error starting realtime updates: {e}")
        return False

def _run_loop(loop):
    try:
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except Exception as e:
        print(f"Error in run loop: {e}")

def format_timestamp(timestamp):
    """Formats Unix timestamp to a readable date/time format."""
    if timestamp:
        try:
            return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError, OSError):
            return "N/A"
    return "N/A"

def format_duration(seconds):
    """Formats duration in seconds to a readable format."""
    if seconds is None:
        return "N/A"
    
    try:
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except (ValueError, TypeError):
        return "N/A"

def estimate_next_run(proc_info):
    """Estimate next run time based on CPU usage and process pattern."""
    try:
        # Special handling for system processes
        if proc_info.get('is_system', False):
            # System processes like "System Idle Process" run continuously
            # Return "Continuous" for these types of processes
            return "Continuous"
        
        # For processes with higher CPU usage, estimate they'll be active again soon
        if proc_info.get('cpu_percent', 0) > 5:
            # Active process - estimate next run in a few seconds
            next_run = datetime.datetime.now() + datetime.timedelta(seconds=5)
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Idle process - estimate next run in a minute
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=1)
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "N/A"

def fetch_realtime_tasks():
    """Fetches real-time processes with timing information."""
    tasks = []
    current_time = time.time()
    boot_time = psutil.boot_time()  # Get system boot time
    
    try:
        # Get processes with more information
        for proc in list(psutil.process_iter(['pid', 'name', 'username', 'create_time', 'cpu_percent'])):
            try:
                # Get basic info from the iterator
                info = proc.info
                
                # Determine process type
                user = info.get('username', None)
                process_name = info.get('name', 'Unknown')
                
                # Special handling for system processes
                is_system_process = (user is None or "SYSTEM" in user.upper() or 
                                    process_name.lower() in ["system", "system idle process", "registry", "memory compression"])
                
                if is_system_process:
                    status = "System"
                    
                    # Special handling for System Idle Process - use boot time instead
                    if process_name.lower() == "system idle process":
                        create_time = boot_time
                    else:
                        # For other system processes, try to get create_time or use boot time as fallback
                        create_time = info.get('create_time', boot_time)
                else:
                    status = "Non-System"
                    create_time = info.get('create_time', None)
                
                # Get process creation time (start time)
                start_time = format_timestamp(create_time)
                
                # Calculate process duration (current time - creation time)
                duration = "N/A"
                if create_time:
                    try:
                        duration_sec = current_time - create_time
                        duration = format_duration(duration_sec)
                    except:
                        duration = "N/A"
                
                # Additional process info for next run estimation
                proc_info = {
                    'cpu_percent': info.get('cpu_percent', 0),
                    'is_system': is_system_process
                }
                
                # Attempt to get next run time
                next_run = estimate_next_run(proc_info)
                
                tasks.append({
                    "name": process_name,
                    "next_run": next_run,
                    "status": status,
                    "start_time": start_time,
                    "duration": duration,
                    "first_scheduled": f"PID: {info['pid']}",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error fetching tasks: {e}")
    
    return tasks

#####################################
# 2) SystemDistributionApp Class
#####################################
class SystemDistributionApp:
    def __init__(self, glass_bgcolor, container_blur, container_shadow, bg_image_path=None):
        self.glass_bgcolor = glass_bgcolor
        self.container_blur = container_blur
        self.container_shadow = container_shadow
        self.bg_image_path = bg_image_path or ""
        self.data_rows_container = None
        self.page = None
        self.stats_container = None
        self.system_count = 0
        self.non_system_count = 0
        self.system_label = None
        self.non_system_label = None
        self.system_segment = None
        self.non_system_segment = None
        
    def create_task_table(self):
        """Creates a table displaying tasks."""
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

        # Create the data rows container
        self.data_rows_container = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        table_data = ft.Container(content=self.data_rows_container, expand=True)
        
        # Create the table container
        table_container = ft.Container(
            content=ft.Column(controls=[header_row, table_data], spacing=0, expand=True),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            expand=True,
        )
        
        # Create the statistics section (right side)
        self.stats_container = ft.Container(
            content=ft.Column([
                ft.Text("Statistics", size=24, color="white", weight=ft.FontWeight.BOLD),
                ft.Container(height=40),  # Spacer
                self.create_pie_chart_ui()
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            width=400  # Reduced width to make left side take more space (was 500)
        )
        
        # Create layout with table on left and chart on right
        # Use a ratio of 7:3 to make the table larger relative to the chart
        layout = ft.Row(
            controls=[
                ft.Container(content=table_container, expand=7),  # Table gets 70% of space
                ft.Container(content=self.stats_container, expand=3)  # Chart gets 30% of space
            ],
            spacing=10,
            expand=True
        )
        
        return layout
    
    def create_pie_chart_ui(self):
        """Creates a donut chart visualization using standard Flet components."""
        self.chart_title = ft.Text("System vs. Non-System Processes", size=18, color="white", weight=ft.FontWeight.BOLD)
        
        # Initialize with dummy data - will be updated with real data
        self.system_percent = 50
        self.non_system_percent = 50
        
        # Chart colors
        system_color = "#4e68f9"  # Blue for System
        non_system_color = "#ff6054"  # Red for Non-System
        
        # Chart dimensions
        chart_size = 220
        
        # Increase donut width by adjusting stroke_width (was 0.2, now 0.3)
        donut_thickness = chart_size * 0.3
        
        # Create the system segment (blue portion) using a progress ring
        self.system_segment = ft.ProgressRing(
            value=self.system_percent / 100,
            width=chart_size,
            height=chart_size,
            stroke_width=donut_thickness,  # Increased thickness for wider donut
            color=system_color,
            bgcolor="transparent",
        )
        
        # Create the non-system segment (red portion)
        self.non_system_segment = ft.ProgressRing(
            value=self.non_system_percent / 100,
            width=chart_size,
            height=chart_size,
            stroke_width=donut_thickness,  # Increased thickness for wider donut
            color=non_system_color,
            bgcolor="transparent",
            rotate=math.pi * self.system_percent / 50,  # Rotate to start where system ends
        )
        
        # Create the percentage labels
        self.system_label = ft.Text(
            f"{self.system_percent}%", 
            size=16, 
            color="white", 
            weight=ft.FontWeight.BOLD
        )
        
        self.non_system_label = ft.Text(
            f"{self.non_system_percent}%", 
            size=16, 
            color="white", 
            weight=ft.FontWeight.BOLD
        )
        
        # Create a stack for the chart - without the black center circle
        self.chart_container = ft.Container(
            width=chart_size,
            height=chart_size,
            content=ft.Stack([
                # Non-system segment first (base layer)
                self.non_system_segment,
                # System segment on top
                self.system_segment,
                # System percentage label
                ft.Container(
                    content=self.system_label,
                    left=chart_size * 0.6,
                    top=chart_size * 0.3,
                ),
                # Non-System percentage label
                ft.Container(
                    content=self.non_system_label,
                    left=chart_size * 0.2,
                    top=chart_size * 0.6,
                ),
            ]),
            alignment=ft.alignment.center,
        )
        
        # Create the legend
        legend = ft.Row([
            # System legend item
            ft.Row([
                ft.Container(width=12, height=12, bgcolor=system_color, border_radius=6),
                ft.Text("System", color="white", size=14),
            ], spacing=5),
            # Spacer
            ft.Container(width=30),
            # Non-System legend item
            ft.Row([
                ft.Container(width=12, height=12, bgcolor=non_system_color, border_radius=6),
                ft.Text("Non-System", color="white", size=14),
            ], spacing=5),
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Create the chart view
        return ft.Column([
            self.chart_title,
            ft.Container(height=40),  # Spacer
            self.chart_container,  
            ft.Container(height=20),  # Spacer
            legend
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def update_task_table(self, tasks):
        """Updates the task table with new data."""
        try:
            new_data_rows = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(content=ft.Text(t["name"], color="white", size=12), width=180),
                            ft.Container(content=ft.Text(t["next_run"], color="white", size=12), width=150),
                            ft.Container(content=ft.Text(t["status"], color="#90caf9" if t["status"] == "System" else "#a5d6a7", size=12), width=100),
                            ft.Container(content=ft.Text(t["start_time"], color="white", size=12), width=150),
                            ft.Container(content=ft.Text(t["duration"], color="white", size=12), width=100),
                            ft.Container(content=ft.Text(t["first_scheduled"], color="white", size=12), width=150),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    border_radius=5,
                    bgcolor=self.glass_bgcolor,
                    blur=self.container_blur,
                    shadow=self.container_shadow,
                ) for t in tasks
            ]
            if self.data_rows_container:
                self.data_rows_container.controls = new_data_rows
        except Exception as e:
            print(f"Error updating task table: {e}")

    def update_statistics_chart(self, tasks):
        """Updates the statistics chart with new data."""
        try:
            # Count system vs non-system processes
            self.system_count = sum(1 for t in tasks if t["status"] == "System")
            self.non_system_count = len(tasks) - self.system_count
            
            total = max(1, self.system_count + self.non_system_count)  # Avoid division by zero
            self.system_percent = int((self.system_count / total) * 100)
            self.non_system_percent = 100 - self.system_percent
            
            # Update the progress rings with new values
            if hasattr(self, 'system_segment') and self.system_segment:
                self.system_segment.value = self.system_percent / 100
                
            if hasattr(self, 'non_system_segment') and self.non_system_segment:
                self.non_system_segment.value = self.non_system_percent / 100
                # Adjust rotation based on system percentage
                self.non_system_segment.rotate = math.pi * self.system_percent / 50
            
            # Update the percentage labels
            if hasattr(self, 'system_label') and self.system_label:
                self.system_label.value = f"{self.system_percent}%"
                
            if hasattr(self, 'non_system_label') and self.non_system_label:
                self.non_system_label.value = f"{self.non_system_percent}%"
                
        except Exception as e:
            print(f"Error updating statistics chart: {e}")

#####################################
# 4) Create a function to return layout
#####################################
def create_system_distribution_layout(glass_bgcolor, container_blur, container_shadow, bg_image_path=None):
    app = SystemDistributionApp(glass_bgcolor, container_blur, container_shadow, bg_image_path)
    layout = app.create_task_table()
    return layout, app
