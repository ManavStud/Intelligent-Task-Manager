import subprocess
import flet as ft

# Function to list available Wi-Fi networks
def get_available_wifi_networks():
    command = 'netsh wlan show networks mode=bssid'
    output = subprocess.check_output(command, shell=True, encoding='utf-8')

    ssid_list = []
    for line in output.splitlines():
        if "SSID" in line and ":" in line:
            ssid = line.split(":")[1].strip()
            if ssid and ssid not in ssid_list:
                ssid_list.append(ssid)
    return ssid_list

# Function to disable all Wi-Fi
def disable_wifi(log):
    command = 'netsh interface set interface "Wi-Fi" admin=disable'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text("✅ Wi-Fi disabled successfully.", color="red"))
    log.update()

# Function to enable Wi-Fi
def enable_wifi(log):
    command = 'netsh interface set interface "Wi-Fi" admin=enable'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text("✅ Wi-Fi enabled successfully.", color="green"))
    log.update()

# Function to block a specific Wi-Fi network (SSID)
def block_wifi_network(ssid, log):
    command = f'netsh wlan add filter permission=block ssid="{ssid}" networktype=infrastructure'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text(f"🚫 Blocked Wi-Fi network: {ssid}", color="blue"))
    log.update()

# Function to unblock a specific Wi-Fi network (SSID)
def unblock_wifi_network(ssid, log):
    command = f'netsh wlan delete filter permission=block ssid="{ssid}" networktype=infrastructure'
    subprocess.run(command, shell=True)
    log.controls.append(ft.Text(f"✅ Unblocked Wi-Fi network: {ssid}", color="green"))
    log.update()

# GUI Setup using Flet
def main(page: ft.Page):
    page.title = "Wi-Fi Control Panel"
    page.window_width = 500
    page.window_height = 400

    log = ft.Column()
    
    # Dropdown for available Wi-Fi networks
    wifi_networks = get_available_wifi_networks()
    ssid_dropdown = ft.Dropdown(label="Select Wi-Fi Network", options=[ft.dropdown.Option(ssid) for ssid in wifi_networks])

    def disable_wifi_click(e):
        disable_wifi(log)

    def enable_wifi_click(e):
        enable_wifi(log)

    def block_ssid_click(e):
        if ssid_dropdown.value:
            block_wifi_network(ssid_dropdown.value, log)
        else:
            log.controls.append(ft.Text("⚠️ Please select an SSID.", color="red"))
            log.update()

    def unblock_ssid_click(e):
        if ssid_dropdown.value:
            unblock_wifi_network(ssid_dropdown.value, log)
        else:
            log.controls.append(ft.Text("⚠️ Please select an SSID.", color="red"))
            log.update()

    page.add(
        ft.Text("Wi-Fi Control Panel", size=20, weight="bold"),
        ft.ElevatedButton("Disable Wi-Fi", on_click=disable_wifi_click, bgcolor="red", color="white"),
        ft.ElevatedButton("Enable Wi-Fi", on_click=enable_wifi_click, bgcolor="green", color="white"),
        ssid_dropdown,
        ft.ElevatedButton("Block Wi-Fi Network", on_click=block_ssid_click, bgcolor="blue", color="white"),
        ft.ElevatedButton("Unblock Wi-Fi Network", on_click=unblock_ssid_click, bgcolor="purple", color="white"),
        log
    )

ft.app(target=main)
