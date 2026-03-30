mod action;
mod app;
mod fragments;
mod session;
mod tui;
mod ui;

use std::io;

use crate::tui::Tui;

fn main() {
    // Install color_eyre for better error reporting
    if let Err(e) = color_eyre::install() {
        eprintln!("Failed to install color_eyre: {}", e);
    }

    // Create terminal backend
    let terminal = ratatui::Terminal::new(ratatui::backend::CrosstermBackend::new(
        io::stdout(),
    ))
    .expect("Failed to create terminal");

    let mut tui = Tui::new(terminal);

    // Enter the terminal UI (enables raw mode, alternate screen)
    if let Err(e) = tui.enter() {
        eprintln!("Failed to enter terminal UI: {}", e);
        return;
    }

    // Create and run the app
    let result = app::run_app(&mut tui);

    // Exit the terminal UI (restores terminal state)
    if let Err(e) = tui.exit() {
        eprintln!("Failed to exit terminal UI: {}", e);
    }

    // Handle any error from the app
    if let Err(e) = result {
        eprintln!("Application error: {}", e);
    }
}
