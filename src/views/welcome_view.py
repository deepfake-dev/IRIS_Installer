import flet as ft

def WelcomeView(page: ft.Page):
    async def go_installation(e):
        await page.push_route("/install")

    install_button = ft.FilledButton(
        "Install IRIS",
        width=200,
        disabled=True,
        on_click=go_installation,
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

    def enable_install(e):
        install_button.disabled = not e.control.value
        page.update()

    container = ft.Container(
        width=640,
        height=480,
        bgcolor="#333333",
        border=ft.Border.all(0.1, ft.Colors.WHITE_54),
        border_radius=16,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=16,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Image(src="icon.png", width=128, height=128),
                        ft.Text(
                            "IRIS System\n", 
                            weight=ft.FontWeight.W_300, 
                            size=72,
                            spans=[
                                ft.TextSpan("Installation", style=ft.TextStyle(size=24, weight=ft.FontWeight.W_900)),
                            ]
                        )
                    ]
                ),
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.TextButton("About IRIS System", icon=ft.Icons.INFO_OUTLINED, style=ft.ButtonStyle(color="#cd9ef7")),
                        ft.TextButton("Check our paper", icon=ft.Icons.SCHOOL_OUTLINED, style=ft.ButtonStyle(color="#cd9ef7")),
                        ft.TextButton("Suggest changes", icon=ft.Icons.LIGHTBULB_OUTLINED, style=ft.ButtonStyle(color="#cd9ef7")),
                    ]
                ),
                ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Checkbox(
                            "I agree to the Terms and Conditions set by the IRIS Developers.",
                            width=400,
                            on_change=enable_install
                        ),
                        install_button
                    ]
                )
            ]
        )
    )

    return ft.View(
        route="/",
        bgcolor="#262626",
        controls=[
            ft.SafeArea(
                expand=True,
                content=ft.Container(
                    content=container,
                    alignment=ft.Alignment.CENTER,
                )
            )
        ]
    )