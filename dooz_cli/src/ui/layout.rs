use ratatui::{layout::{Constraint, Layout, Rect}, Frame, widgets::Widget};

use crate::app::App;

/// Main layout renderer - arranges UI components
pub fn render(_app: &App, f: &mut Frame, chunk: Rect) {
    Widget::render(
        ratatui::widgets::Paragraph::new(ratatui::text::Text::raw("Dooz CLI - TUI")),
        chunk,
        f.buffer_mut(),
    );
}

/// Calculate the 3-panel chat layout
/// 
/// Returns [left_panel, chat_history, input_area]
/// - Left panel: 20% width, full height
/// - Chat history: 80% width, 80% height (top)
/// - Input area: 80% width, 20% height (bottom)
pub fn chat_layout(area: Rect) -> [Rect; 3] {
    // First split horizontally: 20% left, 80% right
    let [left, right] = Layout::horizontal([
        Constraint::Percentage(20),
        Constraint::Percentage(80),
    ])
    .areas(area);

    // Then split right vertically: 80% top, 20% bottom
    let [chat_area, input_area] = Layout::vertical([
        Constraint::Percentage(80),
        Constraint::Percentage(20),
    ])
    .areas(right);

    [left, chat_area, input_area]
}
