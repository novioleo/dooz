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

    fn view(&mut self, frame: &mut Frame) {
        let chunk = frame.area();
        chat::render(&mut self.model, frame, chunk);
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

    /// Set active fragment by index (0-based, for Alt+number shortcuts)
    /// Returns true if successful, false if index is out of bounds
    pub fn set_active_by_index(&mut self, index: usize) -> bool {
        // Get all fragment IDs and sort them
        let fragment_ids: Vec<FragmentId> = self.fragments.keys().cloned().collect();
        if index < fragment_ids.len() {
            let id = fragment_ids[index];
            self.active = id;
            true
        } else {
            false
        }
    }

    /// Get the active fragment ID.
    #[allow(dead_code)]
    pub fn active_id(&self) -> FragmentId {
        self.active
    }

    /// Get the index of the active fragment (for display purposes)
    pub fn active_index(&self) -> usize {
        let mut fragment_ids: Vec<FragmentId> = self.fragments.keys().cloned().collect();
        fragment_ids.sort_by_key(|&id| id as u8);
        fragment_ids.iter().position(|&id| id == self.active).unwrap_or(0)
    }

    /// Get total number of fragments (for display purposes)
    pub fn fragment_count(&self) -> usize {
        self.fragments.len()
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
    pub fn view(&mut self, frame: &mut Frame) {
        if let Some(fragment) = self.fragments.get_mut(&self.active) {
            fragment.view(frame);
        }
    }
}

impl<F: Fragment> Default for FragmentRegistry<F> {
    fn default() -> Self {
        Self::new()
    }
}
