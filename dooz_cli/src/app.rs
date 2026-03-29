use ratatui::{layout::Rect, Frame};

use crate::action::Action;
use crate::fragments::chat::{self, ChatModel};
use crate::session::store::SessionStore;
use crate::tui::Tui;

/// Main application state following TEA pattern.
#[derive(Debug)]
pub struct App {
    pub session_store: SessionStore,
    pub chat_model: ChatModel,
}

impl App {
    pub fn new() -> Self {
        Self {
            session_store: SessionStore::new(),
            chat_model: ChatModel::default(),
        }
    }

    /// Main update function - processes actions and returns new state
    pub fn update(&mut self, action: Action) -> Option<Action> {
        match action {
            Action::Init => Some(Action::Render),
            Action::Quit => None,
            Action::Render => Some(Action::Render),
            Action::Resize(_, _) => Some(Action::Render),
            Action::Chat(chat_action) => {
                chat::update(&mut self.chat_model, chat_action);
                Some(Action::Render)
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

        // Process events
        if let Ok(Some(action)) = terminal.handle_events() {
            if let Some(next_action) = app.update(action) {
                if next_action == Action::Quit {
                    break;
                }
                app.update(next_action);
            }
        }
    }

    Ok(())
}
