from gui.loading.loading_screen import LoadingScreen


class AppLoadingScreen(LoadingScreen):
    def __init__(self, root, theme):
        super().__init__(
            root,
            theme,
            default_title="Wczytywanie...",
            default_status="Przygotowanie interfejsu...",
            default_show_cancel=False,
            show_progress_bar=False,
            show_progress_percent=False,
            show_download_details=False,
        )
