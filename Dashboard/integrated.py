import flet as ft
import os
from flet import Icons, BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur, Stack, ImageFit, ImageRepeat
from proc_chain import create_process_chains_layout, start_proc_chain_updates
from network_monitor import create_network_monitoring_layout
class DesktopApp:
    def __init__(self):
        # Initialize all the common properties
        self.window_width = 1280
        self.window_height = 720
        self.min_width = 800
        self.min_height = 450
        self.dark_bg = "#1a1b26"
        self.dark_card = "#20212e"
        self.accent_color = "#00ffff"
        self.text_color = "#ffffff"
        self.selected_tab_index = 0
        self.sidebar_expanded = False
        self.sidebar_width = 50
        self.sidebar_expanded_width = 150
        
        # Device Manager specific properties
        self.port_start_index = 0
        self.total_ports = 10
        self.visible_ports = 3
        self.ports_row = None
        self.ports_container_ref = ft.Ref[ft.Container]()
        self.all_ports = [{"id": i+1, "state": False} for i in range(self.total_ports)]
        
        # Device navigation state
        self.device_start_index = 0
        self.total_devices = 10
        self.visible_devices = 3
        self.devices_container_ref = ft.Ref[ft.Container]()
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
        
        # Camera and Microphone state
        self.camera_state = False
        self.microphone_state = False
        
        # Glass effect properties
        self.glass_bgcolor = "#20f4f4f4"
        self.container_blur = Blur(10, 10, BlurTileMode.REPEATED)
        self.container_shadow = BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=Colors.BLACK54,
            offset=Offset(2, 2),
            blur_style=ShadowBlurStyle.OUTER
        )
        
        # Path setup
        self.base_path = r"C:\Users\mannp\Downloads\Task\assets"
        self.bg_image_path = os.path.join(self.base_path, "Background.png")
        
        self.svg_icons = {
            "process_monitor": os.path.join(self.base_path, "Process.svg"),
            "system_commands": os.path.join(self.base_path, "system_commands.svg"),
            "network": os.path.join(self.base_path, "Network.svg"),
            "scheduled": os.path.join(self.base_path, "scheduled.svg"),
            "process_chains": os.path.join(self.base_path, "Chaining.svg"),
            "device_manager": os.path.join(self.base_path, "device_manager.svg"),
            "system_logs": os.path.join(self.base_path, "systemlog.svg"),
        }

    def get_tab_content(self):
        """Return the appropriate content based on selected tab"""
        if self.selected_tab_index == 2:  # Network Connections tab
            return create_network_monitoring_layout(
                glass_bgcolor=self.glass_bgcolor,
                container_blur=self.container_blur,
                container_shadow=self.container_shadow
            )
        elif self.selected_tab_index == 5:  # Device Manager tab
            return self.create_device_manager_content()
        elif self.selected_tab_index == 4:
            layout, dashboard = create_process_chains_layout(
                glass_bgcolor=self.glass_bgcolor,
                container_blur=self.container_blur,
                container_shadow=self.container_shadow
            )
            # Optionally, store dashboard if needed for later updates.
            # Start periodic updates for the process chains dashboard.
            start_proc_chain_updates(self.page, dashboard)
            return layout
            
        else:
            return ft.Container(
                content=ft.Text("Coming Soon...", size=20, color="white"),
                alignment=ft.alignment.center,
                expand=True
            )



    # [All Device Manager methods from the previous implementation]
    def next_ports(self, e):
        if self.port_start_index + self.visible_ports < self.total_ports:
            self.port_start_index = min(
                self.port_start_index + self.visible_ports, 
                self.total_ports - self.visible_ports
            )
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

    def next_devices(self, e):
        if self.device_start_index + self.visible_devices < self.total_devices:
            self.device_start_index = min(
                self.device_start_index + self.visible_devices,
                self.total_devices - self.visible_devices
            )
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
                                fit=ft.ImageFit.CONTAIN,
                            ),
                            ft.Text(
                                "USB Type A", 
                                color="white", 
                                size=12,
                                weight=ft.FontWeight.W_500
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Status:", 
                                        color="white", 
                                        size=10,
                                        width=50
                                    ),
                                    ft.Text(
                                        "On" if current_port_state else "Off", 
                                        color="white", 
                                        size=10
                                    )
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
                            ft.Text(
                                "Connected" if current_port_state else "Not Connected", 
                                color="white", 
                                size=10
                            ),
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
        self.ports_row = ft.Row(
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
                    controls=[
                        self.create_port_info_container(i) for i in range(self.visible_ports)
                    ],
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
        return self.ports_row
    
    def create_ports_section(self):
        """Create the ports section for device manager"""
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

    def toggle_port(self, e, port_index):
        actual_index = self.port_start_index + port_index
        self.all_ports[actual_index]["state"] = e.control.value
        new_ports_row = self.create_ports_row()
        if self.ports_container_ref.current:
            self.ports_container_ref.current.content.controls[1] = new_ports_row
            e.page.update()

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

        camera_status = ft.Text(
            "Off", 
            color="white", 
            size=12,
            weight=ft.FontWeight.W_500
        )
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
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text(
                        "Camera", 
                        color="white", 
                        size=14,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Status:", 
                                color="white", 
                                size=12
                            ),
                            camera_status
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        controls=[camera_toggle],
                        alignment=ft.MainAxisAlignment.START, 
                    )
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

        # Microphone Container
        mic_status = ft.Text(
            "Off", 
            color="white", 
            size=12,
            weight=ft.FontWeight.W_500
        )
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
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text(
                        "Microphone", 
                        color="white", 
                        size=14,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Status:", 
                                color="white", 
                                size=12
                            ),
                            mic_status
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(
                        controls=[mic_toggle],
                        alignment=ft.MainAxisAlignment.START,
                    )
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

        # Camera and Microphone Section
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

    def create_device_manager_content(self):
        """Create the device manager tab content"""
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
                            ft.Text(
                                "Device Manager",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=Icons.MORE_VERT,
                                icon_color="white",
                            ),
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
                            ft.Text(
                                "Device Usage Log",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=Icons.MORE_VERT,
                                icon_color="white",
                            ),
                        ],
                    ),
                ],
            ),
        )
        
        return ft.Row(
            controls=[main_panel, right_panel],
            spacing=0,
            expand=True
        )

    def create_tab_item(self, icon_path, label, index):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Image(
                        src=icon_path,
                        width=24,
                        height=24,
                        color="white" if index != self.selected_tab_index else self.accent_color,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    tooltip=ft.Tooltip(
                        message=label,
                        bgcolor="#08CDFF",
                        text_style=ft.TextStyle(color="white"),
                        padding=10,
                    ) if not self.sidebar_expanded else None,
                    margin=ft.margin.only(left=0),
                    width=24,
                    height=24,
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=ft.Text(
                        label,
                        size=10,
                        color="white" if index != self.selected_tab_index else self.accent_color,
                        weight=ft.FontWeight.W_500,
                        overflow=ft.TextOverflow.CLIP,
                        max_lines=2,
                    ),
                    visible=self.sidebar_expanded,
                    padding=ft.padding.only(left=-5),
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=self.glass_bgcolor if index == self.selected_tab_index else None,
            blur=self.container_blur if index == self.selected_tab_index else None,
            shadow=self.container_shadow if index == self.selected_tab_index else None,
            border_radius=0,
            border=ft.border.all(1, self.accent_color) if index == self.selected_tab_index else None,
            width=self.sidebar_expanded_width if self.sidebar_expanded else self.sidebar_width,
            height=50,
            on_click=lambda e, idx=index: self.change_tab(e, idx),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )

    def toggle_sidebar(self, e):
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_tabs.controls = [
            self.create_tab_item(icon_path, label, i) 
            for i, (icon_path, label) in enumerate(self.tabs_data)
        ]
        self.left_sidebar.width = self.sidebar_expanded_width if self.sidebar_expanded else self.sidebar_width
        e.page.update()

    def change_tab(self, e, index):
        """Modified change_tab method to handle content switching"""
        self.selected_tab_index = index
        
        # Update tab styling
        for i, tab in enumerate(self.sidebar_tabs.controls):
            if i == index:
                tab.bgcolor = self.glass_bgcolor
                tab.blur = self.container_blur
                tab.shadow = self.container_shadow
                tab.content.controls[0].content.color = self.accent_color
                if len(tab.content.controls) > 1:
                    tab.content.controls[1].content.color = self.accent_color
                tab.border = ft.border.all(1, self.accent_color)
            else:
                tab.bgcolor = None
                tab.blur = None
                tab.shadow = None
                tab.content.controls[0].content.color = "white"
                if len(tab.content.controls) > 1:
                    tab.content.controls[1].content.color = "white"
                tab.border = None
        
        # Update main content
        if hasattr(self, 'main_content_container'):
            self.main_content_container.content = self.get_tab_content()
        
        e.page.update()

    def main(self, page: ft.Page):
        self.page = page
        page.window_width = self.window_width
        page.window_height = self.window_height
        page.window_min_width = self.min_width
        page.window_min_height = self.min_height
        page.padding = 0
        page.theme_mode = ft.ThemeMode.DARK
        
        # Create background image container
        background = ft.Container(
            expand=True,
            image_src=self.bg_image_path,
            image_fit=ft.ImageFit.COVER,
            image_repeat=ft.ImageRepeat.NO_REPEAT,
        )
        
        # Initialize tabs
        self.tabs_data = [
            (self.svg_icons["process_monitor"], "Process Monitor"),
            (self.svg_icons["system_commands"], "System Commands"),
            (self.svg_icons["network"], "Network Connections"),
            (self.svg_icons["scheduled"], "Scheduled Processes"),
            (self.svg_icons["process_chains"], "Process Chains"),
            (self.svg_icons["device_manager"], "Device Manager"),
            (self.svg_icons["system_logs"], "System Logs"),
        ]

        # Create sidebar tabs
        self.sidebar_tabs = ft.Column(
            controls=[
                self.create_tab_item(icon_path, label, i) 
                for i, (icon_path, label) in enumerate(self.tabs_data)
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.START,
        )

        # Toggle button for sidebar
        toggle_button = ft.IconButton(
            icon=Icons.MENU,
            icon_color="white",
            icon_size=20,
            on_click=self.toggle_sidebar,
        )

        # Left sidebar container
        self.left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=toggle_button,
                        padding=ft.padding.only(left=2, top=5, bottom=5),
                        alignment=ft.alignment.center_left,
                    ),
                    self.sidebar_tabs,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=self.sidebar_width,
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=ft.border_radius.only(top_right=15),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

        # Top bar with logo, search, notifications, and profile
        top_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=os.path.join(self.base_path, "logo.png"),
                        width=75,
                        height=75,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(Icons.SEARCH, color='#6c757d', size=20),
                                ft.TextField(
                                    border=ft.InputBorder.NONE,
                                    height=40,
                                    text_size=14,
                                    bgcolor='transparent',
                                    color='white',
                                    hint_text="Search...",
                                    hint_style=ft.TextStyle(color='#6c757d'),
                                    expand=True,
                                    content_padding=ft.padding.only(left=10, right=10),
                                )
                            ],
                            spacing=10,
                        ),
                        bgcolor=self.glass_bgcolor,
                        blur=self.container_blur,
                        border_radius=20,
                        padding=ft.padding.only(left=15, right=15),
                        expand=True,
                    ),
                    ft.Stack([
                        ft.IconButton(
                            icon=Icons.NOTIFICATIONS_OUTLINED,
                            icon_color='white',
                            icon_size=24,
                            tooltip="Notifications",
                        ),
                    ]),
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text("MP"),
                            bgcolor="#00008B",
                            radius=16,
                        ),
                        ft.Text("Mann Pandya", color="white", size=14),
                        ft.Icon(Icons.ARROW_DROP_DOWN, color="white"),
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=15,
            ),
            padding=ft.padding.only(left=5, right=20, top=0),
            margin=ft.margin.only(top=-10)
        )

        # Create main content container that will be updated with tab changes
        self.main_content_container = ft.Container(
            content=self.get_tab_content(),
            expand=True,
        )

        # Assemble main layout
        main_content = ft.Row(
            controls=[
                self.left_sidebar,
                self.main_content_container,
            ],
            spacing=0,
            expand=True,
        )

        # Content container
        content = ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    top_bar,
                    main_content,
                ],
                spacing=0,
                expand=True,
            ),
        )

        # Final page assembly with background and content in Stack
        page.add(
            ft.Stack(
                controls=[
                    background,  # Background layer
                    content,     # Content layer
                ],
                expand=True,
            )
        )
        
        page.update()

def main(page: ft.Page):
    app = DesktopApp()
    app.main(page)

if __name__ == '__main__':
    ft.app(target=main)