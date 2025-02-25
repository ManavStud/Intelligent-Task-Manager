import subprocess
import flet as ft
import threading
import time
import logging
import json
import os
from datetime import datetime
from prettytable import PrettyTable

# Create log directory if it doesn't exist
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "usb_activity.log")

# Configure structured logging for the terminal
log_formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", '
    '"level": "%(levelname)s", '
    '"script": "%(name)s", '
    '"module": "%(module)s", '
    '"funcName": "%(funcName)s", '
    '"lineNo": "%(lineno)d", '
    '"message": "%(message)s"}'
)

log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)

file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("USB_Control")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(file_handler)

# USB activity tracking
usb_activity = {}

# Function to get all USB devices dynamically
def get_usb_ports():
    command = 'pnputil /enum-devices /class "USB"'
    try:
        output = subprocess.check_output(command, shell=True, encoding='utf-8')
        usb_devices = []
        for line in output.splitlines():
            if "USB\\" in line:  # Identifies USB device entries
                device_id = line.split(":")[-1].strip()
                usb_devices.append(device_id)

        logger.info(json.dumps({"event": "usb_scan", "devices": usb_devices}))
        return usb_devices
    except subprocess.CalledProcessError as e:
        logger.error(json.dumps({"error": "Failed to fetch USB devices", "details": str(e)}))
        return []

# Function to toggle USB Root Hubs (Enable/Disable)
def toggle_usb(action, log):
    device_ids = get_usb_ports()
    
    if not device_ids:
        log.controls.append(ft.Text("⚠️ No USB devices found.", color="red"))
        logger.warning(json.dumps({"event": "no_usb_found"}))
        return
    
    command_action = "/disable-device" if action == "disable" else "/enable-device"

    for device_id in device_ids:
        log.controls.append(ft.Text(f"USB Device Detected: {device_id}", color="blue"))
        command = f'pnputil {command_action} "{device_id}" /force'
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        log.controls.append(ft.Text(f"✅ USB Device {action}d successfully.", color="green"))

        # Log success
        logger.info(json.dumps({"event": f"usb_{action}", "device_id": device_id}))

    log.controls.append(ft.Text("🔄 Please restart your system to apply the changes.", color="orange"))
    log.update()

# Function to dynamically update the list of USB ports
def monitor_usb_changes(log, dropdown, log_table):
    global usb_activity
    previous_devices = set(get_usb_ports())

    while True:
        current_devices = set(get_usb_ports())

        # Detect newly connected USB devices
        for device in current_devices - previous_devices:
            start_time = datetime.now().strftime("%I:%M %p")
            usb_activity[device] = {"start_time": start_time, "end_time": None}  # Mark as connected

            log_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(device)),  # Device Name
                        ft.DataCell(ft.Text("Connected", color="green")),  # Status
                        ft.DataCell(ft.Text(start_time)),  # Start Time
                        ft.DataCell(ft.Text("-")),  # End Time not available yet
                    ]
                )
            )

            logger.info(json.dumps({"event": "usb_connected", "device_id": device, "start_time": start_time}))
            update_log_file()

        # Detect disconnected USB devices
        for device in previous_devices - current_devices:
            if device in usb_activity and usb_activity[device]["end_time"] is None:
                end_time = datetime.now().strftime("%I:%M %p")
                usb_activity[device]["end_time"] = end_time  # Mark as disconnected

                # Update table row with end time
                for row in log_table.rows:
                    if row.cells[0].content.value == device:
                        row.cells[1].content.value = "Disconnected"
                        row.cells[1].content.color = "red"
                        row.cells[3].content.value = end_time  # Update End Time

                logger.info(json.dumps({"event": "usb_disconnected", "device_id": device, "end_time": end_time}))
                update_log_file()

        # Update UI
        dropdown.options = [ft.dropdown.Option(device) for device in current_devices]
        dropdown.update()
        log_table.update()
        previous_devices = current_devices

        time.sleep(3)  # Check every 3 seconds

# Function to generate .log file in table format
def update_log_file():
    table = PrettyTable()
    table.field_names = ["Device ID", "Status", "Start Time", "End Time"]

    for device, details in usb_activity.items():
        table.add_row([
            device,
            "Connected" if details["end_time"] is None else "Disconnected",
            details["start_time"],
            details["end_time"] if details["end_time"] else "-"
        ])

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(table.get_string())

# GUI Setup using Flet
def main(page: ft.Page):
    page.title = "USB Control Panel"
    page.window_width = 700
    page.window_height = 500

    log = ft.Column()
    
    # Dropdown for available USB devices
    usb_devices = get_usb_ports()
    usb_dropdown = ft.Dropdown(label="Select USB Device", options=[ft.dropdown.Option(device) for device in usb_devices])

    # Logs table setup
    log_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Port Name")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Start Time")),
            ft.DataColumn(ft.Text("End Time")),
        ],
        rows=[]
    )

    def enable_usb(e):
        if usb_dropdown.value:
            toggle_usb("enable", log)
        else:
            log.controls.append(ft.Text("⚠️ Please select a USB device.", color="red"))
            log.update()

    def disable_usb(e):
        if usb_dropdown.value:
            toggle_usb("disable", log)
        else:
            log.controls.append(ft.Text("⚠️ Please select a USB device.", color="red"))
            log.update()

    # Start a separate thread to monitor USB changes
    threading.Thread(target=monitor_usb_changes, args=(log, usb_dropdown, log_table), daemon=True).start()

    page.add(
        ft.Text("USB Control Panel", size=20, weight="bold"),
        usb_dropdown,
        ft.ElevatedButton("Enable USB", on_click=enable_usb, bgcolor="green", color="white"),
        ft.ElevatedButton("Disable USB", on_click=disable_usb, bgcolor="red", color="white"),
        log_table,  # Display logs table
        log
    )

ft.app(target=main)
