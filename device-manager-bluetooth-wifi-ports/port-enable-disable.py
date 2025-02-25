import subprocess
import flet as ft

def get_usb_root_hubs():
    command = 'pnputil /enum-devices /class "USB"'
    output = subprocess.check_output(command, shell=True, encoding='utf-8')
    
    device_ids = []
    for line in output.splitlines():
        if "USB\\ROOT_HUB" in line:
            device_id = line.split(":")[-1].strip()
            device_ids.append(device_id)
    return device_ids

def toggle_usb(action, log):
    device_ids = get_usb_root_hubs()
    
    if not device_ids:
        log.controls.append(ft.Text("⚠️ No USB Root Hubs found.", color="red"))
        return
    
    command_action = "/disable-device" if action == "disable" else "/enable-device"
    for device_id in device_ids:
        log.controls.append(ft.Text(f"USB Root Hub Device Detected!! : {device_id}", color="blue"))
        command = f'pnputil {command_action} "{device_id}" /force'
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        log.controls.append(ft.Text(f"✅ USB Root Hub {action}d successfully.", color="green"))
    log.controls.append(ft.Text("🔄 Please restart your system to apply the changes.", color="orange"))
    log.update()

def main(page: ft.Page):
    page.title = "USB Toggle Utility"
    page.window_width = 400
    page.window_height = 300
    
    log = ft.Column()
    
    def enable_usb(e):
        toggle_usb("enable", log)
    
    def disable_usb(e):
        toggle_usb("disable", log)
    
    page.add(
        ft.Text("USB Control Panel", size=20, weight="bold"),
        ft.ElevatedButton("Enable USB", on_click=enable_usb, bgcolor="green", color="white"),
        ft.ElevatedButton("Disable USB", on_click=disable_usb, bgcolor="red", color="white"),
        log
    )

ft.app(target=main)
