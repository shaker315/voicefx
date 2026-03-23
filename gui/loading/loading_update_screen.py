from gui.loading.loading_screen import LoadingScreen


class UpdateLoadingScreen(LoadingScreen):
    def __init__(self, root, theme):
        super().__init__(
            root,
            theme,
            default_title="Pobieranie aktualizacji",
            default_status="Przygotowanie...",
            default_show_cancel=True,
            show_progress_bar=True,
            show_progress_percent=True,
            show_download_details=True,
        )
