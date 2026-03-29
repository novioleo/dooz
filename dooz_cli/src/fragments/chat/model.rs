use ratatui::widgets::{ListState, ScrollbarState};

use uuid::Uuid;

use crate::session::types::{Message, MessageRole, Session};

/// Chat fragment model state
#[derive(Debug, Default, Clone)]
pub struct ChatModel {
    /// All sessions loaded from the store
    pub sessions: Vec<Session>,
    /// State for the session list widget (tracks selection)
    pub session_list_state: ListState,
    /// Currently active/selected session ID
    pub active_session_id: Option<Uuid>,
    /// Chat messages (for the active session)
    pub messages: Vec<Message>,
    /// Scroll state for message list
    pub scroll_state: ScrollbarState,
    /// Current scroll position (tracked separately since ScrollbarState doesn't expose getters)
    scroll_position: usize,
    /// Auto-scroll to bottom when new messages arrive
    pub auto_scroll: bool,
    /// Current input buffer for the text input field
    pub input_buffer: String,
    /// Cursor position in the input buffer
    pub cursor_position: usize,
}

impl ChatModel {
    /// Create a new empty ChatModel
    pub fn new() -> Self {
        Self {
            sessions: Vec::new(),
            session_list_state: ListState::default(),
            active_session_id: None,
            messages: Vec::new(),
            scroll_state: ScrollbarState::default(),
            scroll_position: 0,
            auto_scroll: true,
            input_buffer: String::new(),
            cursor_position: 0,
        }
    }

    /// Get the scroll position
    pub fn scroll_position(&self) -> usize {
        self.scroll_position
    }

    /// Load sessions into the model and select the first one if available
    pub fn load_sessions(&mut self, sessions: Vec<Session>) {
        self.sessions = sessions;
        // Auto-select first session if available
        if !self.sessions.is_empty() {
            self.session_list_state.select(Some(0));
            self.active_session_id = Some(self.sessions[0].id);
        }
    }

    /// Select a session by index
    pub fn select_session(&mut self, index: usize) {
        if index < self.sessions.len() {
            self.session_list_state.select(Some(index));
            self.active_session_id = Some(self.sessions[index].id);
        }
    }

    /// Select a session by its ID
    pub fn select_session_by_id(&mut self, id: Uuid) {
        if let Some(index) = self.sessions.iter().position(|s| s.id == id) {
            self.session_list_state.select(Some(index));
            self.active_session_id = Some(id);
        }
    }

    /// Get the currently selected session, if any
    #[allow(dead_code)]
    pub fn get_active_session(&self) -> Option<&Session> {
        self.active_session_id.and_then(|id| {
            self.sessions.iter().find(|s| s.id == id)
        })
    }

    /// Add a message and ensure auto-scroll to bottom
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
        // Enable auto-scroll when a new message is added
        self.auto_scroll = true;
        // Update scroll state to reflect new message count
        let len = self.messages.len();
        self.scroll_state = self.scroll_state.content_length(len);
        self.scroll_position = len.saturating_sub(1);
    }

    /// Scroll up by one position
    #[allow(dead_code)]
    pub fn scroll_up(&mut self) {
        self.auto_scroll = false;
        if self.scroll_position > 0 {
            self.scroll_position -= 1;
            self.scroll_state = self.scroll_state.position(self.scroll_position);
        }
    }

    /// Scroll down by one position
    #[allow(dead_code)]
    pub fn scroll_down(&mut self) {
        let max_pos = self.messages.len().saturating_sub(1);
        if self.scroll_position < max_pos {
            self.scroll_position += 1;
            self.scroll_state = self.scroll_state.position(self.scroll_position);
        }
        // If we're at the bottom, enable auto-scroll
        if self.scroll_position >= max_pos {
            self.auto_scroll = true;
        }
    }

    /// Scroll to the bottom of the message list
    #[allow(dead_code)]
    pub fn scroll_to_bottom(&mut self) {
        self.scroll_position = self.messages.len().saturating_sub(1);
        self.scroll_state = self.scroll_state.position(self.scroll_position);
        self.auto_scroll = true;
    }

    /// Get the visible range of messages based on scroll state and available height
    #[allow(dead_code)]
    pub fn visible_message_indices(&self, visible_lines: usize) -> std::ops::Range<usize> {
        if self.messages.is_empty() {
            return 0..0;
        }

        let total_messages = self.messages.len();
        let start = self.scroll_position.min(total_messages.saturating_sub(1));
        
        // Calculate end index based on visible lines
        let end = (start + visible_lines).min(total_messages);
        
        start..end
    }

    /// Get messages filtered by role (helper for view)
    #[allow(dead_code)]
    pub fn user_messages(&self) -> Vec<&Message> {
        self.messages.iter().filter(|m| m.role == MessageRole::User).collect()
    }

    /// Get assistant messages
    #[allow(dead_code)]
    pub fn assistant_messages(&self) -> Vec<&Message> {
        self.messages.iter().filter(|m| m.role == MessageRole::Assistant).collect()
    }

    /// Insert a character at the current cursor position
    pub fn insert_char(&mut self, c: char) {
        self.input_buffer.insert(self.cursor_position, c);
        self.cursor_position += 1;
    }

    /// Delete the character before the cursor position (backspace)
    pub fn delete_back(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
            self.input_buffer.remove(self.cursor_position);
        }
    }

    /// Move cursor left
    pub fn move_cursor_left(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
        }
    }

    /// Move cursor right
    pub fn move_cursor_right(&mut self) {
        if self.cursor_position < self.input_buffer.len() {
            self.cursor_position += 1;
        }
    }

    /// Clear the input buffer
    pub fn clear_input(&mut self) {
        self.input_buffer.clear();
        self.cursor_position = 0;
    }

    /// Get the input content for sending
    pub fn get_input_content(&self) -> String {
        self.input_buffer.clone()
    }
}
