use ratatui::{layout::Rect, Frame};

use crate::action::{Action, ChatAction};
use crate::fragments::ChatFragment;
use crate::fragments::{FragmentId, FragmentRegistry};
use crate::session::store::SessionStore;
use crate::tui::Tui;

/// Main application state following TEA pattern.
#[derive(Debug)]
pub struct App {
    pub session_store: SessionStore,
    pub registry: FragmentRegistry<ChatFragment>,
    pub should_quit: bool,
}

impl App {
    /// Create a new App instance
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let mut registry = FragmentRegistry::new();
        registry.register(FragmentId::Chat, ChatFragment::new());
        registry.set_active(FragmentId::Chat);

        let session_store = SessionStore::new()
            .map_err(|e| format!("Failed to create session store: {}", e))?;

        // Load existing sessions or create a new one
        let sessions = session_store
            .list_sessions()
            .map_err(|e| format!("Failed to load sessions: {}", e))?;

        let mut app = Self {
            session_store,
            registry,
            should_quit: false,
        };

        if sessions.is_empty() {
            // Auto-create a session on startup with timestamp title
            let title = chrono::Utc::now().format("%Y-%m-%d %H:%M").to_string();
            match app.session_store.create_session(title) {
                Ok(session) => {
                    if let Some(chat_fragment) = app.registry.get_mut(FragmentId::Chat) {
                        chat_fragment.model.load_sessions(vec![session]);
                    }
                }
                Err(e) => {
                    tracing::warn!("Failed to create initial session: {}", e);
                }
            }
        } else {
            // Load existing sessions
            if let Some(chat_fragment) = app.registry.get_mut(FragmentId::Chat) {
                chat_fragment.model.load_sessions(sessions);
            }
        }

        Ok(app)
    }

    /// Main update function - processes actions and returns new state
    pub fn update(&mut self, action: Action) -> Option<Action> {
        match action {
            Action::Init => Some(Action::Render),
            Action::Quit | Action::Exit => {
                self.should_quit = true;
                None
            }
            Action::Render => Some(Action::Render),
            Action::Resize(_, _) => Some(Action::Render),
            Action::Chat(ChatAction::CreateSession) => {
                // Create a new session with timestamp title
                let title = chrono::Utc::now().format("%Y-%m-%d %H:%M").to_string();
                match self.session_store.create_session(title) {
                    Ok(session) => {
                        // Load sessions to update the chat fragment
                        match self.session_store.list_sessions() {
                            Ok(sessions) => {
                                if let Some(chat_fragment) = self.registry.get_mut(FragmentId::Chat) {
                                    chat_fragment.model.load_sessions(sessions);
                                    // Select the newly created session
                                    chat_fragment.model.select_session_by_id(session.id);
                                }
                            }
                            Err(e) => {
                                tracing::warn!("Failed to reload sessions after creating new: {}", e);
                            }
                        }
                    }
                    Err(e) => {
                        tracing::error!("Failed to create new session: {}", e);
                    }
                }
                Some(Action::Render)
            }
            Action::Chat(_) => {
                // Route chat actions to the registry (active fragment)
                self.registry.update(action)
            }
        }
    }

    /// View function - renders the UI
    pub fn view(&self, f: &mut Frame, chunk: Rect) {
        crate::ui::layout::render(self, f, chunk);
    }

    /// Save the current session state
    pub fn save_current_session(&self) {
        if let Some(chat_fragment) = self.registry.get(FragmentId::Chat) {
            let session = chat_fragment.model.get_active_session();
            if let Some(session) = session {
                if let Err(e) = self.session_store.save_session(session) {
                    tracing::error!("Failed to save session: {}", e);
                }
            }
        }
    }
}

impl Default for App {
    fn default() -> Self {
        Self::new().unwrap_or_else(|e| {
            // If we can't create the app, we have to panic
            // but first try to cleanup the terminal
            let _ = crossterm::terminal::disable_raw_mode();
            let _ = crossterm::execute!(std::io::stdout(), crossterm::terminal::LeaveAlternateScreen);
            panic!("Failed to create app: {}", e);
        })
    }
}

/// Main application loop
pub fn run_app(terminal: &mut Tui) -> std::io::Result<()> {
    let mut app = match App::new() {
        Ok(app) => app,
        Err(e) => {
            eprintln!("Error creating app: {}", e);
            return Ok(());
        }
    };

    // Send init action
    if let Some(action) = app.update(Action::Init) {
        app.update(action);
    }

    loop {
        terminal.draw(|f| {
            let size = f.area();
            app.view(f, size);
        })?;

        // Check if app should quit
        if app.should_quit {
            // Save current session before exiting
            app.save_current_session();
            break;
        }

        // Process events
        match terminal.handle_events() {
            Ok(Some(action)) => {
                if let Some(next_action) = app.update(action) {
                    if next_action == Action::Quit || next_action == Action::Exit || app.should_quit {
                        // Save current session before exiting
                        app.save_current_session();
                        break;
                    }
                    app.update(next_action);
                }
            }
            Ok(None) => {
                // No event, continue
            }
            Err(e) => {
                tracing::error!("Error handling events: {}", e);
            }
        }
    }

    Ok(())
}
