/// Action enum representing all possible user actions/events in the TEA pattern.
#[derive(Debug, Clone, PartialEq)]
pub enum Action {
    // Application lifecycle
    Init,
    Quit,

    // UI actions
    Render,
    Resize(u16, u16),

    // Fragment actions
    Chat(ChatAction),
}

/// Chat fragment actions
#[derive(Debug, Clone, PartialEq)]
pub enum ChatAction {
    SendMessage(String),
    ReceiveMessage { from: String, content: String },
    SelectConversation(String),
}
