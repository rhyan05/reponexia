use std::path::{Path, PathBuf};

use ignore::WalkBuilder;

// Walk com semântica de .gitignore (inclusive de diretórios pais).
// Esconde dotfiles (/ .git / .env) e já ignora .reponexia explicitamente.
pub fn collect_files(root: &Path) -> Vec<PathBuf> {
    WalkBuilder::new(root)
        .hidden(true)
        .git_ignore(true)
        .git_global(true)
        .git_exclude(true)
        .filter_entry(|entry| entry.file_name() != ".reponexia")
        .build()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().map(|kind| kind.is_file()).unwrap_or(false))
        .map(|entry| entry.into_path())
        .collect()
}
