use crate::session::types::ConversationId;

/// Chat fragment model state
#[derive(Debug, Default)]
pub struct ChatModel {
    pub conversations: Vec<ConversationId>,
    pub selected_conversation: Option<ConversationId>,
    pub messages: Vec<ChatMessage>,
}

/// A chat message
#[derive(Debug, Clone)]
pub struct ChatMessage {
    pub id: String,
    pub from: String,
    pub content: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}
