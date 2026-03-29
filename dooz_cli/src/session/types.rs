use serde::{Deserialize, Serialize};

/// Unique identifier for a conversation
pub type ConversationId = String;

/// Session user information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub name: String,
}

/// A session represents a user connection to the daemon
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub user: Option<User>,
    pub conversations: Vec<ConversationId>,
}
