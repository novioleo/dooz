"""Dooz TUI Application."""

from textual.app import App, ComposeResult

from dooz_cli.tui.screens.main_screen import MainScreen


class DoozTUI(App):
    """Main TUI application for dooz CLI."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $primary;
        color: $text;
    }
    
    Footer {
        background: $primary-darken-1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield MainScreen()
    
    async def on_mount(self) -> None:
        """Handle app mount."""
        pass
