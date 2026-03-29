use uuid::Uuid;

use crate::action::ChatAction;

use super::model::{ChatMessage, ChatModel};

/// Update function for chat fragment - processes ChatAction and mutates model
pub fn update(model: &mut ChatModel, action: ChatAction) {
    match action {
        ChatAction::SendMessage(content) => {
            let message = ChatMessage {
                id: Uuid::new_v4().to_string(),
                from: "self".to_string(),
                content,
                timestamp: chrono::Utc::now(),
            };
            model.messages.push(message);
        }
        ChatAction::ReceiveMessage { from, content } => {
            let message = ChatMessage {
                id: Uuid::new_v4().to_string(),
                from,
                content,
                timestamp: chrono::Utc::now(),
            };
            model.messages.push(message);
        }
        ChatAction::SelectConversation(conv_id) => {
            model.selected_conversation = Some(conv_id);
        }
    }
}
