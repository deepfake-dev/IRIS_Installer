import flet as ft
from views.welcome_view import WelcomeView
from views.install_view import InstallView

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "Iris Installer"

    def route_change():
        page.views.clear()
        
        if page.route == "/":
            page.views.append(WelcomeView(page))
        elif page.route == "/install":
            page.views.append(InstallView(page))
            
        page.update()

    async def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.route = "/install"
    
    route_change()

if __name__ == "__main__":
    ft.run(main=main)