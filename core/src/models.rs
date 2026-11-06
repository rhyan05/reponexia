use serde::Serialize;

#[derive(Serialize)]
pub struct Graph {
    pub schema_version: String,
    pub root: String,
    pub repo_hash: String,
    pub languages: Vec<String>,
    pub files: Vec<FileEntry>,
    pub warnings: Vec<Warning>,
}

#[derive(Serialize)]
pub struct FileEntry {
    pub path: String,
    pub language: String,
    pub loc: usize,
    pub hash: String,
    pub parse_errors: Vec<String>,
}

#[derive(Serialize)]
pub struct Warning {
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
}
