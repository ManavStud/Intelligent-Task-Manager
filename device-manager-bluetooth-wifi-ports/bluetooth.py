import subprocess
import flet as ft

# Function to list available Bluetooth devices
def get_available_bluetooth_devices():
    command = 'powershell "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName"'
    output = subprocess.check_output(command, shell=True, encoding='utf-8')

    bt_devices = []
    for line in output.splitlines():
        if line.strip() and "FriendlyName" not in line:
            bt_devices.append(line.strip())
    return bt_devices

# Function to disable Bluetooth (disable the adapter)
def disable_bluetooth(log):
    command = 'powershell "Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false"'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text("✅ Bluetooth disabled successfully.", color="red"))
    log.update()

# Function to enable Bluetooth (enable the adapter)
def enable_bluetooth(log):
    command = 'powershell "Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false"'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text("✅ Bluetooth enabled successfully.", color="green"))
    log.update()

# Function to block (disable) a specific Bluetooth device
def block_bluetooth_device(device_name, log):
    command = f'powershell "Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.FriendlyName -eq \'{device_name}\' }} | Disable-PnpDevice -Confirm:$false"'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text(f"🚫 Blocked Bluetooth device: {device_name}", color="blue"))
    log.update()

# Function to unblock (enable) a specific Bluetooth device
def unblock_bluetooth_device(device_name, log):
    command = f'powershell "Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.FriendlyName -eq \'{device_name}\' }} | Enable-PnpDevice -Confirm:$false"'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text(f"✅ Unblocked Bluetooth device: {device_name}", color="green"))
    log.update()

# GUI Setup using Flet
def main(page: ft.Page):
    page.title = "Bluetooth Control Panel"
    page.window_width = 500
    page.window_height = 400

    log = ft.Column()
    
    # Dropdown for available Bluetooth devices
    bt_devices = get_available_bluetooth_devices()
    bt_dropdown = ft.Dropdown(label="Select Bluetooth Device", options=[ft.dropdown.Option(bt) for bt in bt_devices])

    def disable_bluetooth_click(e):
        disable_bluetooth(log)

    def enable_bluetooth_click(e):
        enable_bluetooth(log)

    def block_bt_click(e):
        if bt_dropdown.value:
            block_bluetooth_device(bt_dropdown.value, log)
        else:
            log.controls.append(ft.Text("⚠️ Please select a Bluetooth device.", color="red"))
            log.update()

    def unblock_bt_click(e):
        if bt_dropdown.value:
            unblock_bluetooth_device(bt_dropdown.value, log)
        else:
            log.controls.append(ft.Text("⚠️ Please select a Bluetooth device.", color="red"))
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
