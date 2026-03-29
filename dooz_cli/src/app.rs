use ratatui::{layout::Rect, Frame};

use crate::action::{Action, ChatAction};
use crate::fragments::ChatFragment;
use crate::fragments::{Fragment, FragmentId, FragmentRegistry};
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
    pub fn new() -> Self {
        let mut registry = FragmentRegistry::new();
        registry.register(FragmentId::Chat, ChatFragment::new());
        registry.set_active(FragmentId::Chat);

        let session_store = SessionStore::new().expect("Failed to create session store");
        
        // Auto-create a session on startup with timestamp title
        let title = chrono::Utc::now().format("%Y-%m-%d %H:%M").to_string();
        let session = session_store.create_session(title).expect("Failed to create initial session");

        let mut app = Self {
            session_store,
            registry,
            should_quit: false,
        };

        // Load the initial session into the chat fragment
        if let Some(chat_fragment) = app.registry.get_mut(FragmentId::Chat) {
            chat_fragment.model.load_sessions(vec![session]);
        }

        app
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
                if let Ok(session) = self.session_store.create_session(title) {
                    // Load sessions to update the chat fragment
                    if let Ok(sessions) = self.session_store.list_sessions() {
                        if let Some(chat_fragment) = self.registry.get_mut(FragmentId::Chat) {
                            chat_fragment.model.load_sessions(sessions);
                            // Select the newly created session
                            chat_fragment.model.select_session_by_id(session.id);
                        }
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
}

impl Default for App {
    fn default() -> Self {
        Self::new()
    }
}

/// Main application loop
pub fn run_app(terminal: &mut Tui, mut app: App) -> std::io::Result<()> {
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
            break;
        }

        // Process events
        if let Ok(Some(action)) = terminal.handle_events() {
            if let Some(next_action) = app.update(action) {
                if next_action == Action::Quit || next_action == Action::Exit || app.should_quit {
                    break;
                }
                app.update(next_action);
            }
        }
    }

    Ok(())
}
