use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Type alias for conversation identifiers
pub type ConversationId = String;

/// Role of the message sender
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MessageRole {
    User,
    Assistant,
}

/// A single message in a session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Uuid,
    pub role: MessageRole,
    pub content: String,
    pub timestamp: DateTime<Utc>,
}

impl Message {
    /// Create a new message with the current timestamp
    pub fn new(role: MessageRole, content: String) -> Self {
        Self {
            id: Uuid::new_v4(),
            role,
            content,
            timestamp: Utc::now(),
        }
    }
}

/// A session representing a conversation with messages
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: Uuid,
    pub title: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub messages: Vec<Message>,
}

impl Session {
    /// Create a new session with the given title
    pub fn new(title: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            title,
            created_at: now,
            updated_at: now,
            messages: Vec::new(),
        }
    }

    /// Add a message to the session and update the timestamp
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
        self.updated_at = Utc::now();
    }
}
