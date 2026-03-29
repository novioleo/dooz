use ratatui::{
    layout::{Margin, Rect},
    style::Style,
    text::Text,
    widgets::{Block, Borders, Paragraph, Widget},
    Frame,
};

use crate::ui::layout::chat_layout;

use super::model::ChatModel;

/// Render the chat fragment view with 3-panel layout
pub fn render(model: &ChatModel, f: &mut Frame, chunk: Rect) {
    let [session_list_area, chat_history_area, input_area] = chat_layout(chunk);

    // Default margin for inner area (no margin = 0)
    let inner_margin = Margin::default();

    // Session list panel (left)
    let session_list_block = Block::default()
        .borders(Borders::ALL)
        .title("Sessions")
        .title_style(Style::new().bold());

    let session_list_content = if model.conversations.is_empty() {
        Text::raw("No sessions")
    } else {
        Text::raw(format!("{} sessions", model.conversations.len()))
    };

    session_list_block.render(session_list_area, f.buffer_mut());
    Paragraph::new(session_list_content).render(session_list_area.inner(inner_margin), f.buffer_mut());

    // Chat history panel (right top)
    let chat_history_block = Block::default()
        .borders(Borders::ALL)
        .title("Chat History")
        .title_style(Style::new().bold());

    let chat_history_content = if model.messages.is_empty() {
        Text::raw("No messages")
    } else {
        Text::raw(format!("{} messages", model.messages.len()))
    };

    chat_history_block.render(chat_history_area, f.buffer_mut());
    Paragraph::new(chat_history_content).render(chat_history_area.inner(inner_margin), f.buffer_mut());

    // Input area panel (right bottom)
    let input_block = Block::default()
        .borders(Borders::ALL)
        .title("Input")
        .title_style(Style::new().bold());

    let input_content = Text::raw("Type a message...");

    input_block.render(input_area, f.buffer_mut());
    Paragraph::new(input_content).render(input_area.inner(inner_margin), f.buffer_mut());
}
