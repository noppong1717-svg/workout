import flet as ft
try:
    import flet_video as fv
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False
import os 
import requests
import time
import threading
from datetime import date

API_BASE_URL = "http://127.0.0.1:8000"

current_user = {"id": None, "username": ""}

def main(page: ft.Page):
    page.title = "Home Workout Premium"
    page.window.width = 400
    page.window.height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"

    COLOR_PRIMARY = "#00FF66"
    COLOR_CARD = "#1E1E1E"

    def show_page(page_name, extra=None):
        page.controls.clear()
        page.navigation_bar = None

        # ----------------------------------------
        # หน้า 1: Login
        # ----------------------------------------
        if page_name == "login":
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

            username_input = ft.TextField(
                label="Username", width=300, border_radius=10,
                border_color="transparent", bgcolor=COLOR_CARD, filled=True
            )
            password_input = ft.TextField(
                label="Password", password=True, can_reveal_password=True,
                width=300, border_radius=10, border_color="transparent",
                bgcolor=COLOR_CARD, filled=True
            )
            error_text = ft.Text("", color=ft.Colors.RED_400, size=13)

            def login_click(e):
                error_text.value = ""
                if not username_input.value or not password_input.value:
                    error_text.value = "กรุณากรอกข้อมูลให้ครบถ้วน"
                    page.update()
                    return
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/login/",
                        json={"username": username_input.value, "password": password_input.value}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        current_user["id"] = data["user_id"]
                        current_user["username"] = data["username"]
                        show_page("home")
                    else:
                        error_text.value = "Username หรือ Password ไม่ถูกต้อง"
                        page.update()
                except Exception:
                    error_text.value = "เชื่อมต่อ Server ไม่ได้ กรุณาเปิด Backend ก่อน"
                    page.update()

            login_btn = ft.Container(
                content=ft.Row(
                    [ft.Text("LOG IN", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=16)],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                bgcolor=COLOR_PRIMARY, width=300, height=55,
                border_radius=10, on_click=login_click, ink=True
            )

            page.add(
                ft.Column([
                    ft.Icon(ft.Icons.BOLT, size=100, color=COLOR_PRIMARY),
                    ft.Text("CALO BURN", size=40, weight=ft.FontWeight.W_900, color=COLOR_PRIMARY),
                    ft.Text("UNLEASH YOUR POTENTIAL", size=12, color=ft.Colors.GREY_500),
                    ft.Divider(height=40, color="transparent"),
                    username_input,
                    password_input,
                    error_text,
                    ft.Divider(height=10, color="transparent"),
                    login_btn
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        # ----------------------------------------
        # หน้า 2: Home
        # ----------------------------------------
        elif page_name == "home":
            page.vertical_alignment = ft.MainAxisAlignment.START
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.navigation_bar = create_nav_bar(0)

            logout_btn = ft.Container(
                content=ft.Row(
                    [ft.Text("LOG OUT", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                bgcolor=COLOR_CARD, width=360, height=50, border_radius=10,
                on_click=lambda _: show_page("login"), ink=True
            )

            page.add(
                ft.Column([
                    ft.AppBar(
                        title=ft.Text(f"HI, {current_user['username'].upper()} 👋",
                                      weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        bgcolor="transparent"
                    ),
                    ft.Container(
                        content=ft.Text("READY\nTO SWEAT?", size=30,
                                        weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        width=360, height=200, border_radius=15,
                        bgcolor=ft.Colors.BLUE_GREY_900, padding=20,
                        alignment=ft.Alignment(-1, 1), margin=ft.margin.only(bottom=20)
                    ),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE),
                                ft.Text("350", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Kcal", color=ft.Colors.GREY)
                            ], alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=110, height=110, bgcolor=COLOR_CARD, border_radius=15
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.TIMER, color=COLOR_PRIMARY),
                                ft.Text("45", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Mins", color=ft.Colors.GREY)
                            ], alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=110, height=110, bgcolor=COLOR_CARD, border_radius=15
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.FITNESS_CENTER, color=ft.Colors.BLUE_400),
                                ft.Text("3", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Workouts", color=ft.Colors.GREY)
                            ], alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=110, height=110, bgcolor=COLOR_CARD, border_radius=15
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=360),
                    ft.Divider(height=40, color="transparent"),
                    logout_btn
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        # ----------------------------------------
        # หน้า 3: Workout — แสดงรายการท่าจาก DB
        # ----------------------------------------
        elif page_name == "workout":
            page.vertical_alignment = ft.MainAxisAlignment.START
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.navigation_bar = create_nav_bar(1)

            exercise_list = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
            status_text = ft.Text("กำลังโหลด...", color=ft.Colors.GREY_500)

            def load_exercises():
                exercise_list.controls.clear()
                try:
                    response = requests.get(f"{API_BASE_URL}/exercises/")
                    if response.status_code == 200:
                        exercises = response.json()
                        status_text.value = ""
                        for ex in exercises:
                            rest_secs = ex.get("rest_time_seconds", 60)
                            card = ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.FITNESS_CENTER,
                                                        color=COLOR_PRIMARY, size=28),
                                        padding=12, bgcolor="#2A2A2A", border_radius=12
                                    ),
                                    ft.Column([
                                        ft.Text(ex["title"], weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE, size=15),
                                        ft.Text(f"⏱ พักระหว่างเซต {rest_secs} วินาที",
                                                size=12, color=ft.Colors.GREY_400),
                                    ], spacing=3, expand=True),
                                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS,
                                            color=ft.Colors.GREY_600, size=16)
                                ], alignment=ft.MainAxisAlignment.START),
                                padding=15, bgcolor=COLOR_CARD, border_radius=15,
                                ink=True,
                                on_click=lambda e, exercise=ex: show_page("exercise_detail", exercise)
                            )
                            exercise_list.controls.append(card)
                    else:
                        status_text.value = "โหลดข้อมูลไม่ได้"
                except Exception:
                    status_text.value = "เชื่อมต่อ Server ไม่ได้"
                page.update()

            load_exercises()

            page.add(
                ft.Column([
                    ft.AppBar(
                        title=ft.Text("WORKOUT", weight=ft.FontWeight.BOLD,
                                      color=ft.Colors.WHITE),
                        bgcolor="transparent"
                    ),
                    ft.Container(
                        content=ft.Text("เลือกท่าออกกำลังกาย", size=16,
                                        weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                        width=360, margin=ft.margin.only(bottom=10)
                    ),
                    status_text,
                    ft.Container(content=exercise_list, width=360, expand=True)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            )

        # ----------------------------------------
        # หน้า 3b: Exercise Detail + REST TIMER
        # ----------------------------------------
        elif page_name == "exercise_detail":
            exercise = extra
            rest_secs = exercise.get("rest_time_seconds", 60) if exercise else 60

            page.vertical_alignment = ft.MainAxisAlignment.START
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.navigation_bar = create_nav_bar(1)

            timer_state = {"seconds": rest_secs, "running": False}
            mins_init, secs_init = divmod(rest_secs, 60)
            timer_text = ft.Text(f"{mins_init:02d}:{secs_init:02d}",
                                 size=70, weight=ft.FontWeight.W_900, color=COLOR_PRIMARY)

            def run_timer():
                while timer_state["running"] and timer_state["seconds"] > 0:
                    time.sleep(1)
                    timer_state["seconds"] -= 1
                    mins, secs = divmod(timer_state["seconds"], 60)
                    timer_text.value = f"{mins:02d}:{secs:02d}"
                    page.update()
                if timer_state["seconds"] == 0:
                    timer_state["running"] = False
                    page.snack_bar = ft.SnackBar(
                        ft.Text("REST IS OVER. LET'S GO! 🔥"), bgcolor=COLOR_PRIMARY
                    )
                    page.snack_bar.open = True
                    page.update()

            def start_timer(e):
                if not timer_state["running"] and timer_state["seconds"] > 0:
                    timer_state["running"] = True
                    threading.Thread(target=run_timer, daemon=True).start()

            def pause_timer(e):
                timer_state["running"] = False

            def reset_timer(e):
                timer_state["running"] = False
                timer_state["seconds"] = rest_secs
                mins, secs = divmod(rest_secs, 60)
                timer_text.value = f"{mins:02d}:{secs:02d}"
                page.update()

            title = exercise["title"] if exercise else "Exercise"

            page.add(
                ft.Column([
                    ft.AppBar(
                        title=ft.Text(title.upper(), weight=ft.FontWeight.BOLD,
                                      color=ft.Colors.WHITE),
                        bgcolor="transparent",
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                            on_click=lambda _: show_page("workout")
                        )
                    ),
                    # กล่องวิดีโอ — ถ้ามีไฟล์ใช้ flet_video / ถ้าไม่มีใช้กล่องจำลอง
                fv.Video(
    playlist=[fv.VideoMedia(
        "file:///" + os.path.abspath("assets/videos/" + exercise.get("video_filename", ""))
    )],
    width=360,
    height=220,
    autoplay=True,
    show_controls=True,
    expand=False,
                ) if (HAS_VIDEO and exercise and exercise.get("video_filename")) else ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=60, color=COLOR_PRIMARY),
                        ft.Text(title, color=ft.Colors.WHITE, size=16,
                                weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text("ยังไม่มีวิดีโอ", color=ft.Colors.GREY_500,
                                size=12, text_align=ft.TextAlign.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=360, height=220, border_radius=15, bgcolor=COLOR_CARD,
                    alignment=ft.Alignment(0, 0),
                ),
                    # REST TIMER
                    ft.Container(
                        content=ft.Column([
                            ft.Text("REST TIMER", size=14, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREY_500),
                            timer_text,
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.PLAY_ARROW_ROUNDED, icon_size=40,
                                              icon_color=ft.Colors.BLACK, bgcolor=COLOR_PRIMARY,
                                              on_click=start_timer),
                                ft.IconButton(icon=ft.Icons.PAUSE_ROUNDED, icon_size=40,
                                              icon_color=ft.Colors.WHITE, bgcolor="#333333",
                                              on_click=pause_timer),
                                ft.IconButton(icon=ft.Icons.STOP_ROUNDED, icon_size=40,
                                              icon_color=ft.Colors.WHITE, bgcolor="#333333",
                                              on_click=reset_timer),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                        ], alignment=ft.MainAxisAlignment.CENTER,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=360, padding=30, border_radius=20, bgcolor=COLOR_CARD
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        # ----------------------------------------
        # หน้า 4: Metrics
        # ----------------------------------------
        elif page_name == "metrics":
            page.vertical_alignment = ft.MainAxisAlignment.START
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.navigation_bar = create_nav_bar(2)

            weight_input = ft.TextField(
                label="Weight (kg)", width=170, border_radius=10,
                border_color="transparent", bgcolor=COLOR_CARD, filled=True,
                keyboard_type=ft.KeyboardType.NUMBER
            )
            waist_input = ft.TextField(
                label="Waist (cm)", width=170, border_radius=10,
                border_color="transparent", bgcolor=COLOR_CARD, filled=True,
                keyboard_type=ft.KeyboardType.NUMBER
            )
            history_list = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, height=300)

            def load_history():
                history_list.controls.clear()
                try:
                    response = requests.get(f"{API_BASE_URL}/metrics/{current_user['id']}")
                    if response.status_code == 200:
                        for row in response.json():
                            card = ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.MONITOR_WEIGHT, color=COLOR_PRIMARY),
                                        padding=10, bgcolor="#2A2A2A", border_radius=10
                                    ),
                                    ft.Column([
                                        ft.Text(f"Date: {row['recorded_date']}",
                                                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text(f"Weight: {row['weight_kg']} kg  |  Waist: {row['waist_cm']} cm",
                                                size=12, color=ft.Colors.GREY_400)
                                    ], spacing=2)
                                ], alignment=ft.MainAxisAlignment.START),
                                padding=15, bgcolor=COLOR_CARD, border_radius=15
                            )
                            history_list.controls.append(card)
                except Exception:
                    pass
                page.update()

            def submit_metric(e):
                if not weight_input.value or not waist_input.value:
                    return
                payload = {
                    "user_id": current_user["id"],
                    "weight_kg": float(weight_input.value),
                    "waist_cm": float(waist_input.value),
                    "recorded_date": str(date.today())
                }
                try:
                    requests.post(f"{API_BASE_URL}/metrics/", json=payload)
                    weight_input.value = ""
                    waist_input.value = ""
                    load_history()
                except Exception:
                    pass
                page.update()

            load_history()

            save_btn = ft.Container(
                content=ft.Row(
                    [ft.Text("SAVE RECORD", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                bgcolor=COLOR_PRIMARY, width=360, height=50,
                border_radius=10, on_click=submit_metric, ink=True
            )

            page.add(
                ft.Column([
                    ft.AppBar(
                        title=ft.Text("BODY METRICS", weight=ft.FontWeight.BOLD,
                                      color=ft.Colors.WHITE),
                        bgcolor="transparent"
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("TRACK TODAY", size=16, weight=ft.FontWeight.BOLD,
                                    color=COLOR_PRIMARY),
                            ft.Row([weight_input, waist_input],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=360),
                            save_btn
                        ], horizontal_alignment=ft.CrossAxisAlignment.START),
                        width=360, margin=ft.margin.only(bottom=20)
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("HISTORY", size=16, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREY_500),
                            history_list
                        ], horizontal_alignment=ft.CrossAxisAlignment.START),
                        width=360, expand=True
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

        page.update()

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: show_page("home")
        elif idx == 1: show_page("workout")
        elif idx == 2: show_page("metrics")

    def create_nav_bar(selected_index):
        return ft.NavigationBar(
            selected_index=selected_index,
            on_change=nav_change,
            bgcolor="#1A1A1A",
            indicator_color="#2A2A2A",
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,
                                             selected_icon=ft.Icons.HOME, label="หน้าแรก"),
                ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER_OUTLINED,
                                             selected_icon=ft.Icons.FITNESS_CENTER, label="ออกกำลังกาย"),
                ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_OUTLINED,
                                             selected_icon=ft.Icons.INSERT_CHART, label="สัดส่วน"),
            ]
        )

    show_page("login")

ft.run(main, assets_dir="assets")