use ratatui::{layout::Rect, Frame, widgets::Widget};

use crate::app::App;

/// Main layout renderer - arranges UI components
pub fn render(_app: &App, f: &mut Frame, chunk: Rect) {
    Widget::render(
        ratatui::widgets::Paragraph::new(ratatui::text::Text::raw("Dooz CLI - TUI")),
        chunk,
        f.buffer_mut(),
    );
}
