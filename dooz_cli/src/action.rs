use uuid::Uuid;

/// Action enum representing all possible user actions/events in the TEA pattern.
#[derive(Debug, Clone, PartialEq)]
pub enum Action {
    // Application lifecycle
    Init,
    Quit,
    Exit,

    // UI actions
    Render,
    Resize(u16, u16),

    // Fragment actions
    Chat(ChatAction),
}

/// Chat fragment actions
#[derive(Debug, Clone, PartialEq)]
pub enum ChatAction {
    // Message actions
    SendMessage(String),
    ReceiveMessage { from: String, content: String },

    // Scroll actions
    ScrollUp,
    ScrollDown,
    ScrollToBottom,

    // Input area actions
    InputChar(char),
    InputBackspace,
    InputLeft,
    InputRight,
    InputEnter,
    ClearInput,

    // Session management
    LoadSessions(Vec<SessionInfo>),
    SelectSession(usize),
    SelectSessionById(Uuid),
    CreateSession,

    // Legacy
    SelectConversation(String),
}

/// Session info for UI display (lightweight)
#[derive(Debug, Clone, PartialEq)]
pub struct SessionInfo {
    pub id: Uuid,
    pub title: String,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

use crate::session::types::Session;

impl From<Session> for SessionInfo {
    fn from(session: Session) -> Self {
        Self {
            id: session.id,
            title: session.title,
            updated_at: session.updated_at,
        }
    }
}
