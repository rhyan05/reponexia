mod models;
mod scan;
mod parse;
mod resolve;

use std::fs;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use sha2::{Digest, Sha256};

use models::{FileEntry, Graph, Warning};

#[derive(Parser)]
#[command(name = "reponexia-core", version, about = "Motor de análise do RepoNexia")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Indexa um repositório e emite graph.json
    Index {
        /// Raiz do repositório a analisar
        path: PathBuf,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Command::Index { path } => {
            let graph = build_graph(&path)?;
            serde_json::to_writer_pretty(std::io::stdout(), &graph)?;
            println!();
        }
    }

    Ok(())
}

fn build_graph(input: &Path) -> Result<Graph, Box<dyn std::error::Error>> {
    let root = fs::canonicalize(input)?;

    let mut paths = scan::collect_files(&root);
    paths.sort();

    let mut parser = parse::new_parser()?;
    let mut files = Vec::new();
    let mut warnings = Vec::new();
    let mut symbols = Vec::new();
    let mut raw_imports = Vec::new();

    for path in paths {
        let Ok(rel) = path.strip_prefix(&root) else {
            continue;
        };
        let rel = rel.to_string_lossy().replace('\\', "/");

        match fs::read(&path) {
            Ok(bytes) => {
                let language = language_of(&path);

                if language == "python" {
                    match parse::parse_python(&rel, &bytes, &mut parser) {
                        Ok(out) => {
                            symbols.extend(out.symbols);
                            raw_imports.extend(out.imports);
                        }
                        Err(message) => warnings.push(Warning {
                            message,
                            path: Some(rel.clone()),
                        }),
                    }
                }

                files.push(FileEntry {
                    path: rel,
                    language: language.to_string(),
                    loc: count_lines(&bytes),
                    hash: sha256_hex(&bytes),
                    parse_errors: Vec::new(),
                });
            }
            Err(err) => warnings.push(Warning {
                message: err.to_string(),
                path: Some(rel),
            }),
        }
    }

    files.sort_by(|a, b| a.path.cmp(&b.path));
    symbols.sort_by(|a, b| (&a.id, a.line).cmp(&(&b.id, b.line)));
    let edges = resolve::resolve_imports(&files, &raw_imports);

    let mut languages: Vec<String> = files.iter().map(|f| f.language.clone()).collect();
    languages.sort();
    languages.dedup();

    let mut repo_hasher = Sha256::new();
    for file in &files {
        repo_hasher.update(file.hash.as_bytes());
    }
    let repo_hash = to_hex(repo_hasher.finalize());

    let root_display = {
        let raw = root.to_string_lossy();
        let trimmed = raw.strip_prefix(r"\\?\").unwrap_or(&raw);
        trimmed.replace('\\', "/")
    };

    Ok(Graph {
        schema_version: "1.0".to_string(),
        root: root_display,
        repo_hash,
        languages,
        files,
        warnings,
        symbols,
        edges,
    })
}

fn language_of(path: &Path) -> &'static str {
    match path.extension().and_then(|ext| ext.to_str()) {
        Some("py") => "python",
        Some("js") | Some("jsx") => "javascript",
        Some("ts") | Some("tsx") => "typescript",
        Some("rs") => "rust",
        Some("go") => "go",
        Some("java") => "java",
        _ => "unknown",
    }
}

fn count_lines(bytes: &[u8]) -> usize {
    if bytes.is_empty() {
        0
    } else {
        bytes.iter().filter(|&&b| b == b'\n').count() + 1
    }
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    to_hex(hasher.finalize())
}

fn to_hex(bytes: impl AsRef<[u8]>) -> String {
    bytes.as_ref().iter().map(|b| format!("{b:02x}")).collect()
}


