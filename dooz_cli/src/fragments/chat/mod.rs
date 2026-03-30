mod model;
mod update;
mod view;

pub use model::ChatModel;
pub use update::update;
pub use view::render;

pub type ChatAction = crate::action::ChatAction;
