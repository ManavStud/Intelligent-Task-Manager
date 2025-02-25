import subprocess
import flet as ft
import threading
import time

# Function to get all USB devices dynamically
def get_usb_ports():
    command = 'pnputil /enum-devices /class "USB"'
    output = subprocess.check_output(command, shell=True, encoding='utf-8')
    
    usb_devices = []
    for line in output.splitlines():
        if "USB\\" in line:  # Identifies USB device entries
            device_id = line.split(":")[-1].strip()
            usb_devices.append(device_id)
    return usb_devices

# Function to toggle USB Root Hubs (Enable/Disable)
def toggle_usb(action, log):
    device_ids = get_usb_ports()
    
    if not device_ids:
        log.controls.append(ft.Text("⚠️ No USB devices found.", color="red"))
        return
    
    command_action = "/disable-device" if action == "disable" else "/enable-device"
    for device_id in device_ids:
        log.controls.append(ft.Text(f"USB Device Detected: {device_id}", color="blue"))
        command = f'pnputil {command_action} "{device_id}" /force'
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        log.controls.append(ft.Text(f"✅ USB Device {action}d successfully.", color="green"))
    log.controls.append(ft.Text("🔄 Please restart your system to apply the changes.", color="orange"))
    log.update()

# Function to dynamically update the list of USB ports
def monitor_usb_changes(log, dropdown):
    previous_devices = set(get_usb_ports())
    
    while True:
        current_devices = set(get_usb_ports())

        if current_devices != previous_devices:
            dropdown.options = [ft.dropdown.Option(device) for device in current_devices]
            dropdown.update()
            log.controls.append(ft.Text("🔄 USB device list updated.", color="purple"))
            log.update()
            previous_devices = current_devices

        time.sleep(3)  # Check for new devices every 3 seconds

# GUI Setup using Flet
def main(page: ft.Page):
    page.title = "USB Control Panel"
    page.window_width = 500
    page.window_height = 400
    
    log = ft.Column()
    
    # Dropdown for available USB devices
    usb_devices = get_usb_ports()
    usb_dropdown = ft.Dropdown(label="Select USB Device", options=[ft.dropdown.Option(device) for device in usb_devices])

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
    threading.Thread(target=monitor_usb_changes, args=(log, usb_dropdown), daemon=True).start()
    
    page.add(
        ft.Text("USB Control Panel", size=20, weight="bold"),
        usb_dropdown,
        ft.ElevatedButton("Enable USB", on_click=enable_usb, bgcolor="green", color="white"),
        ft.ElevatedButton("Disable USB", on_click=disable_usb, bgcolor="red", color="white"),
        log
    )

ft.app(target=main)
