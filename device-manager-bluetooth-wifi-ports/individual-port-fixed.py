import subprocess
import psutil
import flet as ft
import threading
import time
import os

# --- 1. Get USB Root Hub Device IDs ---
def get_usb_root_hubs():
    command = 'pnputil /enum-devices /class "USB"'
    try:
        output = subprocess.check_output(command, shell=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        return []
    
    device_ids = []
    for line in output.splitlines():
        if "USB\\ROOT_HUB" in line:
            device_id = line.split(":")[-1].strip()
            device_ids.append(device_id)
    return device_ids

# --- 2. Toggle USB Ports (Enable/Disable) ---
def toggle_usb(action, log):
    device_ids = get_usb_root_hubs()
    
    if not device_ids:
        log.controls.append(ft.Text("⚠️ No USB Root Hubs found.", color="red"))
        log.update()
        return
    
    command_action = "/disable-device" if action == "disable" else "/enable-device"
    
    for device_id in device_ids:
        log.controls.append(ft.Text(f"USB Root Hub Device Detected!! : {device_id}", color="blue"))
        command = f'pnputil {command_action} "{device_id}" /force'
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        log.controls.append(ft.Text(f"✅ USB Root Hub {action}d successfully.", color="green"))
    
    # Apply Registry Lock when Disabling
    if action == "disable":
        disable_usb_registry()
    
    log.controls.append(ft.Text("🔄 Please restart your system to apply the changes.", color="orange"))
    log.update()

# --- 3. Disable USB via Registry (Prevent Unauthorized Changes) ---
def disable_usb_registry():
    command = r'reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR" /v Start /t REG_DWORD /d 4 /f'
    subprocess.run(command, shell=True)
    
    # Lock registry key to prevent modifications
    lock_command = r'regini.exe HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR [1 1 3]'
    subprocess.run(lock_command, shell=True)

# --- 4. Monitor & Kill Unauthorized USB Enable Attempts ---
def kill_usb_modifiers(log):
    while True:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any("pnputil" in arg or "reg add" in arg for arg in proc.info['cmdline']):
                    log.controls.append(ft.Text(f"⚠️ Unauthorized attempt detected: {proc.info['name']} (PID: {proc.info['pid']})", color="red"))
                    proc.terminate()
                    disable_usb_registry()
                    log.controls.append(ft.Text("🔒 USB re-disabled to prevent unauthorized access.", color="purple"))
                    log.update()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(2)  # Check every 2 seconds

# --- 5. GUI Interface ---
def main(page: ft.Page):
    page.title = "USB Security Control Panel"
    page.window_width = 500
    page.window_height = 400
    
    log = ft.Column()

    def enable_usb(e):
        toggle_usb("enable", log)

    def disable_usb(e):
        toggle_usb("disable", log)

    page.add(
        ft.Text("🔒 USB Security Control Panel", size=24, weight="bold"),
        ft.ElevatedButton("Enable USB", on_click=enable_usb, bgcolor="green", color="white"),
        ft.ElevatedButton("Disable USB", on_click=disable_usb, bgcolor="red", color="white"),
        log
    )

    # Start Background Thread for Monitoring Unauthorized USB Attempts
    threading.Thread(target=kill_usb_modifiers, args=(log,), daemon=True).start()

ft.app(target=main)