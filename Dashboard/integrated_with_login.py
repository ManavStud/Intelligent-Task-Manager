import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable
from flet import Icons, BlurTileMode, Colors, BoxShadow, ShadowBlurStyle, Offset, Blur
import os
import random
import sqlite3
from datetime import datetime

@dataclass
class User:
    email: str
    name: str
    is_authenticated: bool = False

def send_email_otp(email: str, otp: str):
    """Simulated email-sending; replace with real email logic."""
    print(f"Sending OTP {otp} to {email}")

class DBManager:
    """
    A simple SQLite-based database manager for user authentication.
    Creates a 'users' table if it doesn't exist.
    """

    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self._setup_db()

    def _setup_db(self):
        """Create the 'users' table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    verified INTEGER DEFAULT 0,
                    otp TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def create_user(self, name: str, email: str, password: str, otp: str):
        """Insert a new user record."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (name, email, password, verified, otp, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, password, 0, otp, datetime.utcnow().isoformat()+"Z"))
            conn.commit()

    def find_user_by_email(self, email: str):
        """Fetch a user record by email."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            row = c.fetchone()
            if row:
                # row -> (id, name, email, password, verified, otp, created_at)
                return {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "password": row[3],
                    "verified": bool(row[4]),
                    "otp": row[5],
                    "created_at": row[6],
                }
            return None

    def update_user_verification(self, user_id: int, verified: bool, new_otp: Optional[str] = None):
        """Update user verification status and optionally reset OTP."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE users
                   SET verified = ?,
                       otp = ?
                 WHERE id = ?
            """, (1 if verified else 0, new_otp, user_id))
            conn.commit()

class IntegratedApp:
    def __init__(self):
        # Instantiate DB manager
        self.db = DBManager("app.db")

        # Login page settings
        self.login_width = 960
        self.login_height = 540
        self.min_width = 800
        self.min_height = 450
        self.accent_color = "#ffffff"
        self.glass_color = "rgba(30, 30, 30, 0.5)"
        self.glow_color = "#4fb4ff"
        self.neon_blue = "#00F5FF"
        self.light_blue = "#87CEFA"
        self.dark_bg = "#0A0A0A"
        self.is_right_panel_active = False

        # Dashboard settings
        self.window_width = 1280
        self.window_height = 720
        self.dashboard_dark_bg = "#1a1b26"
        self.dashboard_dark_card = "#20212e"
        self.dashboard_accent_color = "#00ffff"
        self.text_color = "#ffffff"
        self.selected_tab_index = 0
        self.port_start_index = 0
        self.total_ports = 10
        self.visible_ports = 5
        self.ports_row = None
        self.all_ports = [{"id": i+1, "state": False} for i in range(self.total_ports)]
        self.sidebar_expanded = False
        self.sidebar_width = 50
        self.sidebar_expanded_width = 190

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

        # Background image path - Update this path
        self.bg_image_path = r"C:\Users\mannp\Downloads\Task\assets\Background.png"

        # SVG icons - Update these paths
        self.svg_icons = {
            "process_monitor": r"C:\Users\mannp\Downloads\Task\assets\Process.svg",
            "system_commands": r"C:\Users\mannp\Downloads\Task\assets\system_commands.svg",
            "network": r"C:\Users\mannp\Downloads\Task\assets\Network.svg",
            "scheduled": r"C:\Users\mannp\Downloads\Task\assets\scheduled.svg",
            "process_chains": r"C:\Users\mannp\Downloads\Task\assets\Chaining.svg",
            "device_manager": r"C:\Users\mannp\Downloads\Task\assets\device_manager.svg",
        }

        # Shared state
        self.current_user: Optional[User] = None
        self.current_view: Optional[ft.View] = None
        self.page: Optional[ft.Page] = None

        # OTP / registration helper fields
        self.current_reg_email: Optional[str] = None
        self.signup_name: Optional[ft.TextField] = None
        self.signup_email: Optional[ft.TextField] = None
        self.signup_password: Optional[ft.TextField] = None
        self.otp_field: Optional[ft.TextField] = None
        self.otp_overlay: Optional[ft.Container] = None

        # Initialize dashboard components
        self.initialize_dashboard_components()
    def create_gmail_button(self):
        """Creates Gmail sign-in button"""
        return ft.IconButton(
            icon=ft.icons.MAIL,
            icon_color="white",
            icon_size=20,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                side=ft.BorderSide(1, "rgba(255,255,255,0.2)"),
            ),
        )
    def show_login(self):
        """Display login view"""
        login_view = ft.View(
            route="/login",
            controls=[self.create_login_ui()],
            bgcolor=self.dark_bg,
            padding=0
        )
        self.page.views.clear()
        self.page.window_width = self.login_width
        self.page.window_height = self.login_height
        self.page.window_min_width = self.min_width
        self.page.window_min_height = self.min_height
        self.page.views.append(login_view)
        self.page.update()

    def initialize_dashboard_components(self):
        """Initialize all dashboard-related components and state"""
        self.tabs_data = [
            (self.svg_icons["process_monitor"], "Process Monitor"),
            (self.svg_icons["system_commands"], "System Commands"),
            (self.svg_icons["network"], "Network Connections"),
            (self.svg_icons["scheduled"], "Scheduled Processes"),
            (self.svg_icons["process_chains"], "Process Chains"),
            (self.svg_icons["device_manager"], "Device Manager"),
        ]

    def create_wavy_rays(self, width, height):
        """Creates wavy background effect for login page"""
        return ft.Container(
            width=width,
            height=height,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[self.neon_blue, self.light_blue],
                stops=[0.3, 0.7],
                rotation=135,
                tile_mode=ft.GradientTileMode.MIRROR
            ),
            blur=20,
            opacity=0.4,
            animate_opacity=ft.animation.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        )

    def initialize_page(self, page: ft.Page):
        """Initialize the application page"""
        self.page = page
        page.title = "Integrated App (DB Version)"
        page.padding = 0
        page.theme_mode = ft.ThemeMode.DARK
        page.window_bgcolor = self.dark_bg

        # Show login on startup
        self.show_login()

    # ----------------- DB-based Auth Methods ----------------- #
    def db_login(self, email: str, password: str) -> bool:
        """Attempt to log in a user from the DB, checking verification."""
        user = self.db.find_user_by_email(email)
        if user and user["password"] == password and user["verified"]:
            self.current_user = User(
                email=user["email"],
                name=user["name"] or email.split('@')[0].title(),
                is_authenticated=True
            )
            return True
        return False

    def db_registration_submit(self):
        """Handle user registration with OTP verification using DB."""
        name = self.signup_name.value.strip()
        email = self.signup_email.value.strip()
        password = self.signup_password.value.strip()

        if not name or not email or not password:
            self.show_message("All fields are required for registration.")
            return

        existing_user = self.db.find_user_by_email(email)
        if existing_user is not None:
            self.show_message("This email is already registered.")
            return

        otp = str(random.randint(100000, 999999))
        # Create the user in DB
        self.db.create_user(name, email, password, otp)

        # Simulate sending OTP
        send_email_otp(email, otp)

        # Store current registration email to verify
        self.current_reg_email = email
        self.show_message(f"OTP sent to {email}. Please verify your email.")
        if self.otp_overlay:
            self.otp_overlay.visible = True
        self.page.update()

    def db_verify_otp_submit(self, e):
        """Handle OTP verification submission using DB."""
        entered_otp = self.otp_field.value.strip()
        user = self.db.find_user_by_email(self.current_reg_email) if self.current_reg_email else None
        if user is None:
            self.show_message("User not found.")
        else:
            if entered_otp == user["otp"]:
                self.db.update_user_verification(user_id=user["id"], verified=True, new_otp=None)
                self.show_message("Email verified successfully!")
                if self.otp_overlay:
                    self.otp_overlay.visible = False
            else:
                self.show_message("Invalid OTP. Please try again.")
        self.page.update()

    # ----------------- UI-Level Auth Handling ----------------- #
    def handle_login_submit(self, email: str, password: str, on_error: Callable):
        """Handle login form submission using DB."""
        user = self.db.find_user_by_email(email)

        if user is None:
            on_error("Email not registered. Please sign up.")
        elif user["password"] != password:
            on_error("Invalid email or password.")
        elif not user["verified"]:
            on_error("Email not verified. Please complete OTP verification.")
        else:
            # Mark current user
            self.current_user = User(
                email=user["email"],
                name=user["name"],
                is_authenticated=True
            )
            self.show_dashboard()

    def handle_logout(self, e):
        """Handle user logout"""
        self.current_user = None
        self.show_login()

    # ----------------- Common UI Helpers ----------------- #
    def show_message(self, msg: str):
        """Display a SnackBar message."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()

    def create_floating_text_field(self, label, password=False):
        """Creates a floating label text field"""
        return ft.TextField(
            label=label,
            password=password,
            bgcolor="rgba(44, 44, 44, 0.3)",
            color="white",
            border=ft.InputBorder.OUTLINE,
            width=280,
            height=50,
            text_size=14,
            cursor_color="white",
            label_style=ft.TextStyle(
                color="#9e9e9e",
                size=14,
            ),
        )

    # ----------------- Login / Registration UI ----------------- #
    def create_login_ui(self):
        """Create the login and registration UI (two forms + overlay)."""

        # Fields for the Sign In form
        email_field = self.create_floating_text_field("Email")
        password_field = self.create_floating_text_field("Password", password=True)
        error_text = ft.Text("", color="red", size=12)

        # On submit for Sign In
        def handle_submit(e):
            error_text.value = ""
            self.handle_login_submit(
                email_field.value,
                password_field.value,
                lambda msg: setattr(error_text, 'value', msg),
            )
            self.page.update()

        # Toggle between Sign In and Sign Up forms
        def toggle_panel(e):
            self.is_right_panel_active = not self.is_right_panel_active
            if self.is_right_panel_active:
                overlay_container.left = 0
                signup_form.left = 320
                signin_form.left = -320
            else:
                overlay_container.left = 320
                signup_form.left = 640
                signin_form.left = 0
            self.page.update()

        def create_logo(alignment):
            return ft.Container(
                content=ft.Image(
                    src=r"C:\Users\mannp\Downloads\Task\assets\logo.png",  # Update this path
                    width=75,
                    height=50,
                    fit=ft.ImageFit.CONTAIN,
                ),
                alignment=alignment,
            )

        # Sign In Form
        signin_form = ft.Container(
            content=ft.Column(
                controls=[
                    create_logo(ft.alignment.top_left),
                    ft.Text("Sign In", size=24, weight=ft.FontWeight.BOLD, color="white"),
                    self.create_gmail_button(),
                    email_field,
                    password_field,
                    error_text,
                    ft.TextButton(
                        text="Forgot Password?",
                        style=ft.ButtonStyle(
                            color="lightblue",
                            padding=ft.Padding(0, 5, 0, 0)
                        ),
                    ),
                    ft.ElevatedButton(
                        text="SIGN IN",
                        style=ft.ButtonStyle(
                            bgcolor={"": "rgba(44, 44, 44, 0.7)"},
                            shape=ft.RoundedRectangleBorder(radius=20),
                        ),
                        color="white",
                        height=40,
                        width=160,
                        on_click=handle_submit,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            width=320,
            height=450,
            bgcolor=self.glass_color,
            border_radius=10,
            border=ft.border.all(1, "rgba(255, 255, 255, 0.2)"),
            left=0,
            blur=10,
            animate_position=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )

        # Sign Up Form with Confirm Password and real-time validation
        self.signup_name = self.create_floating_text_field("Name")
        self.signup_email = self.create_floating_text_field("Email")
        self.signup_password = self.create_floating_text_field("Password", password=True)
        self.signup_confirm_password = self.create_floating_text_field("Confirm Password", password=True)

        # "Get OTP" button, initially disabled until validations pass.
        self.get_otp_button = ft.ElevatedButton(
            text="Get OTP",
            style=ft.ButtonStyle(
                bgcolor={"": "rgba(44, 44, 44, 0.7)"},
                shape=ft.RoundedRectangleBorder(radius=20),
            ),
            color="white",
            height=40,
            width=160,
            disabled=True,
            on_click=lambda e: self.db_registration_submit(),
        )

        # Real-time validation for sign-up fields
        def check_signup_fields(e):
            name = self.signup_name.value.strip()
            email = self.signup_email.value.strip()
            password = self.signup_password.value.strip()
            confirm_password = self.signup_confirm_password.value.strip()

            import re
            email_valid = re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None
            password_valid = len(password) == 8 and password.isalnum()
            password_match = password == confirm_password

            # Update error messages based on validations
            self.signup_email.error_text = "Invalid email format" if email and not email_valid else None
            self.signup_password.error_text = "Password must be 8 alphanumeric characters" if password and not password_valid else None
            self.signup_confirm_password.error_text = "Passwords do not match" if confirm_password and not password_match else None

            # Enable Get OTP button only if all fields are non-empty and valid
            if name and email and password and confirm_password and email_valid and password_valid and password_match:
                self.get_otp_button.disabled = False
            else:
                self.get_otp_button.disabled = True

            self.page.update()

        # Attach on_change events to trigger real-time validation
        self.signup_name.on_change = check_signup_fields
        self.signup_email.on_change = check_signup_fields
        self.signup_password.on_change = check_signup_fields
        self.signup_confirm_password.on_change = check_signup_fields

        signup_form = ft.Container(
            content=ft.Column(
                controls=[
                    create_logo(ft.alignment.top_right),
                    ft.Text("Create Account", size=24, weight=ft.FontWeight.BOLD, color="white"),
                    self.create_gmail_button(),
                    self.signup_name,
                    self.signup_email,
                    self.signup_password,
                    self.signup_confirm_password,
                    self.get_otp_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            width=320,
            height=500,  # Increased height for the additional field
            bgcolor=self.glass_color,
            border_radius=10,
            border=ft.border.all(1, "rgba(255, 255, 255, 0.2)"),
            left=640,
            blur=10,
            animate_position=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )

        # Overlay Container (toggle sign up)
        overlay_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Hello, Friend!", size=24, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Enter your details to join us", size=14, color="#9e9e9e"),
                    ft.ElevatedButton(
                        text="SIGN UP",
                        style=ft.ButtonStyle(
                            bgcolor={"": ft.colors.TRANSPARENT},
                            shape=ft.RoundedRectangleBorder(radius=20),
                            side=ft.BorderSide(2, "white"),
                        ),
                        color="white",
                        height=40,
                        width=160,
                        on_click=toggle_panel,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15,
            ),
            width=320,
            height=450,
            left=320,
            bgcolor="rgba(0, 0, 0, 0.5)",
            border_radius=10,
            blur=10,
            animate_position=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )

        # --- OTP Verification Overlay (initially hidden) ---
        self.otp_overlay = self.create_otp_overlay()

        # Main Container (Stacked UI)
        main_container = ft.Container(
            content=ft.Stack(
                controls=[
                    self.create_wavy_rays(640, 450),
                    signin_form,
                    signup_form,
                    overlay_container,
                    self.otp_overlay,  # OTP overlay on top
                ],
            ),
            width=640,
            height=450,
            bgcolor=self.dark_bg,
            border_radius=10,
            border=ft.border.all(2, self.glow_color),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.colors.with_opacity(0.5, self.glow_color),
                offset=ft.Offset(0, 0),
            ),
        )

        return ft.Container(
            content=ft.Container(
                content=main_container,
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=self.dark_bg,
            ),
            expand=True,
            bgcolor=self.dark_bg,
        )

    # ----------------- OTP Overlay and Resend OTP Methods ----------------- #
    def create_otp_overlay(self):
        # Create the OTP input field with centered text
        self.otp_field = ft.TextField(
            label="Enter OTP",
            width=280,
            text_align="center",
            border=ft.InputBorder.OUTLINE,
            color="white",
            bgcolor="rgba(44,44,44,0.3)",
        )

        # Build the content of the OTP overlay
        otp_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "OTP Verification",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align="center"
                    ),
                    ft.Text(
                        "We have sent an OTP to your email.\nPlease enter it below.",
                        size=14,
                        color="#cccccc",
                        text_align="center",
                    ),
                    self.otp_field,
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                text="Verify OTP",
                                on_click=self.db_verify_otp_submit,
                                bgcolor=self.dashboard_accent_color,
                                color="white",
                                height=40,
                                width=120,
                            ),
                            ft.ElevatedButton(
                                text="Resend OTP",
                                on_click=self.resend_otp,
                                bgcolor="gray",
                                color="white",
                                height=40,
                                width=120,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    # Placeholder for a countdown timer (can be updated with timer logic)
                    ft.Text(
                        "OTP expires in: 60 seconds",
                        size=12,
                        color="white",
                        text_align="center",
                        key="otp_timer_text"
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            width=400,
            padding=20,
            bgcolor=self.glass_color,
            border_radius=15,
            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=5,
                color=ft.colors.BLACK45,
                offset=ft.Offset(0, 0)
            ),
        )

        # Create a full-screen modal overlay with a semi-transparent background
        overlay = ft.Container(
            content=otp_content,
            alignment=ft.alignment.center,
            bgcolor="rgba(0,0,0,0.5)",
            expand=True,
            visible=False,
            animate_opacity=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )
        return overlay

    def resend_otp(self, e):
        """Generate and resend a new OTP to the user's email."""
        if self.current_reg_email:
            new_otp = str(random.randint(100000, 999999))
            user = self.db.find_user_by_email(self.current_reg_email)
            if user:
                self.db.update_user_verification(user_id=user["id"], verified=False, new_otp=new_otp)
                send_email_otp(self.current_reg_email, new_otp)
                self.show_message("OTP resent to your email.")
            else:
                self.show_message("User not found.")
        else:
            self.show_message("No registration in progress.")
    # ----------------- Dashboard UI ----------------- #
    def show_dashboard(self):
        """Display dashboard view"""
        dashboard_view = ft.View(
            route="/dashboard",
            controls=[self.create_dashboard_ui()],
            bgcolor=self.dashboard_dark_bg,
            padding=0
        )
        self.page.views.clear()
        self.page.window_width = self.window_width
        self.page.window_height = self.window_height
        self.page.window_min_width = self.min_width
        self.page.window_min_height = self.min_height
        self.page.views.append(dashboard_view)
        self.page.update()

    def toggle_sidebar(self, e):
        """Toggle dashboard sidebar expansion"""
        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_tabs.controls = [
            self.create_tab_item(icon_path, label, i) 
            for i, (icon_path, label) in enumerate(self.tabs_data)
        ]
        self.left_sidebar.width = self.sidebar_expanded_width if self.sidebar_expanded else self.sidebar_width
        e.page.update()

    def create_tab_item(self, icon_path, label, index):
        """Creates a sidebar tab item"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Image(
                        src=icon_path,
                        width=24,
                        height=24,
                        color="white" if index != self.selected_tab_index else self.dashboard_accent_color,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    tooltip=ft.Tooltip(
                        message=label,
                        bgcolor="black",
                        text_style=ft.TextStyle(color="lightblue"),
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
                        size=14,
                        color="white" if index != self.selected_tab_index else self.dashboard_accent_color,
                        weight=ft.FontWeight.W_500,
                        overflow=ft.TextOverflow.CLIP,
                        max_lines=2,
                    ),
                    visible=self.sidebar_expanded,
                    padding=ft.padding.only(left=10),
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=self.glass_bgcolor if index == self.selected_tab_index else None,
            blur=self.container_blur if index == self.selected_tab_index else None,
            shadow=self.container_shadow if index == self.selected_tab_index else None,
            border_radius=0,
            border=ft.border.all(1, self.dashboard_accent_color) if index == self.selected_tab_index else None,
            width=self.sidebar_expanded_width if self.sidebar_expanded else self.sidebar_width,
            height=50,
            on_click=lambda e, idx=index: self.change_tab(e, idx),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )

    def change_tab(self, e, index):
        """Handle tab change in dashboard"""
        self.selected_tab_index = index
        for i, tab in enumerate(self.sidebar_tabs.controls):
            self.update_tab_appearance(tab, i == index)
        e.page.update()

    def update_tab_appearance(self, tab, is_selected):
        """Update tab appearance based on selection state"""
        tab.bgcolor = self.glass_bgcolor if is_selected else None
        tab.blur = self.container_blur if is_selected else None
        tab.shadow = self.container_shadow if is_selected else None
        tab.content.controls[0].content.color = self.dashboard_accent_color if is_selected else "white"
        tab.content.controls[1].content.color = self.dashboard_accent_color if is_selected else "white"
        tab.border = ft.border.all(1, self.dashboard_accent_color) if is_selected else None

    def create_dashboard_ui(self):
        """Create the main dashboard UI"""
        # Create top bar
        top_bar = self.create_dashboard_top_bar()

        # Create sidebar
        self.sidebar_tabs = ft.Column(
            controls=[
                self.create_tab_item(icon_path, label, i)
                for i, (icon_path, label) in enumerate(self.tabs_data)
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.START,
        )

        # Create toggle button
        toggle_button = ft.IconButton(
            icon=Icons.MENU,
            icon_color="white",
            icon_size=20,
            on_click=self.toggle_sidebar,
        )

        # Create left sidebar
        self.left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=toggle_button,
                        padding=ft.padding.only(left=2, top=10, bottom=10),
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

        # Create main panel
        main_panel = self.create_main_panel()

        # Create right panel
        right_panel = self.create_right_panel()

        # Create main content
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

        # Background
        background = ft.Container(
            expand=True,
            image_src=self.bg_image_path,
            image_fit=ft.ImageFit.COVER,
            image_repeat=ft.ImageRepeat.NO_REPEAT,
        )

        return ft.Stack(
            controls=[
                background,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            top_bar,
                            main_content,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
        )

    def create_dashboard_top_bar(self):
        """Create dashboard top bar"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=r"C:\Users\mannp\Downloads\Task\assets\logo.png",  # Update this path
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
                            content=ft.Text(self.current_user.name[:2].upper() if self.current_user else ""),
                            bgcolor="#00008B",
                            radius=16,
                        ),
                        ft.Text(
                            self.current_user.name if self.current_user else "",
                            color="white",
                            size=14
                        ),
                        ft.IconButton(
                            icon=Icons.LOGOUT,
                            icon_color='white',
                            icon_size=20,
                            tooltip="Logout",
                            on_click=self.handle_logout,
                        ),
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=15,
            ),
            padding=ft.padding.only(left=5, right=20, top=0),
            margin=ft.margin.only(top=-10)
        )

    def create_main_panel(self):
        """Create main panel of dashboard"""
        return ft.Container(
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
                    self.create_ports_section(),
                    # Device Controls Section
                    self.create_device_controls_section(),
                    # Connected Devices Section
                    self.create_connected_devices_section(),
                ],
            ),
        )

    def create_ports_section(self):
        """Create ports section"""
        return ft.Container(
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

    def create_device_controls_section(self):
        """Create device controls section"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Device Controls", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(expand=True),
                ]),
                ft.Container(height=15),
                ft.Row(
                    controls=[
                        self.create_device_control("Camera", Icons.CAMERA_ALT),
                        ft.Container(width=15),
                        self.create_device_control("Microphone", Icons.MIC),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True
                ),
            ]),
            bgcolor=self.glass_bgcolor,
            blur=self.container_blur,
            shadow=self.container_shadow,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=15),
        )

    def create_device_control(self, name, icon):
        """Create individual device control"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, color="white", size=40),
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=ft.Text(name, color="white", size=14, weight=ft.FontWeight.W_500),
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=ft.Switch(
                        value=False,
                        active_color=self.dashboard_accent_color,
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
        )

    def create_connected_devices_section(self):
        """Create connected devices section"""
        return ft.Container(
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
                        self.create_device_item("Bluetooth", Icons.BLUETOOTH),
                        self.create_device_item("Keyboard", Icons.KEYBOARD),
                        self.create_device_item("Mouse", Icons.MOUSE),
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
        )

    def create_device_item(self, name, icon):
        """Create individual device item"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color="white", size=24),
                ft.Text(name, color="white", size=12),
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

    def create_right_panel(self):
        """Create right panel of dashboard"""
        return ft.Container(
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
                    # Add your usage log content here
                    self.create_usage_log_content(),
                ],
            ),
        )

    def create_usage_log_content(self):
        """Create usage log content"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(Icons.ACCESS_TIME, color="white", size=16),
                            ft.Text("Recent Activities", color="white", size=14, weight=ft.FontWeight.BOLD),
                        ], spacing=10),
                        *[self.create_log_entry(
                            f"Device {i} connected",
                            f"{i}0 minutes ago",
                            Icons.DEVICE_HUB
                        ) for i in range(1, 6)]
                    ]),
                    bgcolor=self.glass_bgcolor,
                    blur=self.container_blur,
                    padding=15,
                    border_radius=10,
                    margin=ft.margin.only(top=20),
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

    def create_log_entry(self, title, time, icon):
        """Create individual log entry"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="white", size=20),
                ft.Column([
                    ft.Text(title, color="white", size=12, weight=ft.FontWeight.W_500),
                    ft.Text(time, color="#9e9e9e", size=10),
                ], spacing=2),
            ], spacing=10),
            margin=ft.margin.only(top=10),
        )

    # ----------------- Ports UI Logic ----------------- #
    def create_ports_row(self):
        """Create the ports control row"""
        self.ports_row = ft.Row(
            controls=[
                self.create_port_navigation_button(Icons.ARROW_BACK_IOS, self.prev_ports, True),
                *[self.create_port_container(i) for i in range(self.visible_ports)],
                self.create_port_navigation_button(Icons.ARROW_FORWARD_IOS, self.next_ports, False),
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        return self.ports_row

    def create_port_navigation_button(self, icon, on_click, is_back):
        """Create port navigation button"""
        return ft.Container(
            content=ft.IconButton(
                icon=icon,
                icon_color="white",
                icon_size=20,
                on_click=on_click,
                disabled=self.port_start_index == 0 if is_back else self.port_start_index + self.visible_ports >= self.total_ports,
            ),
            padding=ft.padding.only(right=5 if is_back else 0, left=0 if is_back else 5),
        )

    def create_port_container(self, index):
        """Create individual port container"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(Icons.USB, color="white", size=28),
                    margin=ft.margin.only(bottom=2),
                ),
                ft.Text(
                    f"Port {self.port_start_index + index + 1}",
                    color="white",
                    size=13,
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(
                    content=ft.Switch(
                        value=self.all_ports[self.port_start_index + index]["state"],
                        active_color=self.dashboard_accent_color,
                        scale=1.1,
                        on_change=lambda e, i=index: self.toggle_port(e, i),
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
        )

    def next_ports(self, e):
        """Handle next ports button click"""
        if self.port_start_index + self.visible_ports < self.total_ports:
            self.animate_ports(-1, e)
            self.port_start_index = min(self.port_start_index + self.visible_ports, self.total_ports - self.visible_ports)
            self.update_ports()

    def prev_ports(self, e):
        """Handle previous ports button click"""
        if self.port_start_index > 0:
            self.animate_ports(1, e)
            self.port_start_index = max(0, self.port_start_index - self.visible_ports)
            self.update_ports()

    def animate_ports(self, direction, e):
        """Animate ports transition"""
        for port in self.ports_row.controls[1:-1]:
            port.offset = ft.transform.Offset(direction, 0)
            port.opacity = 0
            e.page.update()
        for port in self.ports_row.controls[1:-1]:
            port.offset = ft.transform.Offset(0, 0)
            port.opacity = 1
            e.page.update()

    def update_ports(self):
        """Update ports display"""
        current_ports = self.ports_row.controls[1:-1]
        for i, port in enumerate(current_ports):
            port_number = self.port_start_index + i
            if port_number < self.total_ports:
                port.visible = True
                port.content.controls[1].value = f"Port {port_number + 1}"
                port.content.controls[2].content.value = self.all_ports[port_number]["state"]
                port.opacity = 1
            else:
                port.visible = False

        self.ports_row.controls[0].content.disabled = self.port_start_index == 0
        self.ports_row.controls[-1].content.disabled = self.port_start_index + self.visible_ports >= self.total_ports

    def toggle_port(self, e, port_index):
        """Toggle port state"""
        actual_index = self.port_start_index + port_index
        self.all_ports[actual_index]["state"] = e.control.value
        e.page.update()

    # ----------------- Main Entry Point ----------------- #
def main():
    """Main entry point of the application"""
    app = IntegratedApp()
    ft.app(target=app.initialize_page)

if __name__ == "__main__":
    main()
