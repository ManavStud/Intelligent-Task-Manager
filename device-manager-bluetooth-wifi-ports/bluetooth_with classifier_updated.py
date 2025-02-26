import subprocess
import os
import flet as ft

POWERSHELL_PATH = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"

def is_powershell_available():
    return os.path.exists(POWERSHELL_PATH)

def run_powershell_command(command):
    if not is_powershell_available():
        return "❌ PowerShell is not available."

    try:
        output = subprocess.check_output(
            [POWERSHELL_PATH, "-Command", command],
            encoding="utf-8",
            stderr=subprocess.STDOUT
        )
        return output.strip()
    except subprocess.CalledProcessError as e:
        return f"❌ Error: {e.output.strip()}"

def is_admin():
    command = '[bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).Groups -match "S-1-5-32-544")'
    output = run_powershell_command(command)
    return "True" in output

def identify_device_type(device_name):
    command = f'Get-WmiObject Win32_PnPEntity | Where-Object {{ $_.Caption -eq "{device_name}" }} | Select-Object PNPClass, Description, DeviceID'
    output = run_powershell_command(command).lower()

    # Improved detection logic
    if any(keyword in device_name.lower() for keyword in ["airpods", "airdopes", "boat rockerz", "headset", "headphone", "earbuds"]) or "avrcp" in output:
        return "Headset/Headphone"
    elif "speaker" in output or "a2dp" in output:
        return "Speaker"
    elif "mouse" in output or "hid" in output:
        return "Mouse"
    elif "keyboard" in output:
        return "Keyboard"
    elif "game" in output or "controller" in output:
        return "Game Controller"
    elif "printer" in output:
        return "Printer"
    elif "phone" in output or "rfcomm" in output:
        return "Mobile Device"
    elif "network" in output or "adapter" in output:
        return "Network Device"
    elif "storage" in output or "usb" in output:
        return "Storage Device"
    
    return "Unknown"

def get_available_bluetooth_devices():
    command = 'Get-WmiObject Win32_PnPEntity | Where-Object { $_.PNPClass -eq "Bluetooth" } | Select-Object Caption'
    output = run_powershell_command(command)

    if "❌" in output:
        return [output]  

    bt_devices = [line.strip() for line in output.splitlines() if line.strip()]
    if not bt_devices:
        return ["⚠️ No Bluetooth Devices Found"]

    bt_devices_with_type = []
    for device in bt_devices:
        device_type = identify_device_type(device)
        bt_devices_with_type.append(f"{device} ({device_type})")

    return bt_devices_with_type

def enable_bluetooth(log):
    if not is_admin():
        log.controls.append(ft.Text("❌ Run as Administrator.", color="red"))
        log.update()
        return

    command = 'Start-Service bthserv; Get-PnpDevice | Where-Object { $_.Class -eq "Bluetooth" } | Enable-PnpDevice -Confirm:$false'
    result = run_powershell_command(command)
    log.controls.append(ft.Text(result, color="green" if "✅" in result else "red"))
    log.update()

def disable_bluetooth(log):
    if not is_admin():
        log.controls.append(ft.Text("❌ Run as Administrator.", color="red"))
        log.update()
        return

    command = 'Get-PnpDevice | Where-Object { $_.Class -eq "Bluetooth" } | Disable-PnpDevice -Confirm:$false'
    result = run_powershell_command(command)
    log.controls.append(ft.Text(result, color="red"))
    log.update()

def block_bluetooth_device(device_name, log):
    if not is_admin():
        log.controls.append(ft.Text("❌ Run as Administrator.", color="red"))
        log.update()
        return

    command = f'Get-PnpDevice | Where-Object {{ $_.FriendlyName -eq "{device_name}" }} | Disable-PnpDevice -Confirm:$false'
    result = run_powershell_command(command)
    log.controls.append(ft.Text(result, color="blue"))
    log.update()

def unblock_bluetooth_device(device_name, log):
    if not is_admin():
        log.controls.append(ft.Text("❌ Run as Administrator.", color="red"))
        log.update()
        return

    command = f'Get-PnpDevice | Where-Object {{ $_.FriendlyName -eq "{device_name}" }} | Enable-PnpDevice -Confirm:$false'
    result = run_powershell_command(command)
    log.controls.append(ft.Text(result, color="green"))
    log.update()

def main(page: ft.Page):
    page.title = "Bluetooth Control Panel"
    page.window_width = 500
    page.window_height = 500

    log = ft.Column()

    if not is_powershell_available():
        log.controls.append(ft.Text("❌ PowerShell is not available.", color="red"))
        page.add(log)
        return

    bt_devices = get_available_bluetooth_devices()
    bt_dropdown = ft.Dropdown(
        label="Select Bluetooth Device",
        options=[ft.dropdown.Option(bt) for bt in bt_devices],
    )

    def disable_bluetooth_click(e):
        disable_bluetooth(log)

    def enable_bluetooth_click(e):
        enable_bluetooth(log)

    def block_bt_click(e):
        if bt_dropdown.value and "⚠️" not in bt_dropdown.value:
            block_bluetooth_device(bt_dropdown.value.split(" (")[0], log)
        else:
            log.controls.append(ft.Text("⚠️ Select a valid Bluetooth device.", color="red"))
            log.update()

    def unblock_bt_click(e):
        if bt_dropdown.value and "⚠️" not in bt_dropdown.value:
            unblock_bluetooth_device(bt_dropdown.value.split(" (")[0], log)
        else:
            log.controls.append(ft.Text("⚠️ Select a valid Bluetooth device.", color="red"))
            log.update()

    page.add(
        ft.Text("Bluetooth Control Panel", size=20, weight="bold"),
        ft.ElevatedButton("Disable Bluetooth", on_click=disable_bluetooth_click, bgcolor="red", color="white"),
        ft.ElevatedButton("Enable Bluetooth", on_click=enable_bluetooth_click, bgcolor="green", color="white"),
        bt_dropdown,
        ft.ElevatedButton("Block Bluetooth Device", on_click=block_bt_click, bgcolor="blue", color="white"),
        ft.ElevatedButton("Unblock Bluetooth Device", on_click=unblock_bt_click, bgcolor="purple", color="white"),
        log
    )

ft.app(target=main)
