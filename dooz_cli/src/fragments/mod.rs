//! Fragment system for modular UI components.
//!
//! This module provides the Fragment trait, FragmentId enum, and FragmentRegistry
//! for managing multiple UI fragments in a TEA-like architecture.

mod fragment;

pub mod chat;

use std::collections::HashMap;

use ratatui::Frame;

use crate::action::Action;

pub use fragment::Fragment;

/// Identifier for registered fragments.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FragmentId {
    Chat, // Fragment1
    // Future: Settings,
    // Future: Help,
}

/// Chat fragment that wraps the chat module's functionality.
///
/// This struct implements the Fragment trait using the existing
/// chat module's model and update/view functions.
#[derive(Debug, Default)]
pub struct ChatFragment {
    pub model: chat::ChatModel,
}

impl ChatFragment {
    /// Create a new ChatFragment with a default model.
    pub fn new() -> Self {
        Self {
            model: chat::ChatModel::default(),
        }
    }
}

impl Fragment for ChatFragment {
    type Model = chat::ChatModel;

    fn model(&self) -> &Self::Model {
        &self.model
    }

    fn model_mut(&mut self) -> &mut Self::Model {
        &mut self.model
    }

    fn update(&mut self, action: Action) -> Option<Action> {
        match action {
            Action::Chat(chat_action) => {
                let result = chat::update(&mut self.model, chat_action);
                // If the chat update returns an action (like CreateSession or Exit), propagate it
                // Otherwise, return Render to trigger re-render
                result.or(Some(Action::Render))
            }
            _ => None,
        }
    }

    fn view(&self, frame: &mut Frame) {
        let chunk = frame.area();
        chat::render(&self.model, frame, chunk);
    }
}

/// Registry for managing fragments and routing actions to the active fragment.
///
/// The registry maintains a collection of fragments and routes actions
/// to the currently active fragment based on its ID.
#[derive(Debug)]
pub struct FragmentRegistry<F: Fragment> {
    fragments: HashMap<FragmentId, F>,
    active: FragmentId,
}

impl<F: Fragment> FragmentRegistry<F> {
    /// Create a new empty FragmentRegistry.
    pub fn new() -> Self {
        Self {
            fragments: HashMap::new(),
            active: FragmentId::Chat, // Default to Chat
        }
    }

    /// Register a fragment with the given ID.
    ///
    /// If a fragment with the same ID already exists, it will be replaced.
    pub fn register(&mut self, id: FragmentId, fragment: F) {
        self.fragments.insert(id, fragment);
    }

    /// Set the active fragment by ID.
    ///
    /// # Panics
    /// Panics if no fragment is registered with the given ID.
    pub fn set_active(&mut self, id: FragmentId) {
        if !self.fragments.contains_key(&id) {
            panic!("No fragment registered with ID: {:?}", id);
        }
        self.active = id;
    }

    /// Get the active fragment ID.
    #[allow(dead_code)]
    pub fn active_id(&self) -> FragmentId {
        self.active
    }

    /// Get a mutable reference to a fragment by ID.
    ///
    /// # Panics
    /// Panics if no fragment is registered with the given ID.
    #[allow(dead_code)]
    pub fn get_mut(&mut self, id: FragmentId) -> Option<&mut F> {
        self.fragments.get_mut(&id)
    }

    /// Get an immutable reference to a fragment by ID.
    #[allow(dead_code)]
    pub fn get(&self, id: FragmentId) -> Option<&F> {
        self.fragments.get(&id)
    }

    /// Update the active fragment with the given action.
    ///
    /// Routes the action to the active fragment's update method.
    /// Returns an optional action produced by the fragment's update.
    pub fn update(&mut self, action: Action) -> Option<Action> {
        let fragment = self.fragments.get_mut(&self.active)?;
        fragment.update(action)
    }

    /// Render the active fragment to the terminal frame.
    pub fn view(&self, frame: &mut Frame) {
        if let Some(fragment) = self.fragments.get(&self.active) {
            fragment.view(frame);
        }
    }
}

impl<F: Fragment> Default for FragmentRegistry<F> {
    fn default() -> Self {
        Self::new()
    }
}
