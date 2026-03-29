use ratatui::{
    layout::{Alignment, Margin, Rect},
    style::Style,
    text::{Line, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Scrollbar, ScrollbarOrientation, Widget},
    Frame,
};
use ratatui::style::Stylize;

use textwrap::wrap;

use crate::session::types::MessageRole;

use super::model::ChatModel;
use crate::ui::layout::chat_layout;

/// Render the chat fragment view with 3-panel layout
pub fn render(model: &ChatModel, f: &mut Frame, chunk: Rect) {
    let [session_list_area, chat_history_area, input_area] = chat_layout(chunk);

    // Default margin for inner area (no margin = 0)
    let inner_margin = Margin::default();

    // Session list panel (left)
    render_session_list(model, f, session_list_area, inner_margin);

    // Chat history panel (right top) - WeChat-style messages
    render_chat_history(model, f, chat_history_area, inner_margin);

    // Input area panel (right bottom)
    render_input_area(f, input_area, inner_margin);
}

/// Render the session list panel (left)
fn render_session_list(model: &ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin) {
    let session_list_block = Block::default()
        .borders(Borders::ALL)
        .title("Sessions")
        .title_style(Style::new().bold());

    session_list_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    if model.sessions.is_empty() {
        let empty_text = Text::raw("No sessions");
        Paragraph::new(empty_text)
            .style(Style::new().dim())
            .render(content_area, f.buffer_mut());
    } else {
        let mut state = model.session_list_state.clone();
        let items: Vec<_> = model
            .sessions
            .iter()
            .map(|session| {
                let is_active = model.active_session_id == Some(session.id);
                let time_str = session.updated_at.format("%H:%M").to_string();
                if is_active {
                    Line::from(vec![
                        session.title.clone().bold().cyan(),
                        " ".into(),
                        time_str.dim(),
                    ])
                } else {
                    Line::from(vec![
                        session.title.clone().into(),
                        " ".into(),
                        time_str.dim(),
                    ])
                }
            })
            .collect();

        let list = List::new(
            items
                .into_iter()
                .map(|line| ListItem::new(line))
                .collect::<Vec<_>>(),
        );
        f.render_stateful_widget(list, content_area, &mut state);
    }
}

/// Render the chat history panel with WeChat-style messages
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
        return;
    }

    // Calculate how many lines each message takes
    let max_content_width = (content_area.width.saturating_sub(2)) as usize;

    // Calculate visible message range starting from scroll position
    let start_idx = model.scroll_position().min(model.messages.len().saturating_sub(1));
    let mut current_y = 0;

    // Render messages starting from scroll position
    for msg in model.messages.iter().skip(start_idx) {
        let msg_height = calculate_message_height(msg, max_content_width.max(1));

        if current_y + msg_height > content_area.height {
            break;
        }

        let msg_area = Rect::new(
            content_area.x,
            content_area.y + current_y,
            content_area.width,
            msg_height,
        );

        render_message_to_frame(msg, msg_area, max_content_width.max(1) as u16, f);
        current_y += msg_height;
    }

    // Render scrollbar on the right side of the chat area
    let scrollbar_area = Rect::new(
        area.right() - 1,
        area.y + 1,
        1,
        area.height - 2,
    );

    let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight)
        .thumb_style(Style::new().cyan())
        .track_style(Style::new().dark_gray());

    f.render_stateful_widget(scrollbar, scrollbar_area, &mut model.scroll_state.clone());
}

/// Calculate the height needed to render a message (content + timestamp + spacing)
fn calculate_message_height(message: &crate::session::types::Message, max_width: usize) -> u16 {
    if max_width < 1 {
        return 1;
    }

    // Wrap content
    let wrapped_lines: Vec<_> = wrap(&message.content, max_width).into_iter().collect();
    let num_content_lines = wrapped_lines.len();

    // 1 line for timestamp + 1 line spacing + content lines
    (num_content_lines as u16) + 2
}

/// Render a single message with WeChat-style alignment directly to frame buffer
fn render_message_to_frame(message: &crate::session::types::Message, area: Rect, content_width: u16, f: &mut Frame) {
    let timestamp_str = format_timestamp(&message.timestamp);
    let wrapped: Vec<Line> = wrap(&message.content, content_width as usize)
        .into_iter()
        .map(|cow| Line::from(cow.into_owned()))
        .collect::<Vec<_>>();

    match message.role {
        MessageRole::User => {
            // Right-aligned, cyan color
            render_user_message_to_frame(&wrapped, &timestamp_str, area, content_width, f);
        }
        MessageRole::Assistant => {
            // Left-aligned, green color
            render_assistant_message_to_frame(&wrapped, &timestamp_str, area, content_width, f);
        }
    }
}

/// Render a user message (right-aligned, cyan) directly to frame
fn render_user_message_to_frame(lines: &[Line], timestamp: &str, area: Rect, content_width: u16, f: &mut Frame) {
    let style = Style::new().cyan();
    let timestamp_style = Style::new().dim().cyan();

    // Content area with padding
    let content_area = Rect::new(
        area.x + 1,
        area.y + 1,
        content_width,
        area.height.saturating_sub(2),
    );

    // Render content right-aligned
    for (i, line) in lines.iter().enumerate() {
        let line_area = Rect::new(
            content_area.x,
            content_area.y + i as u16,
            content_area.width,
            1,
        );
        let right_aligned_line = Line::from(line.clone()).alignment(Alignment::Right);
        Paragraph::new(Text::from(right_aligned_line))
            .style(style)
            .render(line_area, f.buffer_mut());
    }

    // Render timestamp right-aligned at bottom
    let timestamp_area = Rect::new(
        content_area.x,
        content_area.y + lines.len() as u16,
        content_area.width,
        1,
    );
    Paragraph::new(Text::raw(timestamp))
        .style(timestamp_style)
        .alignment(Alignment::Right)
        .render(timestamp_area, f.buffer_mut());
}

/// Render an assistant message (left-aligned, green) directly to frame
fn render_assistant_message_to_frame(lines: &[Line], timestamp: &str, area: Rect, content_width: u16, f: &mut Frame) {
    let style = Style::new().green();
    let timestamp_style = Style::new().dim().green();

    // Left-aligned content
    let content_area = Rect::new(
        area.x + 1,
        area.y + 1,
        content_width,
        area.height.saturating_sub(2),
    );

    // Render content left-aligned
    for (i, line) in lines.iter().enumerate() {
        let line_area = Rect::new(
            content_area.x,
            content_area.y + i as u16,
            content_area.width,
            1,
        );
        Paragraph::new(line.clone())
            .style(style)
            .alignment(Alignment::Left)
            .render(line_area, f.buffer_mut());
    }

    // Render timestamp left-aligned at bottom
    let timestamp_area = Rect::new(
        content_area.x,
        content_area.y + lines.len() as u16,
        content_area.width,
        1,
    );
    Paragraph::new(Text::raw(timestamp))
        .style(timestamp_style)
        .alignment(Alignment::Left)
        .render(timestamp_area, f.buffer_mut());
}

/// Render the input area panel (right bottom)
fn render_input_area(f: &mut Frame, area: Rect, inner_margin: Margin) {
    let input_block = Block::default()
        .borders(Borders::ALL)
        .title("Input")
        .title_style(Style::new().bold());

    input_block.render(area, f.buffer_mut());

    let input_content = Text::raw("Type a message...");

    Paragraph::new(input_content).render(area.inner(inner_margin), f.buffer_mut());
}

/// Format timestamp for display (HH:MM format)
fn format_timestamp(timestamp: &chrono::DateTime<chrono::Utc>) -> String {
    timestamp.format("%H:%M").to_string()
}
