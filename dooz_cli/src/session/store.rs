use std::collections::HashMap;

use super::types::{ConversationId, Session, User};

/// Session store managing all active sessions and their state
#[derive(Debug, Default)]
pub struct SessionStore {
    sessions: HashMap<String, Session>,
    active_session: Option<String>,
}

impl SessionStore {
    pub fn new() -> Self {
        Self::default()
    }

    /// Get a session by ID
    pub fn get(&self, id: &str) -> Option<&Session> {
        self.sessions.get(id)
    }

    /// Create a new session
    pub fn create_session(&mut self, user: Option<User>) -> String {
        let id = uuid::Uuid::new_v4().to_string();
        let session = Session {
            id: id.clone(),
            user,
            conversations: Vec::new(),
        };
        self.sessions.insert(id.clone(), session);
        self.active_session = Some(id.clone());
        id
    }

    /// Set the active session
    pub fn set_active(&mut self, id: String) {
        if self.sessions.contains_key(&id) {
            self.active_session = Some(id);
        }
    }

    /// Get the active session
    pub fn active(&self) -> Option<&Session> {
        self.active_session.as_ref().and_then(|id| self.get(id))
    }

    /// Add a conversation to a session
    pub fn add_conversation(&mut self, session_id: &str, conv_id: ConversationId) {
        if let Some(session) = self.sessions.get_mut(session_id) {
            session.conversations.push(conv_id);
        }
    }
}
