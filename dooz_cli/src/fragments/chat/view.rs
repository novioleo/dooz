use ratatui::{layout::Rect, Frame, text::Text, widgets::Widget};

use super::model::ChatModel;

/// Render the chat fragment view
pub fn render(_model: &ChatModel, f: &mut Frame, chunk: Rect) {
    Widget::render(
        ratatui::widgets::Paragraph::new(Text::raw("Chat Fragment - TODO")),
        chunk,
        f.buffer_mut(),
    );
}
