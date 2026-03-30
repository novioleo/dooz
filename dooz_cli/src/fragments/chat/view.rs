use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Margin, Rect},
    style::Stylize,
    style::Style,
    text::{Line, Span, Text},
    widgets::{Block, Borders, Paragraph, Widget},
    Frame,
};

use crate::ui::layout::chat_layout;

use super::model::{ChatModel, ChatRegion};

/// Render the chat fragment view with 3-panel layout
pub fn render(model: &mut ChatModel, f: &mut Frame, chunk: Rect) {
    let [session_list_area, chat_history_area, input_area] = chat_layout(chunk);

    let border_margin = Margin {
        horizontal: 1,
        vertical: 1,
    };

    // Determine which region is active
    let active_region = model.active_region;

    // Session list panel (left)
    render_session_list(model, f, session_list_area, border_margin, active_region);

    // Chat history panel (right top)
    render_chat_history(model, f, chat_history_area, border_margin, active_region);

    // Input area panel (right bottom)
    render_input_area(model, f, input_area, border_margin, active_region);
}

/// Render the session list panel (left) as cards
fn render_session_list(model: &mut ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin, active_region: Option<ChatRegion>) {
    // Store the terminal area coordinates (not content area) for click detection
    model.set_session_list_layout(area.x, area.y, area.width, area.height);

    // Determine border style based on whether this region is active
    let is_active = active_region == Some(ChatRegion::SessionList);
    let border_style = if is_active {
        Style::new().cyan()
    } else {
        Style::new().dark_gray()
    };

    let session_list_block = Block::default()
        .borders(Borders::ALL)
        .title("Sessions")
        .title_style(Style::new().bold())
        .border_style(border_style);

    session_list_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    if model.sessions.is_empty() {
        let empty_text = Text::raw("No sessions\n\nType /new to create");
        Paragraph::new(empty_text)
            .style(Style::new().dim())
            .alignment(Alignment::Center)
            .render(content_area, f.buffer_mut());
    } else {
        // Render each session as a card
        let card_height = 5u16; // Each card takes 5 rows
        let mut current_y = content_area.y;
        let available_height = content_area.height;

        for session in model.sessions.iter() {
            // Stop if we run out of space
            if current_y + card_height > content_area.y + available_height {
                break;
            }

            let is_active = model.active_session_id == Some(session.id);
            let card_area = Rect {
                x: content_area.x,
                y: current_y,
                width: content_area.width,
                height: card_height,
            };

            render_session_card(session, is_active, card_area, f);

            current_y += card_height;
        }
    }
}

/// Render a single session card
fn render_session_card(
    session: &crate::session::types::Session,
    is_active: bool,
    area: Rect,
    f: &mut Frame,
) {
    // Card background and border style
    let (bg_color, border_color, text_color, title_style) = if is_active {
        (Style::new().on_cyan().black(), Style::new().cyan(), Style::new().black(), Style::new().bold())
    } else {
        (Style::new().dark_gray(), Style::new().dark_gray(), Style::new().white(), Style::new())
    };

    let card_block = Block::default()
        .borders(Borders::ALL)
        .border_style(border_color)
        .style(bg_color);

    card_block.render(area, f.buffer_mut());

    // Card inner content area
    let inner = area.inner(Margin {
        horizontal: 1,
        vertical: 1,
    });

    if inner.height < 3 {
        // Not enough space, skip rendering content
        return;
    }

    // Title (truncate if too long)
    let max_title_len = (inner.width as usize).saturating_sub(2);
    let display_title = if session.title.len() > max_title_len {
        format!("{}...", &session.title[..max_title_len.saturating_sub(3)])
    } else {
        session.title.clone()
    };

    // Time
    let time_str = session.updated_at.format("%m-%d %H:%M").to_string();

    // Message count
    let msg_count = session.messages.len();
    let count_str = if msg_count == 0 {
        "empty".to_string()
    } else if msg_count == 1 {
        "1 message".to_string()
    } else {
        format!("{} messages", msg_count)
    };

    // Build card content using Stylize trait
    let title_span = Span::styled(&display_title, title_style);
    let title_line = Line::from(vec![title_span]);
    let time_line = Line::from(vec![time_str.as_str().dim()]);
    let count_line = Line::from(vec![count_str.as_str().dim()]);

    // Create paragraphs for each line
    let title_para = Paragraph::new(title_line)
        .alignment(Alignment::Left)
        .style(text_color);

    let time_para = Paragraph::new(time_line)
        .alignment(Alignment::Left)
        .style(text_color);

    let count_para = Paragraph::new(count_line)
        .alignment(Alignment::Left)
        .style(text_color);

    // Calculate positions within the card
    let inner_width = inner.width;

    // Render title at top of card
    let title_area = Rect {
        x: inner.x,
        y: inner.y,
        width: inner_width,
        height: 1,
    };
    title_para.render(title_area, f.buffer_mut());

    // Render time below title
    let time_area = Rect {
        x: inner.x,
        y: inner.y + 1,
        width: inner_width,
        height: 1,
    };
    time_para.render(time_area, f.buffer_mut());

    // Render message count
    let count_area = Rect {
        x: inner.x,
        y: inner.y + 2,
        width: inner_width,
        height: 1,
    };
    count_para.render(count_area, f.buffer_mut());
}

/// Render the chat history panel (right top)
fn render_chat_history(model: &mut ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin, active_region: Option<ChatRegion>) {
    // Store the chat history layout for scroll handling
    model.set_chat_history_layout(area.x, area.y, area.width, area.height);

    // Determine border style based on whether this region is active
    let is_active = active_region == Some(ChatRegion::ChatHistory);
    let border_style = if is_active {
        Style::new().cyan()
    } else {
        Style::new().dark_gray()
    };

    let chat_history_block = Block::default()
        .borders(Borders::ALL)
        .title("Chat History")
        .title_style(Style::new().bold())
        .border_style(border_style);

    chat_history_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    if model.messages.is_empty() {
        let empty_text = if model.active_session_id.is_some() {
            Text::raw("No messages\n\nStart typing to chat")
        } else {
            Text::raw("Select a session\n\nor create a new one")
        };
        Paragraph::new(empty_text)
            .style(Style::new().dim())
            .alignment(Alignment::Center)
            .render(content_area, f.buffer_mut());
    } else {
        // Build message lines with automatic wrapping
        let mut lines: Vec<Line> = Vec::new();
        
        // Calculate available width for content (accounting for prefix)
        // Ensure at least 1 column width for wrapping to work
        let prefix_width = 4; // "You: " or "Bot: "
        let content_width = (content_area.width as usize).saturating_sub(prefix_width).max(1);

        for msg in model.messages.iter() {
            let prefix = match msg.role {
                crate::session::types::MessageRole::User => "You: ",
                crate::session::types::MessageRole::Assistant => "Bot: ",
            };
            let style = match msg.role {
                crate::session::types::MessageRole::User => Style::new().cyan(),
                crate::session::types::MessageRole::Assistant => Style::new().green(),
            };

            // Wrap the content text
            let wrapped_lines = wrap_text(&msg.content, content_width as u16);
            
            // First line with prefix
            let prefix_span = Span::styled(prefix, style);
            if let Some(first_line) = wrapped_lines.first() {
                let content_span: Span<'static> = Span::raw(first_line.clone());
                let msg_line = Line::from(vec![prefix_span, content_span]);
                lines.push(msg_line);
            }
            
            // Remaining lines without prefix (continuation)
            for line in wrapped_lines.iter().skip(1) {
                let content_span: Span<'static> = Span::raw(line.clone());
                let msg_line = Line::from(vec![content_span]);
                lines.push(msg_line);
            }

            // Add timestamp
            let time_str = msg.timestamp.format(" %H:%M").to_string();
            let time_span: Span<'static> = Span::raw(time_str);
            let time_line = Line::from(vec![time_span]);
            lines.push(time_line);

            // Add spacer
            lines.push(Line::from(vec![" ".into()]));
        }

        // Calculate total display lines before moving
        let total_lines = lines.len();
        
        let chat_content = Text::from(lines);
        let chat_para = Paragraph::new(chat_content)
            .scroll((model.scroll_position() as u16, 0));

        chat_para.render(content_area, f.buffer_mut());
        
        // Render scrollbar if there are more lines than visible
        if total_lines > content_area.height as usize {
            let scrollbar = ratatui::widgets::Scrollbar::new(
                ratatui::widgets::ScrollbarOrientation::VerticalRight,
            )
            .thumb_style(Style::new().cyan())
            .track_style(Style::new().dark_gray());

            let scrollbar_area = Rect {
                x: area.right() - 1,
                y: area.y + 1,
                width: 1,
                height: area.height - 2,
            };

            let mut scroll_state = model.scroll_state;
            scroll_state = scroll_state.content_length(total_lines);
            scroll_state = scroll_state.position(model.scroll_position());
            f.render_stateful_widget(scrollbar, scrollbar_area, &mut scroll_state);
        }
    }
}

/// Calculate the visual column width of a character
fn char_width(c: char) -> usize {
    if c.is_ascii_graphic() || c == ' ' {
        1
    } else if c == '\t' {
        4
    } else if matches!(c as u32,
        0x4E00..=0x9FFF |  // CJK Unified Ideographs
        0x3400..=0x4DBF |  // CJK Unified Ideographs Extension A
        0xAC00..=0xD7AF |  // Hangul Syllables
        0x3040..=0x309F |  // Hiragana
        0x30A0..=0x30FF |  // Katakana
        0xFF00..=0xFFEF    // Halfwidth and Fullwidth Forms
    ) {
        2
    } else {
        1
    }
}

/// Calculate the visual column width of a string
fn text_width(s: &str) -> usize {
    s.chars().map(char_width).sum()
}

/// Wrap text into lines of at most `width` columns
/// Preserves existing newlines, wraps long lines at word boundaries or character boundaries
fn wrap_text(text: &str, width: u16) -> Vec<String> {
    let width = width as usize;
    if width == 0 {
        return vec![text.to_string()];
    }
    
    let mut result = Vec::new();
    
    for line in text.lines() {
        if line.is_empty() {
            result.push(String::new());
            continue;
        }
        
        // Check if line already fits
        if text_width(line) <= width {
            result.push(line.to_string());
            continue;
        }
        
        // Need to wrap - build character by character
        let mut current_line = String::new();
        let mut current_width = 0;
        
        for c in line.chars() {
            let char_w = char_width(c);
            
            // If adding this char would exceed width
            if current_width + char_w > width {
                // Save current line and start new one
                result.push(current_line.clone());
                current_line.clear();
                current_width = 0;
            }
            
            current_line.push(c);
            current_width += char_w;
        }
        
        // Don't forget the last line
        if !current_line.is_empty() {
            result.push(current_line);
        }
    }
    
    if result.is_empty() {
        result.push(String::new());
    }
    
    result
}

/// Calculate the total visual column width of text before the cursor position
fn text_column_width_before(text: &str, char_index: usize) -> usize {
    text.chars()
        .take(char_index)
        .map(char_width)
        .sum()
}

/// Render the input area panel (right bottom)
fn render_input_area(model: &mut ChatModel, f: &mut Frame, area: Rect, inner_margin: Margin, active_region: Option<ChatRegion>) {
    // Store the input area layout for click handling
    model.set_input_area_layout(area.x, area.y, area.width, area.height);

    // Determine border style based on whether this region is active
    // Input area uses green color (brighter when active)
    let is_active = active_region == Some(ChatRegion::InputArea);
    let border_style = if is_active {
        Style::new().green().bold()
    } else {
        Style::new().green().dim()
    };

    let input_block = Block::default()
        .borders(Borders::ALL)
        .title("Input")
        .title_style(Style::new().bold())
        .border_style(border_style);

    input_block.render(area, f.buffer_mut());

    let content_area = area.inner(inner_margin);

    if content_area.height < 1 {
        return;
    }

    // Calculate available width for input (accounting for prompt)
    // Ensure at least 1 column width for wrapping to work
    let prompt_prefix = "> ";
    let content_width = (content_area.width as usize).saturating_sub(prompt_prefix.len()).max(1);

    // Build input text with wrapping
    let input_lines = if model.input_buffer.is_empty() {
        vec![prompt_prefix.to_string()]
    } else {
        // Wrap the input content first
        let wrapped = wrap_text(&model.input_buffer, content_width as u16);
        // Add prompt to first line only
        wrapped.into_iter()
            .enumerate()
            .map(|(i, line)| {
                if i == 0 {
                    format!("{}{}", prompt_prefix, line)
                } else {
                    line
                }
            })
            .collect()
    };

    let lines: Vec<Line> = input_lines.into_iter()
        .map(|line| Line::from(line))
        .collect();

    let text = Text::from(lines);

    // Calculate visible height and total lines
    let visible_height = content_area.height as usize;
    let total_lines = text.lines.len();

    // Create paragraph
    let input_para = Paragraph::new(text)
        .style(Style::new().white())
        .scroll((model.input_scroll_position as u16, 0));

    input_para.render(content_area, f.buffer_mut());

    // Show scrollbar if there are more lines than visible
    if total_lines > visible_height {
        let scrollbar = ratatui::widgets::Scrollbar::new(
            ratatui::widgets::ScrollbarOrientation::VerticalRight,
        )
        .thumb_style(Style::new().green())
        .track_style(Style::new().green().dim());

        let scrollbar_area = Rect {
            x: area.right() - 1,
            y: area.y + 1,
            width: 1,
            height: area.height - 2,
        };

        let mut scroll_state = ratatui::widgets::ScrollbarState::default()
            .content_length(total_lines)
            .position(model.input_scroll_position);
        f.render_stateful_widget(scrollbar, scrollbar_area, &mut scroll_state);
    }

    // Calculate cursor position based on cursor_position in the text
    // Find which line and column the cursor is at
    let cursor_char_pos = model.cursor_position.min(model.input_buffer.chars().count());
    
    // Convert character index to byte index for string slicing
    let cursor_byte_pos = model.input_buffer
        .chars()
        .take(cursor_char_pos)
        .map(|c| c.len_utf8())
        .sum::<usize>();
    
    // Count chars before cursor to find its line/column
    let text_before_cursor = format!("> {}", &model.input_buffer[..cursor_byte_pos]);
    
    // Find the last newline before cursor to determine line
    let last_newline_pos = text_before_cursor.rfind('\n');
    let line_start_pos = last_newline_pos.map(|p| p + 1).unwrap_or(0);
    let col_in_line = text_before_cursor.len() - line_start_pos;
    
    // Count which line the cursor is on
    let line_index = text_before_cursor.matches('\n').count();
    
    // Calculate actual cursor position on screen
    // If cursor line is below visible area, cursor is at last visible line
    // If cursor line is above visible area, cursor is at first visible line
    let display_line = if line_index >= visible_height {
        visible_height - 1
    } else {
        line_index
    };
    
    let cursor_x = content_area.x + (col_in_line as u16).min(content_area.width - 1);
    let cursor_y = content_area.y + (display_line as u16);

    if cursor_x < content_area.right() && cursor_y < content_area.bottom() {
        f.set_cursor_position(ratatui::layout::Position::new(cursor_x, cursor_y));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wrap_text_short_line() {
        // Short line that fits
        let result = wrap_text("hello", 80);
        assert_eq!(result, vec!["hello"]);
    }

    #[test]
    fn test_wrap_text_long_line() {
        // Long line that needs wrapping
        let result = wrap_text("This is a very long line that should be wrapped", 20);
        // Should be wrapped into multiple lines
        assert!(result.len() > 1);
        for line in &result {
            assert!(text_width(line) <= 20);
        }
    }

    #[test]
    fn test_wrap_text_cjk() {
        // Chinese characters (2 columns each)
        let result = wrap_text("你好世界", 6);
        // Each char is 2 columns, so 4 chars fit in 6 columns
        // "你好世界" is 8 columns total, should wrap
        assert!(result.len() > 1);
        for line in &result {
            assert!(text_width(line) <= 6);
        }
    }

    #[test]
    fn test_wrap_text_existing_newline() {
        // Preserve existing newlines
        let result = wrap_text("hello\nworld", 80);
        assert_eq!(result, vec!["hello", "world"]);
    }
}
