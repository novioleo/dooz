use crossterm::event::{Event, KeyCode, KeyEventKind};
use crossterm::execute;
use ratatui::Frame;

use crate::action::{Action, ChatAction};

/// Terminal UI wrapper providing event handling and rendering
#[derive(Debug)]
pub struct Tui {
    terminal: ratatui::Terminal<ratatui::backend::CrosstermBackend<std::io::Stdout>>,
}

impl Tui {
    /// Create a new Tui instance
    pub fn new(
        terminal: ratatui::Terminal<ratatui::backend::CrosstermBackend<std::io::Stdout>>,
    ) -> Self {
        Self { terminal }
    }

    /// Enter the terminal UI mode - enables raw mode and alternate screen
    pub fn enter(&mut self) -> std::io::Result<()> {
        use crossterm::terminal::{enable_raw_mode, EnterAlternateScreen};
        use crossterm::event::EnableMouseCapture;

        // Enable raw mode for direct terminal control
        enable_raw_mode()?;

        // Enter the alternate screen (provides a fresh terminal for TUI)
        execute!(std::io::stdout(), EnterAlternateScreen)?;

        // Enable mouse capture for mouse events
        execute!(std::io::stdout(), EnableMouseCapture)?;

        // Hide the cursor for a cleaner look
        self.terminal.hide_cursor()?;

        // Clear the terminal
        self.terminal.clear()?;

        // Set panic hook to restore terminal on panic
        let original_hook = std::panic::take_hook();
        std::panic::set_hook(Box::new(move |panic_info| {
            let _ = Self::cleanup();
            original_hook(panic_info);
        }));

        Ok(())
    }

    /// Exit the terminal UI mode - restores terminal to previous state
    pub fn exit(&mut self) -> std::io::Result<()> {
        Self::cleanup()?;
        self.terminal.show_cursor()?;
        Ok(())
    }

    /// Cleanup terminal state (used by panic hook and exit)
    fn cleanup() -> std::io::Result<()> {
        use crossterm::terminal::{disable_raw_mode, LeaveAlternateScreen};
        use crossterm::event::DisableMouseCapture;

        // Ignore errors during cleanup to avoid cascading failures
        let _ = execute!(std::io::stdout(), DisableMouseCapture);
        let _ = disable_raw_mode();
        let _ = execute!(std::io::stdout(), LeaveAlternateScreen);
        Ok(())
    }

    /// Draw a single frame
    pub fn draw<F>(&mut self, f: F) -> std::io::Result<()>
    where
        F: FnOnce(&mut Frame),
    {
        self.terminal.draw(f)?;
        Ok(())
    }

    /// Handle input events, returning the corresponding Action
    pub fn handle_events(&mut self) -> std::io::Result<Option<Action>> {
        use crossterm::event::read;

        // Check if there's an event available without blocking
        if !crossterm::event::poll(std::time::Duration::from_millis(10))? {
            return Ok(None);
        }

        // Read the event (we know one is available now)
        let event = read()?;

        // Handle the event and return the corresponding action
        Ok(Some(Self::map_event_to_action(event)?))
    }

    /// Map crossterm events to application actions
    fn map_event_to_action(event: Event) -> std::io::Result<Action> {
        match event {
            Event::Key(key_event) => {
                // Only handle key press events (not key release)
                if key_event.kind != KeyEventKind::Press {
                    return Ok(Action::Render);
                }

                // Handle Alt+number for fragment switching (like tmux)
                if key_event.modifiers == crossterm::event::KeyModifiers::ALT {
                    if let KeyCode::Char(c) = key_event.code {
                        if let Some(n) = c.to_digit(10) {
                            return Ok(Action::SwitchToFragment(n as usize));
                        }
                    }
                }

                match key_event.code {
                    KeyCode::Char(c) => {
                        // Handle all character input
                        Ok(Action::Chat(ChatAction::InputChar(c)))
                    }
                    KeyCode::Backspace => Ok(Action::Chat(ChatAction::InputBackspace)),
                    KeyCode::Left => Ok(Action::Chat(ChatAction::InputLeft)),
                    KeyCode::Right => Ok(Action::Chat(ChatAction::InputRight)),
                    KeyCode::Enter => {
                        // Check if Shift is pressed - if so, insert newline
                        if key_event.modifiers.contains(crossterm::event::KeyModifiers::SHIFT) {
                            Ok(Action::Chat(ChatAction::InputEnter))
                        } else {
                            // Regular Enter sends the input
                            Ok(Action::Chat(ChatAction::SendInput))
                        }
                    }
                    KeyCode::Up => Ok(Action::Chat(ChatAction::Scroll(1))),
                    KeyCode::Down => Ok(Action::Chat(ChatAction::Scroll(-1))),
                    KeyCode::Esc => Ok(Action::Exit),
                    KeyCode::Home => Ok(Action::Chat(ChatAction::ScrollToBottom)),
                    KeyCode::End => Ok(Action::Chat(ChatAction::ScrollToBottom)),
                    _ => Ok(Action::Render),
                }
            }
            Event::Mouse(mouse_event) => {
                use crossterm::event::MouseEventKind;

                match mouse_event.kind {
                    MouseEventKind::ScrollUp => {
                        // Route scroll to the active region in the fragment
                        Ok(Action::Chat(ChatAction::Scroll(1))) // Positive = up
                    }
                    MouseEventKind::ScrollDown => {
                        // Route scroll to the active region in the fragment
                        Ok(Action::Chat(ChatAction::Scroll(-1))) // Negative = down
                    }
                    MouseEventKind::Down(_) => {
                        // Pass click coordinates to app for session selection
                        Ok(Action::MouseClick {
                            x: mouse_event.column,
                            y: mouse_event.row,
                        })
                    }
                    _ => Ok(Action::Render),
                }
            }
            Event::Resize(_, _) => {
                // Terminal was resized - just re-render
                Ok(Action::Render)
            }
            Event::FocusGained | Event::FocusLost | Event::Paste(_) => {
                // Other events - just re-render
                Ok(Action::Render)
            }
        }
    }
}
