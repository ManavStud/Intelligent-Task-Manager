import flet as ft
import os
from flet import Icons, BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur, ImageFit, ImageRepeat

class DeviceManagerUI:
    def __init__(self, base_path: str, glass_bgcolor: str, container_blur: Blur, container_shadow: BoxShadow, accent_color: str):
        self.base_path = base_path
        self.glass_bgcolor = glass_bgcolor
        self.container_blur = container_blur
        self.container_shadow = container_shadow
        self.accent_color = accent_color

        # Ports state
        self.port_start_index = 0
        self.total_ports = 10
        self.visible_ports = 3
        self.all_ports = [{"id": i+1, "state": False} for i in range(self.total_ports)]
        self.ports_container_ref = ft.Ref[ft.Container]()

        # Devices state
        self.device_start_index = 0
        self.total_devices = 10
        self.visible_devices = 3
        self.all_devices = [
            {"type": "bluetooth", "icon": Icons.BLUETOOTH, "name": "Bluetooth"},
            {"type": "keyboard", "icon": Icons.KEYBOARD, "name": "Keyboard"},
            {"type": "mouse", "icon": Icons.MOUSE, "name": "Mouse"},
            {"type": "headphones", "icon": Icons.HEADPHONES, "name": "Headphones"},
            {"type": "speaker", "icon": Icons.SPEAKER, "name": "Speaker"},
            {"type": "printer", "icon": Icons.PRINT, "name": "Printer"},
            {"type": "monitor", "icon": Icons.MONITOR, "name": "Monitor"},
            {"type": "webcam", "icon": Icons.VIDEOCAM, "name": "Webcam"},
            {"type": "microphone", "icon": Icons.MIC, "name": "Microphone"},
            {"type": "tablet", "icon": Icons.TABLET, "name": "Tablet"},
        ]
        self.devices_container_ref = ft.Ref[ft.Container]()

        # Camera and Microphone state
        self.camera_state = False
        self.microphone_state = False

    # ------------------- Ports Section -------------------
    def create_port_info_container(self, index):
        actual_index = self.port_start_index + index
        info_tooltip = ft.Ref[ft.Container]()
        info_icon = ft.IconButton(
            icon=Icons.INFO_OUTLINE,
            icon_color="white",
            icon_size=16,
            on_click=lambda e: toggle_info_color(e, info_tooltip)
        )

        def toggle_info_color(e, tooltip_ref):
            if tooltip_ref.current.data == "inactive":
                tooltip_ref.current.data = "active"
                info_icon.icon_color = "green"
            else:
                tooltip_ref.current.data = "inactive"
                info_icon.icon_color = "white"
            e.control.update()

        current_port_state = self.all_ports[actual_index]["state"]

        return ft.Container(
            ref=info_tooltip,
            data="inactive",
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Image(
                                src=os.path.join(self.base_path, "usb_type_a.svg"),
                                width=50,
                                height=50,
                                fit=ImageFit.CONTAIN,
                            ),
                            ft.Text("USB Type A", color="white", size=12, weight=ft.FontWeight.W_500)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Status:", color="white", size=10, width=50),
                                    ft.Text("On" if current_port_state else "Off", color="white", size=10)
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                spacing=-18,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Switch(
                                        value=current_port_state,
                                        active_color=self.accent_color,
                                        scale=0.8,
                                        on_change=lambda e, i=index: self.toggle_port(e, i),
                                    ),
                                    info_icon
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                spacing=-15,
                            ),
                            ft.Text("Connected" if current_port_state else "Not Connected", color="white", size=10),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=5,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            ),
            width=200,
            height=110,
            padding=10,
            border_radius=10,
            bgcolor="transparent",
        )

    def create_ports_row(self):
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color="white",
                        icon_size=20,
                        on_click=self.prev_ports,
                        disabled=self.port_start_index == 0,
                    ),
                    alignment=ft.alignment.center_right,
                    padding=ft.padding.only(right=20),
                ),
                ft.Row(
                    controls=[self.create_port_info_container(i) for i in range(self.visible_ports)],
                    spacing=30,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=Icons.ARROW_FORWARD_IOS,
                        icon_color="white",
                        icon_size=20,
                        on_click=self.next_ports,
                        disabled=self.port_start_index + self.visible_ports >= self.total_ports,
                    ),
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(left=10),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=-30,
        )

    def create_ports_section(self):
        return ft.Container(
            ref=self.ports_container_ref,
            content=ft.Column([
                ft.Row([
                    ft.Text("Ports", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(expand=True),
                ]),
                self.create_ports_row(),
            ]),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=15),
        )

    def toggle_port(self, e, port_index):
        actual_index = self.port_start_index + port_index
        self.all_ports[actual_index]["state"] = e.control.value
        new_ports_row = self.create_ports_row()
        if self.ports_container_ref.current:
            self.ports_container_ref.current.content.controls[1] = new_ports_row
            e.page.update()

    def next_ports(self, e):
        if self.port_start_index + self.visible_ports < self.total_ports:
            self.port_start_index = min(self.port_start_index + self.visible_ports, self.total_ports - self.visible_ports)
            new_ports_row = self.create_ports_row()
            if self.ports_container_ref.current:
                self.ports_container_ref.current.content.controls[1] = new_ports_row
                e.page.update()

    def prev_ports(self, e):
        if self.port_start_index > 0:
            self.port_start_index = max(0, self.port_start_index - self.visible_ports)
            new_ports_row = self.create_ports_row()
            if self.ports_container_ref.current:
                self.ports_container_ref.current.content.controls[1] = new_ports_row
                e.page.update()

    # ------------------- Devices Section -------------------
    def create_device_container(self, device):
        return ft.Container(
            content=ft.Column([
                ft.Icon(device["icon"], color="white", size=24),
                ft.Text(device["name"], color="white", size=12),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5,
            ),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            width=90,
            height=80,
        )

    def create_devices_row(self):
        visible_devices = self.all_devices[self.device_start_index:self.device_start_index + self.visible_devices]
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color="white",
                        icon_size=20,
                        on_click=self.prev_devices,
                        disabled=self.device_start_index == 0,
                    ),
                    alignment=ft.alignment.center_right,
                    padding=ft.padding.only(right=50),
                ),
                ft.Row(
                    controls=[self.create_device_container(device) for device in visible_devices],
                    spacing=170,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=Icons.ARROW_FORWARD_IOS,
                        icon_color="white",
                        icon_size=20,
                        on_click=self.next_devices,
                        disabled=self.device_start_index + self.visible_devices >= self.total_devices,
                    ),
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(left=50),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=-30,
        )

    def next_devices(self, e):
        if self.device_start_index + self.visible_devices < self.total_devices:
            self.device_start_index = min(self.device_start_index + self.visible_devices,
                                          self.total_devices - self.visible_devices)
            new_devices_row = self.create_devices_row()
            if self.devices_container_ref.current:
                self.devices_container_ref.current.content.controls[1] = new_devices_row
                e.page.update()

    def prev_devices(self, e):
        if self.device_start_index > 0:
            self.device_start_index = max(0, self.device_start_index - self.visible_devices)
            new_devices_row = self.create_devices_row()
            if self.devices_container_ref.current:
                self.devices_container_ref.current.content.controls[1] = new_devices_row
                e.page.update()

    def create_connected_devices_section(self):
        return ft.Container(
            ref=self.devices_container_ref,
            content=ft.Column([
                ft.Row([
                    ft.Text("Connected Devices", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(expand=True),
                ]),
                self.create_devices_row(),
            ]),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=ft.padding.only(top=20, bottom=40, left=15, right=15),
        )

    # ------------------- Camera & Microphone Section -------------------
    def create_camera_microphone_section(self):
        def toggle_camera(e):
            self.camera_state = not self.camera_state
            camera_status.value = "On" if self.camera_state else "Off"
            camera_toggle.value = self.camera_state
            e.control.page.update()

        def toggle_microphone(e):
            self.microphone_state = not self.microphone_state
            mic_status.value = "On" if self.microphone_state else "Off"
            mic_toggle.value = self.microphone_state
            e.control.page.update()

        camera_status = ft.Text("Off", color="white", size=12, weight=ft.FontWeight.W_500)
        camera_toggle = ft.Switch(
            value=self.camera_state,
            active_color=self.accent_color,
            scale=0.8,
            on_change=toggle_camera
        )
        camera_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src=os.path.join(self.base_path, "camera.svg"),
                        width=25,
                        height=25,
                        fit=ImageFit.CONTAIN,
                    ),
                    ft.Text("Camera", color="white", size=14, weight=ft.FontWeight.W_500),
                    ft.Row(
                        controls=[ft.Text("Status:", color="white", size=12), camera_status],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(controls=[camera_toggle], alignment=ft.MainAxisAlignment.START),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=5,
            ),
            width=280,
            height=130,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            padding=15,
        )

        mic_status = ft.Text("Off", color="white", size=12, weight=ft.FontWeight.W_500)
        mic_toggle = ft.Switch(
            value=self.microphone_state,
            active_color=self.accent_color,
            scale=0.8,
            on_change=toggle_microphone
        )
        microphone_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src=os.path.join(self.base_path, "mic.svg"),
                        width=25,
                        height=25,
                        fit=ImageFit.CONTAIN,
                    ),
                    ft.Text("Microphone", color="white", size=14, weight=ft.FontWeight.W_500),
                    ft.Row(
                        controls=[ft.Text("Status:", color="white", size=12), mic_status],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(controls=[mic_toggle], alignment=ft.MainAxisAlignment.START),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=5,
            ),
            width=280,
            height=130,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            padding=15,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Device Control", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(expand=True),
                ]),
                ft.Row(
                    controls=[camera_container, microphone_container],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=30,
                ),
            ]),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=15),
        )

    # ------------------- Assemble the Device Manager UI -------------------
    def build(self):
        """Return the complete Device Manager UI layout."""
        main_panel = ft.Container(
            expand=2,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            margin=ft.margin.only(left=10, right=10, top=2, bottom=10),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Device Manager", size=20, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(icon=Icons.MORE_VERT, icon_color="white"),
                        ],
                    ),
                    self.create_ports_section(),
                    self.create_camera_microphone_section(),
                    self.create_connected_devices_section(),
                ],
            ),
        )

        right_panel = ft.Container(
            expand=1,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=15,
            margin=ft.margin.only(right=10, top=2, bottom=10),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Device Usage Log", size=20, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(icon=Icons.MORE_VERT, icon_color="white"),
                        ],
                    ),
                    # Additional log content can be added here
                ],
            ),
        )

        return ft.Row(
            controls=[main_panel, right_panel],
            spacing=0,
            expand=True
        )
