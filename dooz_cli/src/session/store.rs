use std::fs;
use std::path::PathBuf;

use anyhow::{Context, Result};
use uuid::Uuid;

use super::types::Session;

/// Session store that persists sessions to the `.doz/sessions/` directory
#[derive(Debug)]
pub struct SessionStore {
    sessions_dir: PathBuf,
}

impl SessionStore {
    /// Create a new SessionStore, auto-creating the sessions directory if needed
    pub fn new() -> Result<Self> {
        let sessions_dir = Self::default_sessions_dir()?;

        if !sessions_dir.exists() {
            fs::create_dir_all(&sessions_dir)
                .context("Failed to create sessions directory")?;
        }

        Ok(Self { sessions_dir })
    }

    /// Get the default sessions directory path: `.doz/sessions/`
    fn default_sessions_dir() -> Result<PathBuf> {
        let home_dir = dirs::home_dir()
            .context("Could not determine home directory")?;
        Ok(home_dir.join(".doz").join("sessions"))
    }

    /// Get the file path for a session
    fn session_file_path(&self, id: Uuid) -> PathBuf {
        self.sessions_dir.join(format!("{}.json", id))
    }

    /// Create a new session with the given title
    pub fn create_session(&self, title: String) -> Result<Session> {
        let session = Session::new(title);
        self.save_session(&session)?;
        Ok(session)
    }

    /// Get a session by ID, returns None if not found
    pub fn get_session(&self, id: Uuid) -> Result<Option<Session>> {
        let path = self.session_file_path(id);

        if !path.exists() {
            return Ok(None);
        }

        let content = fs::read_to_string(&path)
            .context("Failed to read session file")?;

        let session: Session = serde_json::from_str(&content)
            .context("Failed to parse session JSON")?;

        Ok(Some(session))
    }

    /// Save (create or update) a session
    pub fn save_session(&self, session: &Session) -> Result<()> {
        if !self.sessions_dir.exists() {
            fs::create_dir_all(&self.sessions_dir)
                .context("Failed to create sessions directory")?;
        }

        let path = self.session_file_path(session.id);
        let content = serde_json::to_string_pretty(session)
            .context("Failed to serialize session")?;

        fs::write(&path, content)
            .context("Failed to write session file")?;

        Ok(())
    }

    /// List all sessions, sorted by updated_at descending (most recent first)
    pub fn list_sessions(&self) -> Result<Vec<Session>> {
        if !self.sessions_dir.exists() {
            return Ok(Vec::new());
        }

        let mut sessions = Vec::new();

        for entry in fs::read_dir(&self.sessions_dir)
            .context("Failed to read sessions directory")?
        {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();

            if path.extension().map(|e| e == "json").unwrap_or(false) {
                let content = fs::read_to_string(&path)
                    .context("Failed to read session file")?;

                match serde_json::from_str::<Session>(&content) {
                    Ok(session) => sessions.push(session),
                    Err(e) => {
                        eprintln!("Warning: Skipping invalid session file {:?}: {}", path, e);
                    }
                }
            }
        }

        // Sort by updated_at descending (most recent first)
        sessions.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));

        Ok(sessions)
    }

    /// Delete a session by ID
    #[allow(dead_code)]
    pub fn delete_session(&self, id: Uuid) -> Result<bool> {
        let path = self.session_file_path(id);

        if !path.exists() {
            return Ok(false);
        }

        fs::remove_file(&path)
            .context("Failed to delete session file")?;

        Ok(true)
    }
}

impl Default for SessionStore {
    fn default() -> Self {
        Self {
            sessions_dir: Self::default_sessions_dir().unwrap_or_else(|_| PathBuf::from(".doz/sessions")),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn create_test_store() -> (SessionStore, TempDir) {
        let temp_dir = TempDir::new().unwrap();
        let sessions_dir = temp_dir.path().join("sessions");
        fs::create_dir_all(&sessions_dir).unwrap();

        let store = SessionStore {
            sessions_dir,
        };
        (store, temp_dir)
    }

    #[test]
    fn test_create_session() {
        let (store, _temp) = create_test_store();

        let session = store.create_session("Test Session".to_string()).unwrap();

        assert_eq!(session.title, "Test Session");
        assert!(session.messages.is_empty());
    }

    #[test]
    fn test_get_session() {
        let (store, _temp) = create_test_store();

        let created = store.create_session("My Session".to_string()).unwrap();
        let loaded = store.get_session(created.id).unwrap().unwrap();

        assert_eq!(loaded.id, created.id);
        assert_eq!(loaded.title, created.title);
    }

    #[test]
    fn test_get_session_not_found() {
        let (store, _temp) = create_test_store();

        let result = store.get_session(Uuid::new_v4()).unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn test_save_session() {
        let (store, _temp) = create_test_store();

        let mut session = Session::new("Updated Session".to_string());
        store.save_session(&session).unwrap();

        let loaded = store.get_session(session.id).unwrap().unwrap();
        assert_eq!(loaded.title, "Updated Session");

        // Update and save again
        session.title = "Modified Title".to_string();
        store.save_session(&session).unwrap();

        let loaded = store.get_session(session.id).unwrap().unwrap();
        assert_eq!(loaded.title, "Modified Title");
    }

    #[test]
    fn test_list_sessions() {
        let (store, _temp) = create_test_store();

        let s1 = store.create_session("First".to_string()).unwrap();
        let s2 = store.create_session("Second".to_string()).unwrap();

        // Need to ensure different updated_at times for deterministic test
        std::thread::sleep(std::time::Duration::from_millis(10));
        let s3 = store.create_session("Third".to_string()).unwrap();

        let sessions = store.list_sessions().unwrap();
        assert_eq!(sessions.len(), 3);

        // Should be sorted by updated_at descending (most recent first)
        assert_eq!(sessions[0].id, s3.id);
        assert_eq!(sessions[1].id, s2.id);
        assert_eq!(sessions[2].id, s1.id);
    }

    #[test]
    fn test_list_sessions_empty() {
        let (store, _temp) = create_test_store();

        let sessions = store.list_sessions().unwrap();
        assert!(sessions.is_empty());
    }

    #[test]
    fn test_delete_session() {
        let (store, _temp) = create_test_store();

        let session = store.create_session("To Delete".to_string()).unwrap();
        assert!(store.get_session(session.id).unwrap().is_some());

        let deleted = store.delete_session(session.id).unwrap();
        assert!(deleted);
        assert!(store.get_session(session.id).unwrap().is_none());
    }

    #[test]
    fn test_delete_session_not_found() {
        let (store, _temp) = create_test_store();

        let result = store.delete_session(Uuid::new_v4()).unwrap();
        assert!(!result);
    }

    #[test]
    fn test_auto_create_sessions_dir() {
        let temp_dir = TempDir::new().unwrap();
        let sessions_dir = temp_dir.path().join("nonexistent").join("sessions");

        let store = SessionStore {
            sessions_dir: sessions_dir.clone(),
        };

        // Should auto-create the directory
        let session = store.create_session("Auto Create Test".to_string()).unwrap();
        assert!(sessions_dir.exists());
        assert!(store.get_session(session.id).unwrap().is_some());
    }
}
