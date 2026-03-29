use ratatui::Frame;

use crate::action::Action;

/// Terminal UI wrapper providing event handling and rendering
#[derive(Debug)]
pub struct Tui {
    terminal: ratatui::Terminal<ratatui::backend::CrosstermBackend<std::io::Stdout>>,
}

impl Tui {
    /// Create a new Tui instance
    pub fn new(terminal: ratatui::Terminal<ratatui::backend::CrosstermBackend<std::io::Stdout>>) -> Self {
        Self { terminal }
    }

    /// Draw a single frame
    pub fn draw<F>(&mut self, f: F) -> std::io::Result<()>
    where
        F: FnOnce(&mut Frame),
    {
        self.terminal.draw(f)?;
        Ok(())
    }

    /// Handle input events, returning the corresponding Action
    pub fn handle_events(&mut self) -> std::io::Result<Option<Action>> {
        // Event handling would go here
        // For skeleton, return None (no action)
        Ok(None)
    }
}
