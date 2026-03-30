use ratatui::widgets::{ListState, ScrollbarState};

use uuid::Uuid;

use crate::session::types::{Message, MessageRole, Session};

/// Session list layout info for mouse click handling
#[derive(Debug, Clone, Copy)]
pub struct SessionListLayout {
    pub x: u16,
    pub y: u16,
    pub width: u16,
    pub height: u16,
    pub card_height: u16,
}

impl Default for SessionListLayout {
    fn default() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
            card_height: 5, // Default card height for calculations
        }
    }
}

impl SessionListLayout {
    pub fn new() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
            card_height: 5,
        }
    }

    /// Check if a point (x, y) is within the session list area
    pub fn contains_point(&self, x: u16, y: u16) -> bool {
        x >= self.x && x < self.x + self.width && y >= self.y && y < self.y + self.height
    }

    /// Calculate session index from y coordinate
    /// Returns None if the click is not on a valid session card
    pub fn session_index_from_y(&self, y: u16, total_sessions: usize) -> Option<usize> {
        if !self.contains_point(self.x, y) {
            return None;
        }

        // Calculate offset from the top of the session list area
        // Account for: border (1) + title (1) + inner margin (1) = 3 rows
        let offset_from_top = y.saturating_sub(self.y + 3);

        let index = offset_from_top / self.card_height;
        if index < total_sessions as u16 {
            Some(index as usize)
        } else {
            None
        }
    }
}

/// Chat layout regions
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ChatRegion {
    SessionList,
    ChatHistory,
    InputArea,
}

/// Chat history layout info for scroll handling
#[derive(Debug, Clone, Copy)]
pub struct ChatHistoryLayout {
    pub x: u16,
    pub y: u16,
    pub width: u16,
    pub height: u16,
}

impl Default for ChatHistoryLayout {
    fn default() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
        }
    }
}

impl ChatHistoryLayout {
    pub fn new() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
        }
    }

    /// Check if a point is within the chat history area
    pub fn contains_point(&self, x: u16, y: u16) -> bool {
        x >= self.x && x < self.x + self.width && y >= self.y && y < self.y + self.height
    }
}

/// Input area layout info for click handling
#[derive(Debug, Clone, Copy)]
pub struct InputAreaLayout {
    pub x: u16,
    pub y: u16,
    pub width: u16,
    pub height: u16,
}

impl Default for InputAreaLayout {
    fn default() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
        }
    }
}

impl InputAreaLayout {
    pub fn new() -> Self {
        Self {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
        }
    }

    /// Check if a point is within the input area
    pub fn contains_point(&self, x: u16, y: u16) -> bool {
        x >= self.x && x < self.x + self.width && y >= self.y && y < self.y + self.height
    }
}

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
    /// Current input buffer for the text input field (supports multi-line)
    pub input_buffer: String,
    /// Cursor position in the input buffer (character index)
    pub cursor_position: usize,
    /// Scroll position for input area (for multi-line text scrolling)
    pub input_scroll_position: usize,
    /// Session list layout info for mouse click handling
    pub session_list_layout: SessionListLayout,
    /// Chat history area layout (for scroll handling)
    pub chat_history_layout: ChatHistoryLayout,
    /// Input area layout (for click handling)
    pub input_area_layout: InputAreaLayout,
    /// Currently active/hovered region (for scroll routing)
    pub active_region: Option<ChatRegion>,
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
            input_scroll_position: 0,
            session_list_layout: SessionListLayout::new(),
            chat_history_layout: ChatHistoryLayout::new(),
            input_area_layout: InputAreaLayout::new(),
            active_region: None,
        }
    }

    /// Update the session list layout info (called during rendering)
    pub fn set_session_list_layout(&mut self, x: u16, y: u16, width: u16, height: u16) {
        self.session_list_layout.x = x;
        self.session_list_layout.y = y;
        self.session_list_layout.width = width;
        self.session_list_layout.height = height;
    }

    /// Update the chat history layout info (called during rendering)
    pub fn set_chat_history_layout(&mut self, x: u16, y: u16, width: u16, height: u16) {
        self.chat_history_layout.x = x;
        self.chat_history_layout.y = y;
        self.chat_history_layout.width = width;
        self.chat_history_layout.height = height;
    }

    /// Update the input area layout info (called during rendering)
    pub fn set_input_area_layout(&mut self, x: u16, y: u16, width: u16, height: u16) {
        self.input_area_layout.x = x;
        self.input_area_layout.y = y;
        self.input_area_layout.width = width;
        self.input_area_layout.height = height;
    }

    /// Determine which region a point belongs to
    pub fn get_region_at_point(&self, x: u16, y: u16) -> Option<ChatRegion> {
        if self.session_list_layout.contains_point(x, y) {
            Some(ChatRegion::SessionList)
        } else if self.chat_history_layout.contains_point(x, y) {
            Some(ChatRegion::ChatHistory)
        } else if self.input_area_layout.contains_point(x, y) {
            Some(ChatRegion::InputArea)
        } else {
            None
        }
    }

    /// Handle mouse click - returns true if click was handled
    pub fn handle_click(&mut self, x: u16, y: u16) -> bool {
        // First determine which region was clicked
        match self.get_region_at_point(x, y) {
            Some(ChatRegion::SessionList) => {
                // Handle session list click
                if let Some(index) = self.session_list_layout.session_index_from_y(y, self.sessions.len()) {
                    if index < self.sessions.len() {
                        let session = &self.sessions[index];
                        self.active_session_id = Some(session.id);
                        self.session_list_state.select(Some(index));
                        // Load the session's messages
                        self.messages = session.messages.clone();
                        // Reset scroll position and enable auto-scroll when switching sessions
                        self.scroll_position = self.messages.len().saturating_sub(1);
                        self.scroll_state = ScrollbarState::default().content_length(self.messages.len()).position(self.scroll_position);
                        self.auto_scroll = true;
                        // Keep session list as active region so arrow keys scroll the session list
                        self.active_region = Some(ChatRegion::SessionList);
                        return true;
                    }
                }
            }
            Some(ChatRegion::ChatHistory) => {
                self.active_region = Some(ChatRegion::ChatHistory);
            }
            Some(ChatRegion::InputArea) => {
                self.active_region = Some(ChatRegion::InputArea);
            }
            None => {}
        }
        false
    }

    /// Handle scroll in the active region
    pub fn handle_scroll(&mut self, delta: i32) {
        // Scroll the region that was last interacted with
        match self.active_region {
            Some(ChatRegion::SessionList) => {
                // Scroll session list
                if delta > 0 {
                    if let Some(selected) = self.session_list_state.selected() {
                        if selected > 0 {
                            self.session_list_state.select(Some(selected - 1));
                        }
                    }
                } else if delta < 0 {
                    if let Some(selected) = self.session_list_state.selected() {
                        if selected < self.sessions.len().saturating_sub(1) {
                            self.session_list_state.select(Some(selected + 1));
                        }
                    }
                }
            }
            Some(ChatRegion::ChatHistory) | None => {
                // Scroll chat history
                if delta > 0 {
                    self.scroll_up();
                } else if delta < 0 {
                    self.scroll_down();
                }
            }
            Some(ChatRegion::InputArea) => {
                // Input area doesn't scroll, but we acknowledge the input
            }
        }
    }

    /// Get the total number of sessions
    pub fn total_sessions(&self) -> usize {
        self.sessions.len()
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
            // Load the session's messages
            self.messages = self.sessions[index].messages.clone();
            // Reset scroll position and enable auto-scroll when switching sessions
            self.scroll_position = self.messages.len().saturating_sub(1);
            self.scroll_state = ScrollbarState::default().content_length(self.messages.len()).position(self.scroll_position);
            self.auto_scroll = true;
            // Switch to chat history region so scrolling affects messages
            self.active_region = Some(ChatRegion::ChatHistory);
        }
    }

    /// Select a session by its ID
    pub fn select_session_by_id(&mut self, id: Uuid) {
        if let Some(index) = self.sessions.iter().position(|s| s.id == id) {
            self.session_list_state.select(Some(index));
            self.active_session_id = Some(id);
            // Load the session's messages
            self.messages = self.sessions[index].messages.clone();
            // Reset scroll position and enable auto-scroll when switching sessions
            self.scroll_position = self.messages.len().saturating_sub(1);
            self.scroll_state = ScrollbarState::default().content_length(self.messages.len()).position(self.scroll_position);
            self.auto_scroll = true;
            // Switch to chat history region so scrolling affects messages
            self.active_region = Some(ChatRegion::ChatHistory);
        }
    }

    /// Get the currently selected session, if any
    #[allow(dead_code)]
    pub fn get_active_session(&self) -> Option<&Session> {
        self.active_session_id.and_then(|id| {
            self.sessions.iter().find(|s| s.id == id)
        })
    }

    /// Check if current session is empty (no messages)
    pub fn is_current_session_empty(&self) -> bool {
        self.messages.is_empty()
    }

    /// Check if the latest session (first in list, sorted by updated_at) is empty
    /// This is used to determine if we should create a new session or reuse the empty one
    pub fn is_latest_session_empty(&self) -> bool {
        self.sessions
            .first()
            .map(|s| s.messages.is_empty())
            .unwrap_or(true)
    }

    /// Clear all messages in the current session (for when creating new session)
    pub fn clear_messages(&mut self) {
        self.messages.clear();
        self.scroll_state = ScrollbarState::default().content_length(0);
        self.scroll_position = 0;
        self.auto_scroll = true;
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
    pub fn scroll_up(&mut self) {
        self.auto_scroll = false;
        if self.messages.is_empty() {
            return;
        }
        if self.scroll_position > 0 {
            self.scroll_position -= 1;
            self.scroll_state = self.scroll_state.position(self.scroll_position);
        }
    }

    /// Scroll down by one position
    pub fn scroll_down(&mut self) {
        let len = self.messages.len();
        if len == 0 {
            return;
        }
        let max_pos = len - 1;
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
    pub fn scroll_to_bottom(&mut self) {
        let len = self.messages.len();
        if len == 0 {
            return;
        }
        self.scroll_position = len - 1;
        self.scroll_state = self.scroll_state.position(self.scroll_position);
        self.auto_scroll = true;
    }

    /// Insert a character at the current cursor position
    /// Cursor position is tracked as character index, but insert needs byte index
    pub fn insert_char(&mut self, c: char) {
        // Find the byte position for the current cursor (character index)
        let byte_offset = if self.cursor_position == 0 {
            0
        } else {
            self.input_buffer
                .char_indices()
                .nth(self.cursor_position)
                .map(|(i, _)| i)
                .unwrap_or(self.input_buffer.len())
        };
        self.input_buffer.insert(byte_offset, c);
        self.cursor_position += 1;
    }

    /// Insert a newline character at the current cursor position
    pub fn insert_newline(&mut self) {
        self.insert_char('\n');
    }

    /// Delete the character before the cursor position (backspace)
    /// Cursor position is tracked as character index, but remove needs byte index
    pub fn delete_back(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
            // Find byte position of character we just passed (the one to delete)
            // char_indices().nth(cursor_position) gives start of character at cursor_position
            let byte_offset = self.input_buffer
                .char_indices()
                .nth(self.cursor_position)
                .map(|(i, _)| i)
                .unwrap_or(self.input_buffer.len());
            self.input_buffer.remove(byte_offset);
        }
    }

    /// Move cursor left (by one character)
    pub fn move_cursor_left(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
        }
    }

    /// Move cursor right (by one character)
    pub fn move_cursor_right(&mut self) {
        let char_count = self.input_buffer.chars().count();
        if self.cursor_position < char_count {
            self.cursor_position += 1;
        }
    }

    /// Clear the input buffer
    pub fn clear_input(&mut self) {
        self.input_buffer.clear();
        self.cursor_position = 0;
        self.input_scroll_position = 0;
    }

    /// Get the input content for sending
    pub fn get_input_content(&self) -> String {
        self.input_buffer.clone()
    }

    /// Get the active session with messages synced from model.messages
    /// This should be called before saving to ensure latest messages are included
    pub fn get_active_session_with_messages(&self) -> Option<Session> {
        let session = self.get_active_session()?;
        // Create a new session with updated messages from model.messages
        let mut updated_session = session.clone();
        updated_session.messages = self.messages.clone();
        updated_session.updated_at = chrono::Utc::now();
        Some(updated_session)
    }
}
