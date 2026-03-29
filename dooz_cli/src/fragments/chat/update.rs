use uuid::Uuid;

use crate::action::{Action, ChatAction};
use crate::session::types::{Message, MessageRole, Session};

use super::model::ChatModel;

/// Update function for chat fragment - processes ChatAction and mutates model
/// Returns Some(Action) for actions that need to be handled at the app level
pub fn update(model: &mut ChatModel, action: ChatAction) -> Option<Action> {
    match action {
        ChatAction::SendMessage(content) => {
            let message = Message::new(MessageRole::User, content);
            model.add_message(message);
            None
        }
        ChatAction::ReceiveMessage { from: _, content } => {
            let message = Message::new(MessageRole::Assistant, content);
            model.add_message(message);
            None
        }
        ChatAction::LoadSessions(sessions) => {
            // Convert SessionInfo to Session for storage
            model.sessions = sessions.into_iter().map(|info| {
                Session {
                    id: info.id,
                    title: info.title,
                    created_at: info.updated_at, // Approximation
                    updated_at: info.updated_at,
                    messages: Vec::new(),
                }
            }).collect();
            
            // Auto-select first session if available
            if !model.sessions.is_empty() {
                model.session_list_state.select(Some(0));
                model.active_session_id = Some(model.sessions[0].id);
            }
            None
        }
        ChatAction::SelectSession(index) => {
            model.select_session(index);
            None
        }
        ChatAction::SelectSessionById(id) => {
            if let Some(index) = model.sessions.iter().position(|s| s.id == id) {
                model.select_session(index);
            }
            None
        }
        ChatAction::SelectConversation(_) => {
            // Conversation selection is handled at the app level
            // Chat fragment just displays messages for now
            None
        }
        ChatAction::ScrollUp => {
            model.scroll_up();
            None
        }
        ChatAction::ScrollDown => {
            model.scroll_down();
            None
        }
        ChatAction::ScrollToBottom => {
            model.scroll_to_bottom();
            None
        }
        ChatAction::InputChar(c) => {
            model.insert_char(c);
            None
        }
        ChatAction::InputBackspace => {
            model.delete_back();
            None
        }
        ChatAction::InputLeft => {
            model.move_cursor_left();
            None
        }
        ChatAction::InputRight => {
            model.move_cursor_right();
            None
        }
        ChatAction::InputEnter => {
            if !model.input_buffer.is_empty() {
                let content = model.get_input_content();
                
                // Check for commands (input starting with /)
                match content.trim() {
                    "/new" => {
                        model.clear_input();
                        return Some(Action::Chat(ChatAction::CreateSession));
                    }
                    "/exit" => {
                        model.clear_input();
                        return Some(Action::Exit);
                    }
                    _ => {
                        model.clear_input();
                        // Send the message
                        let message = Message::new(MessageRole::User, content);
                        model.add_message(message);
                    }
                }
            }
            None
        }
        ChatAction::ClearInput => {
            model.clear_input();
            None
        }
        ChatAction::CreateSession => {
            // This is handled at the app level via Action::Chat(CreateSession)
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_send_message_adds_to_model() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::SendMessage("Hello".to_string()));
        
        assert_eq!(model.messages.len(), 1);
        assert_eq!(model.messages[0].content, "Hello");
        assert_eq!(model.messages[0].role, MessageRole::User);
    }

    #[test]
    fn test_receive_message_adds_to_model() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::ReceiveMessage { 
            from: "assistant".to_string(), 
            content: "Hi there".to_string() 
        });
        
        assert_eq!(model.messages.len(), 1);
        assert_eq!(model.messages[0].content, "Hi there");
        assert_eq!(model.messages[0].role, MessageRole::Assistant);
    }

    #[test]
    fn test_auto_scroll_on_new_message() {
        let mut model = ChatModel::new();
        assert!(model.auto_scroll); // Default is true
        
        model.scroll_up(); // User scrolled up
        assert!(!model.auto_scroll);
        
        update(&mut model, ChatAction::SendMessage("New message".to_string()));
        assert!(model.auto_scroll); // Auto-scroll re-enabled
    }

    #[test]
    fn test_load_sessions() {
        let mut model = ChatModel::new();
        let session_info = crate::action::SessionInfo {
            id: Uuid::new_v4(),
            title: "Test Session".to_string(),
            updated_at: chrono::Utc::now(),
        };
        
        update(&mut model, ChatAction::LoadSessions(vec![session_info.clone()]));
        
        assert_eq!(model.sessions.len(), 1);
        assert_eq!(model.sessions[0].title, "Test Session");
        assert!(model.active_session_id.is_some());
    }

    #[test]
    fn test_select_session() {
        let mut model = ChatModel::new();
        let session1 = crate::action::SessionInfo {
            id: Uuid::new_v4(),
            title: "Session 1".to_string(),
            updated_at: chrono::Utc::now(),
        };
        let session2 = crate::action::SessionInfo {
            id: Uuid::new_v4(),
            title: "Session 2".to_string(),
            updated_at: chrono::Utc::now(),
        };
        
        update(&mut model, ChatAction::LoadSessions(vec![session1, session2]));
        
        // Initially first session is selected
        assert_eq!(model.active_session_id, Some(model.sessions[0].id));
        
        // Select second session
        update(&mut model, ChatAction::SelectSession(1));
        
        assert_eq!(model.active_session_id, Some(model.sessions[1].id));
    }

    #[test]
    fn test_input_char() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        
        assert_eq!(model.input_buffer, "hi");
        assert_eq!(model.cursor_position, 2);
    }

    #[test]
    fn test_input_backspace() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        assert_eq!(model.input_buffer, "hi");
        
        update(&mut model, ChatAction::InputBackspace);
        assert_eq!(model.input_buffer, "h");
        assert_eq!(model.cursor_position, 1);
    }

    #[test]
    fn test_input_enter_sends_message() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        
        // Press Enter to send
        let result = update(&mut model, ChatAction::InputEnter);
        
        // Input should be cleared
        assert_eq!(model.input_buffer, "");
        assert_eq!(model.cursor_position, 0);
        
        // Message should be in the chat
        assert_eq!(model.messages.len(), 1);
        assert_eq!(model.messages[0].content, "hi");
        assert_eq!(model.messages[0].role, MessageRole::User);
        
        // Should return None for regular messages
        assert!(result.is_none());
    }

    #[test]
    fn test_input_enter_empty_does_nothing() {
        let mut model = ChatModel::new();
        
        // Press Enter with empty input
        let result = update(&mut model, ChatAction::InputEnter);
        
        // No message should be added
        assert_eq!(model.messages.len(), 0);
        
        // Should return None
        assert!(result.is_none());
    }

    #[test]
    fn test_clear_input() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        assert_eq!(model.input_buffer, "hi");
        
        update(&mut model, ChatAction::ClearInput);
        
        assert_eq!(model.input_buffer, "");
        assert_eq!(model.cursor_position, 0);
    }

    #[test]
    fn test_cursor_left() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        assert_eq!(model.cursor_position, 2);
        
        update(&mut model, ChatAction::InputLeft);
        assert_eq!(model.cursor_position, 1);
        
        update(&mut model, ChatAction::InputLeft);
        assert_eq!(model.cursor_position, 0);
    }

    #[test]
    fn test_cursor_right() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('i'));
        assert_eq!(model.cursor_position, 2);
        
        update(&mut model, ChatAction::InputLeft);
        update(&mut model, ChatAction::InputLeft);
        assert_eq!(model.cursor_position, 0);
        
        update(&mut model, ChatAction::InputRight);
        assert_eq!(model.cursor_position, 1);
    }

    #[test]
    fn test_input_new_command_returns_create_session() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('/'));
        update(&mut model, ChatAction::InputChar('n'));
        update(&mut model, ChatAction::InputChar('e'));
        update(&mut model, ChatAction::InputChar('w'));
        
        assert_eq!(model.input_buffer, "/new");
        
        // Press Enter to execute command
        let result = update(&mut model, ChatAction::InputEnter);
        
        // Should return CreateSession action
        assert!(result.is_some());
        assert_eq!(result.unwrap(), Action::Chat(ChatAction::CreateSession));
        
        // Input should be cleared
        assert_eq!(model.input_buffer, "");
    }

    #[test]
    fn test_input_exit_command_returns_exit() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('/'));
        update(&mut model, ChatAction::InputChar('e'));
        update(&mut model, ChatAction::InputChar('x'));
        update(&mut model, ChatAction::InputChar('i'));
        update(&mut model, ChatAction::InputChar('t'));
        
        assert_eq!(model.input_buffer, "/exit");
        
        // Press Enter to execute command
        let result = update(&mut model, ChatAction::InputEnter);
        
        // Should return Exit action
        assert!(result.is_some());
        assert_eq!(result.unwrap(), Action::Exit);
        
        // Input should be cleared
        assert_eq!(model.input_buffer, "");
    }

    #[test]
    fn test_input_unknown_command_sends_as_message() {
        let mut model = ChatModel::new();
        update(&mut model, ChatAction::InputChar('/'));
        update(&mut model, ChatAction::InputChar('h'));
        update(&mut model, ChatAction::InputChar('e'));
        update(&mut model, ChatAction::InputChar('l'));
        update(&mut model, ChatAction::InputChar('p'));
        
        assert_eq!(model.input_buffer, "/help");
        
        // Press Enter - unknown commands are sent as messages
        let result = update(&mut model, ChatAction::InputEnter);
        
        // Should return None and send as message
        assert!(result.is_none());
        assert_eq!(model.messages.len(), 1);
        assert_eq!(model.messages[0].content, "/help");
        assert_eq!(model.messages[0].role, MessageRole::User);
    }
}
