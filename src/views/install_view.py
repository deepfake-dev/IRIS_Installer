import flet as ft
import os
import shutil
from install_engine import InstallerEngine
import subprocess
import datetime
import asyncio

def InstallView(page: ft.Page):
    default_path = os.path.join(os.getenv('LOCALAPPDATA', ''), 'IRIS')
    path_text = ft.Text(default_path, color=ft.Colors.WHITE)
    page.session.store.set("overwrite", False)

    async def close_app(run_control_center: bool):
        if run_control_center:
            subprocess.Popen(
                ["uv", "run", "--python", "./.venv/", "flet", "run", "./iris_control_center/src/main.py"],
                cwd=path_text.value, # Set the working directory directly here
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        
        # Give the OS a moment to register the process start
        await asyncio.sleep(1)
        page.window.close()

    run_cc = ft.Checkbox("Run IRIS Control Center on exit.")

    def show_closing_dialog():
        dialog = ft.AlertDialog(
            title=ft.Text("Installation Done!"),
            modal=True,
            content=run_cc,
            alignment=ft.Alignment.CENTER,
            actions=[
                ft.TextButton("Ok", on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda e: close_app(run_cc.value),
        )
        page.show_dialog(dialog)

    log_view = ft.ListView(expand=True, auto_scroll=True, spacing=4)

    def write_log(message: str, is_error: bool = False):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        color = "#ff6b6b" if is_error else "#BDD1D9"
        log_view.controls.append(
            ft.Text(f"[{timestamp}] {message}", color=color, font_family="JetBrains Mono")
        )
        page.update()

    async def change_path(e):
        path = await ft.FilePicker().get_directory_path(
            initial_directory=os.getenv('LOCALAPPDATA'),
            dialog_title="Choose IRIS Installation Folder"
        )

        if path != "" and path is not None:
            path_text.value = os.path.join(path, 'IRIS')

    installation_steps = [
        "Preparing Environment",
        "Downloading Provenance Check Models",
        "Downloading Transcription/Narration Models",
        "Downloading Vision-Language Model",
        "Downloading Multimodal Projector for VLM",
        "Downloading Assets, Databases, and Scripts",
        "Installing LLM Server",
        "Installing Python Dependencies",
        "Installing IRIS Control Center",
        "Checking if everything is in place",
        "IRIS System Installed"
    ]
    
    step_tiles = {}

    def create_progress_tile(index, title):
        tile =  ft.ListTile(
            toggle_inputs=False,
            title=ft.Text(title, color=ft.Colors.WHITE),
            leading=ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.WHITE_54)
        )

        step_tiles[index] = tile
        return tile

    async def update_step_status(step_index, status, progress=None, description=None):
        tile: ft.ListTile = step_tiles.get(step_index)
        if not tile: return

        if status == "running":
            tile.leading = ft.ProgressRing(width=16, height=16, color=ft.Colors.WHITE)
            tile.text_color = ft.Colors.WHITE
        elif status == "done":
            tile.leading = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400)
            tile.text_color = ft.Colors.GREEN

        if progress is not None and progress >= 0 and description:
            status_text.value = f"{progress:.2%}  —  {description}"
        elif progress is not None and progress == -1 and description:
            status_text.value = description
        
        page.update()
    
    def allow_overwrite():
        page.session.store.set("overwrite", True)
        page.pop_dialog()
    
    def start_install(e: ft.Event[ft.FilledButton]):
        path = path_text.value
        if os.path.exists(path) and not page.session.store.get("overwrite"):
            page.show_dialog(confirm_dialog)
        else:
            if page.session.store.get("overwrite"):
                try:
                    shutil.rmtree(path)
                except OSError as e:
                    print(f"Error clearing directory {path}: {e}")
                    return

            if not os.path.exists(path):
                os.makedirs(path)
            
            e.control.disabled = True
            
            engine = InstallerEngine(
                target_dir=path,
                update_callback=update_step_status,
                log_writer=write_log,
                show_closing_dialog_command=show_closing_dialog
            )
            engine.start()
    
    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you want to overwrite the contents of this directory? If yes, please start installation again."),
        actions=[
            ft.TextButton("Yes", on_click=lambda e: allow_overwrite()),
            ft.TextButton("No", on_click=lambda e: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    sidebar = ft.Container(
        bgcolor="#333333",
        width=350,
        content=ft.Column(
            controls=[
                ft.Divider(color=ft.Colors.TRANSPARENT, height=64),
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        controls=[create_progress_tile(i, step) for i, step in enumerate(installation_steps)]
                    )
                )
            ]
        )
    )

    status_text = ft.Text(
        "Waiting to Start",
        color="#BDD1D9",
        style=ft.TextStyle(
            font_family="JetBrains Mono"
        ),
    )

    main_content = ft.Container(
        expand=True,
        padding=ft.Padding.all(16),
        content=ft.Column(
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Image(src="icon.png", width=40, height=40),
                        ft.Text("IRIS System\n", weight=ft.FontWeight.W_300, size=24)
                    ]
                ),
                ft.Text("Installation Status", weight=ft.FontWeight.BOLD),
                ft.Container(
                    bgcolor="#0d1117",
                    height=48,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=16),
                    alignment=ft.Alignment.CENTER_LEFT,
                    content = status_text
                ),
                ft.Text("Installation Logs", weight=ft.FontWeight.BOLD),
                ft.Container(
                    bgcolor="#0d1117",
                    height=48,
                    border_radius=8,
                    expand=True,
                    padding=ft.Padding.all(16),
                    alignment=ft.Alignment.TOP_LEFT,
                    content = log_view
                ),
                ft.Text("Installation Path", weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.Button(
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.START,
                                controls=[
                                    ft.Icon(ft.Icons.FILE_OPEN_OUTLINED, color=ft.Colors.WHITE),
                                    path_text
                                ]
                            ),
                            expand=True,
                            style=ft.ButtonStyle(
                                shape=ft.ContinuousRectangleBorder(
                                    side=ft.BorderSide(
                                        width=0.2,
                                        color=ft.Colors.WHITE
                                    )
                                ),
                                padding=ft.Padding.only(left=8),
                                bgcolor="#333333"
                            ),
                            on_click=change_path
                        ),
                        ft.Divider(color=ft.Colors.BLACK, thickness=2, height=16),
                        ft.FilledButton(
                            "Start Installation",
                            on_click=start_install,
                            style=ft.ButtonStyle(
                                bgcolor={
                                    ft.ControlState.DISABLED: ft.Colors.GREY,
                                    ft.ControlState.HOVERED: "#e4c6fa",
                                    ft.ControlState.DEFAULT: "#cd9ef7",
                                },
                                color={
                                    ft.ControlState.DISABLED: ft.Colors.WHITE,
                                    ft.ControlState.DEFAULT: "#452981",
                                }
                            )
                        )
                    ]
                ),
            ]
        )
    )

    write_log("Logs...")

    return ft.View(
        route="/install",
        bgcolor="#262626",
        padding=0,
        controls=[
            ft.SafeArea(
                expand=True,
                content=ft.Row(
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        sidebar,
                        ft.VerticalDivider(width=1, color=ft.Colors.WHITE_54),
                        main_content
                    ]
                )
            )
        ]
    )