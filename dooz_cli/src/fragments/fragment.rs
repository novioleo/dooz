//! Fragment trait defining the interface for all UI fragments.
//!
//! Each fragment implements the TEA (The Elm Architecture) pattern with:
//! - `Model`: Fragment-specific state
//! - `update()`: Handle actions and potentially return new actions
//! - `view()`: Render the fragment to the terminal frame

use ratatui::Frame;

use crate::action::Action;

/// Fragment trait for modular UI components.
///
/// Implement this trait to create new fragments that can be
/// registered and managed by the FragmentRegistry.
pub trait Fragment {
    /// Fragment-specific model state
    type Model: Default;

    /// Get a reference to the fragment's model.
    fn model(&self) -> &Self::Model;

    /// Get a mutable reference to the fragment's model.
    fn model_mut(&mut self) -> &mut Self::Model;

    /// Update the fragment's model based on an action.
    ///
    /// Returns an optional action to be processed by the app.
    fn update(&mut self, action: Action) -> Option<Action>;

    /// Render the fragment to the terminal frame.
    fn view(&mut self, frame: &mut Frame);
}
