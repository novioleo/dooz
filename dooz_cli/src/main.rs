mod action;
mod app;
mod fragments;
mod session;
mod tui;
mod ui;

use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;

fn main() -> std::io::Result<()> {
    color_eyre::install().expect("Failed to install color_eyre");
    let terminal = Terminal::new(CrosstermBackend::new(std::io::stdout()))?;
    let mut tui = tui::Tui::new(terminal);
    let app = app::App::new();
    app::run_app(&mut tui, app)?;
    Ok(())
}
