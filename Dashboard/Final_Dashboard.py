import flet as ft
from flet import Icons, BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur, Stack, ImageFit, ImageRepeat

class DesktopApp:
    def __init__(self):
        self.window_width = 1280
        self.window_height = 720
        self.min_width = 800
        self.min_height = 450
        self.dark_bg = "#1a1b26"
        self.dark_card = "#20212e"
        self.accent_color = "#00ffff"
        self.text_color = "#ffffff"
        self.selected_tab_index = 0
        self.port_start_index = 0
        self.total_ports = 10
        self.visible_ports = 5
        self.ports_row = None
        self.all_ports = [{"id": i+1, "state": False} for i in range(self.total_ports)]
        self.sidebar_expanded = False
        self.sidebar_width = 50 # Default collapsed width
        self.sidebar_expanded_width = 190# width when expanded
        
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
        
        # Background image path
        self.bg_image_path = r"C:\Users\mannp\Downloads\25002f46-9c5e-4ca4-9d3c-d11f6fca60b1.png"
        
        self.svg_icons = {
            "process_monitor": r"C:\Users\mannp\Downloads\Task\assets\Process.svg",
            "system_commands": r"C:\Users\mannp\Downloads\Task\assets\system_commands.svg",
            "network": r"C:\Users\mannp\Downloads\Task\assets\Network.svg",
            "scheduled": r"C:\Users\mannp\Downloads\Task\assets\scheduled.svg",
            "process_chains": r"C:\Users\mannp\Downloads\Task\assets\Chaining.svg",
            "device_manager": r"C:\Users\mannp\Downloads\Task\assets\device_manager.svg",
        }

    def next_ports(self, e):
        if self.port_start_index + self.visible_ports < self.total_ports:
            for port in self.ports_row.controls[1:-1]:
                port.offset = ft.transform.Offset(-1, 0)
                port.opacity = 0
                e.page.update()
                self.port_start_index = min(self.port_start_index + self.visible_ports, self.total_ports - self.visible_ports)
                self.update_ports()
            for port in self.ports_row.controls[1:-1]:
                port.offset = ft.transform.Offset(0, 0)
                port.opacity = 1
                e.page.update()
                
    def prev_ports(self, e):
        if self.port_start_index > 0:
         for port in self.ports_row.controls[1:-1]:
                port.offset = ft.transform.Offset(1, 0)
                port.opacity = 0
                e.page.update()
                self.port_start_index = max(0, self.port_start_index - self.visible_ports)
                self.update_ports()
                for port in self.ports_row.controls[1:-1]:
                    port.offset = ft.transform.Offset(0, 0)
                    port.opacity = 1
                    e.page.update()

    def update_ports(self):
        current_ports = self.ports_row.controls[1:-1]
        for i, port in enumerate(current_ports):
            port_number = self.port_start_index + i
            if port_number < self.total_ports:
                port.visible = True
                port.content.controls[1].value = f"Port {port_number + 1}"
                port.content.controls[2].content.value = self.all_ports[port_number]["state"]
                port.opacity = 1  # Add this line
            else:
                port.visible = False

        self.ports_row.controls[0].content.disabled = self.port_start_index == 0
        self.ports_row.controls[-1].content.disabled = self.port_start_index + self.visible_ports >= self.total_ports

    def toggle_port(self, e, port_index):
        actual_index = self.port_start_index + port_index
        self.all_ports[actual_index]["state"] = e.control.value
        e.page.update()

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
                padding=ft.padding.only(right=5),
            ),
            *[
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(Icons.USB, 
                            color="white", 
                            size=28),
                            margin=ft.margin.only(bottom=2),
                        ),
                        ft.Text(f"Port {self.port_start_index + i + 1}", 
                        color="white", 
                        size=13,
                        weight=ft.FontWeight.W_500),
                        ft.Container(
                            content=ft.Switch(
                                value=self.all_ports[self.port_start_index + i]["state"],
                                active_color=self.accent_color,
                                scale=1.1,
                                on_change=lambda e, i=i: self.toggle_port(e, i),
                            ),
                            margin=ft.margin.only(top=-5),
                        ),
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    ),
                    bgcolor=self.glass_bgcolor,
                    blur=self.container_blur,
                    shadow=self.container_shadow,
                    border_radius=10,
                    padding=ft.padding.all(15),
                    width=90,
                    height=120,
                    margin=ft.margin.symmetric(horizontal=15),
                    offset=ft.transform.Offset(0, 0),
                    animate_offset=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
                    animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
                ) for i in range(self.visible_ports)
            ],
            ft.Container(
                content=ft.IconButton(
                    icon=Icons.ARROW_FORWARD_IOS,
                    icon_color="white",
                    icon_size=20,
                    on_click=self.next_ports,
                    disabled=self.port_start_index + self.visible_ports >= self.total_ports,
                ),
                padding=ft.padding.only(left=5),
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )
        return self.ports_row

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
                    bgcolor="black",
                    text_style=ft.TextStyle(color="lightblue"),
                    padding=10,
                ) if not self.sidebar_expanded else None,
                margin=ft.margin.only(left=0),
                width=24,  # Set a fixed width for the logo container
                height=24,  # Set a fixed height for the logo container
                alignment=ft.alignment.center,  # Center the logo within the container
            ),
            ft.Container(
                content=ft.Text(
                    label,
                    size=14,
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
    # Recreate sidebar tabs
        self.sidebar_tabs.controls = [
        self.create_tab_item(icon_path, label, i) 
        for i, (icon_path, label) in enumerate(self.tabs_data)
    ]
    # Update sidebar width
        self.left_sidebar.width = self.sidebar_expanded_width if self.sidebar_expanded else self.sidebar_width
        e.page.update()

    def change_tab(self, e, index):
        self.selected_tab_index = index
        for i, tab in enumerate(self.sidebar_tabs.controls):
            if i == index:
                tab.bgcolor = self.glass_bgcolor
                tab.blur = self.container_blur
                tab.shadow = self.container_shadow
                tab.content.controls[0].content.color = self.accent_color
                tab.content.controls[1].color = self.accent_color
                tab.border = ft.border.all(1, self.accent_color)
            else:
                tab.bgcolor = None
                tab.blur = None
                tab.shadow = None
                tab.content.controls[0].content.color = "white"
                tab.content.controls[1].color = "white"
                tab.border = None
        e.page.update()

    def main(self, page: ft.Page):
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
        
        self.tabs_data = [
            (self.svg_icons["process_monitor"], "Process Monitor"),
            (self.svg_icons["system_commands"], "System Commands"),
            (self.svg_icons["network"], "Network Connections"),
            (self.svg_icons["scheduled"], "Scheduled Processes"),
            (self.svg_icons["process_chains"], "Process Chains"),
            (self.svg_icons["device_manager"], "Device Manager"),
        ]

        self.sidebar_tabs = ft.Column(
            controls=[
                self.create_tab_item(icon_path, label, i) 
                for i, (icon_path, label) in enumerate(self.tabs_data)
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.START,
        )

        # Add toggle button at the top of sidebar
        toggle_button = ft.IconButton(
            icon=Icons.MENU,
            icon_color="white",
            icon_size=20,
            on_click=self.toggle_sidebar,
        )

        self.left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=toggle_button,
                        padding=ft.padding.only(left=2, top=10, bottom=10),  # Adjust padding
                        alignment=ft.alignment.center_left,  # Change alignment
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
                                "Dashboard",
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
                    ft.Container(height=20),
                    # Ports Section
                    ft.Container(
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
                    ),
                    # Device Controls
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Device Controls", size=16, weight=ft.FontWeight.BOLD, color="white"),
                                ft.Container(expand=True),
                            ]),
                            ft.Container(height=15),
                            ft.Row(
                                controls=[
                                    # Camera Control
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Container(
                                                content=ft.Icon(Icons.CAMERA_ALT, color="white", size=40),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                content=ft.Text("Camera", color="white", size=14, weight=ft.FontWeight.W_500),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                content=ft.Switch(
                                                    value=False,
                                                    active_color=self.accent_color,
                                                    scale=1.2,
                                                ),
                                                alignment=ft.alignment.center,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=15,
                                        ),
                                        bgcolor=self.glass_bgcolor,
                                        blur=self.container_blur,
                                        shadow=self.container_shadow,
                                        border_radius=10,
                                        expand=True,
                                        height=160,
                                    ),
                                    ft.Container(width=15),
                                    # Microphone Control
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Container(
                                                content=ft.Icon(Icons.MIC, color="white", size=40),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                content=ft.Text("Microphone", color="white", size=14, weight=ft.FontWeight.W_500),
                                                alignment=ft.alignment.center,
                                            ),
                                            ft.Container(
                                                content=ft.Switch(
                                                    value=False,
                                                    active_color=self.accent_color,
                                                    scale=1.2,
                                                ),
                                                alignment=ft.alignment.center,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=15,
                                        ),
                                        bgcolor=self.glass_bgcolor,
                                        blur=self.container_blur,
                                        shadow=self.container_shadow,
                                        border_radius=10,
                                        expand=True,
                                        height=160,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                expand=True),
                        ]),
                        bgcolor=self.glass_bgcolor,
                        blur=self.container_blur,
                        shadow=self.container_shadow,
                        border_radius=10,
                        padding=15,
                        margin=ft.margin.only(bottom=15),
                    ),
                    # Connected Devices
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Connected Devices", size=16, weight=ft.FontWeight.BOLD, color="white"),
                                ft.Container(expand=True),
                            ]),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=Icons.ARROW_BACK_IOS,
                                        icon_color="white",
                                        icon_size=20,
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Icon(Icons.BLUETOOTH, color="white", size=24),
                                            ft.Text("Bluetooth", color="white", size=12),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=5,
                                        ),
                                        bgcolor=self.glass_bgcolor,
                                        blur=self.container_blur,
                                        shadow=self.container_shadow,
                                        border_radius=10,
                                        padding=5,
                                        width=90,
                                        height=80,
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Icon(Icons.KEYBOARD, color="white", size=24),
                                            ft.Text("Keyboard", color="white", size=12),
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
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Icon(Icons.MOUSE, color="white", size=24),
                                            ft.Text("Mouse", color="white", size=12),
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
                                    ),
                                    ft.IconButton(
                                        icon=Icons.ARROW_FORWARD_IOS,
                                        icon_color="white",
                                        icon_size=20,
                                    ),
                                ],
                                spacing=90,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ]),
                        bgcolor=self.glass_bgcolor,
                        blur=self.container_blur,
                        shadow=self.container_shadow,
                        border_radius=10,
                        padding=15,
                    ),
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

        # Replace the top_bar definition with this:
        top_bar = ft.Container(
            content=ft.Row(
                controls=[
                    # Logo
                    ft.Image(
                        src=r"C:\Users\mannp\Downloads\Task\assets\logo.png",
                        width=75,
                        height=75,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    
                    # Search Box
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
                    
                    # Notification Bell with Counter
                    ft.Stack([
                        ft.IconButton(
                            icon=Icons.NOTIFICATIONS_OUTLINED,
                            icon_color='white',
                            icon_size=24,
                            tooltip="Notifications",
                        ),
                    ]),
                    
                    # Profile Section
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
            margin=ft.margin.only(top=-10)  # Add negative top margin
        )
        
        main_content = ft.Row(
            controls=[
                self.left_sidebar,
                ft.Container(
                    content=ft.Row(
                        controls=[main_panel, right_panel],
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        # Create content container
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
                    content,    # Content layer
                ],
                expand=True,
            )
        )
        
        page.update()

if __name__ == '__main__':
    app = DesktopApp()
    ft.app(target=app.main)