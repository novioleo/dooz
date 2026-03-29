use ratatui::{
    layout::{Margin, Rect},
    style::Stylize,
    style::Style,
    text::{Line, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Widget},
    Frame,
};

use crate::ui::layout::chat_layout;

use super::model::ChatModel;

/// Convert a session to a ListItem for display
fn session_to_list_item(session: &crate::session::types::Session, is_active: bool) -> ListItem<'static> {
    let time_str = session.updated_at.format("%H:%M").to_string();
    let title = session.title.clone();
    
    let line = if is_active {
        Line::from(vec![
            title.bold().cyan(),
            " ".into(),
            time_str.dim(),
        ])
    } else {
        Line::from(vec![
            title.into(),
            " ".into(),
            time_str.dim(),
        ])
    };
    
    ListItem::new(line)
}

/// Render the chat fragment view with 3-panel layout
pub fn render(model: &ChatModel, f: &mut Frame, chunk: Rect) {
    let [session_list_area, chat_history_area, input_area] = chat_layout(chunk);

    // Default margin for inner area (no margin = 0)
    let inner_margin = Margin::default();

    // Session list panel (left)
    render_session_list(model, f, session_list_area, inner_margin);

    // Chat history panel (right top)
    render_chat_history(model, f, chat_history_area, inner_margin);

    // Input area panel (right bottom)
    render_input_area(model, f, input_area, inner_margin);
}

/// Render the session list panel (left)
fn render_session_list(model: &ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin) {
    let session_list_block = Block::default()
        .borders(Borders::ALL)
        .title("Sessions")
        .title_style(Style::new().bold());

    // Render the block border
    session_list_block.render(area, f.buffer_mut());

    // Calculate the inner area for content
    let content_area = area.inner(inner_margin);

    if model.sessions.is_empty() {
        // Empty state message
        let empty_text = Text::raw("No sessions");
        Paragraph::new(empty_text)
            .style(Style::new().dim())
            .render(content_area, f.buffer_mut());
    } else {
        // Build list items with highlighting for active session
        let items: Vec<ListItem> = model
            .sessions
            .iter()
            .map(|session| {
                let is_active = model.active_session_id == Some(session.id);
                session_to_list_item(session, is_active)
            })
            .collect();

        // Create List widget with state
        let list = List::new(items)
            .block(Block::default()) // No additional block since we rendered outer above
            .style(Style::new());

        // Render with stateful widget to maintain scroll position
        let mut state = model.session_list_state;
        f.render_stateful_widget(list, content_area, &mut state);
    }
}

/// Render the chat history panel (right top)
fn render_chat_history(model: &ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin) {
    let chat_history_block = Block::default()
        .borders(Borders::ALL)
        .title("Chat History")
        .title_style(Style::new().bold());

    chat_history_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    if model.messages.is_empty() {
        let empty_text = if model.active_session_id.is_some() {
            Text::raw("No messages in this session")
        } else {
            Text::raw("Select a session to view messages")
        };
        Paragraph::new(empty_text)
            .style(Style::new().dim())
            .render(content_area, f.buffer_mut());
    } else {
        // Build the message content
        let message_lines: Vec<Line> = model.messages.iter().map(|msg| {
            let role_str = match msg.role {
                crate::session::types::MessageRole::User => "You: ",
                crate::session::types::MessageRole::Assistant => "Assistant: ",
            };
            Line::from(vec![
                role_str.bold().cyan(),
                msg.content.as_str().into(),
            ])
        }).collect();

        let chat_content = Text::from(message_lines);
        Paragraph::new(chat_content)
            .scroll((0, 0)) // TODO: Use scroll position when available
            .render(content_area, f.buffer_mut());
    }
}

/// Render the input area panel (right bottom)
fn render_input_area(model: &ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin) {
    // Use a distinct style for the input area - green border to differentiate
    let input_block = Block::default()
        .borders(Borders::ALL)
        .title("Input")
        .title_style(Style::new().bold())
        .border_style(Style::new().green()); // Distinct border for input area

    input_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    // If input buffer is empty, show placeholder "> "
    let input_text = if model.input_buffer.is_empty() {
        Text::raw("> ")
    } else {
        // Show the input buffer with cursor position
        let display_text = format!("{} ", model.input_buffer);
        Text::raw(display_text)
    };

    Paragraph::new(input_text)
        .style(Style::new().white())
        .render(content_area, f.buffer_mut());

    // Set cursor position for input
    // The cursor should be at the end of the input buffer
    let cursor_x = content_area.x + model.cursor_position as u16;
    let cursor_y = content_area.y;
    
    // Only set cursor if we're in the input area
    if cursor_x < content_area.right() {
        f.set_cursor_position(ratatui::layout::Position::new(cursor_x, cursor_y));
    }
}
