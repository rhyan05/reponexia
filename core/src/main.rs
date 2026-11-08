mod models;
mod scan;
mod parse;
mod resolve;
mod analyze;
mod entrypoints;

use std::fs;
use std::path::{Path, PathBuf};
use std::time::Instant;

use clap::{Parser, Subcommand};
use rayon::prelude::*;
use sha2::{Digest, Sha256};

use entrypoints::RawScriptImport;
use models::{Entrypoint, FileEntry, Graph, Symbol, Warning};
use parse::{ParsedFile, RawImport};

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
        /// Grava o JSON em arquivo em vez de stdout
        #[arg(long)]
        out: Option<PathBuf>,
        /// Filtra linguagens: --lang python,typescript
        #[arg(long, value_delimiter = ',')]
        lang: Vec<String>,
        /// Número de threads do parse paralelo
        #[arg(long)]
        jobs: Option<usize>,
        /// Métricas de execução no stderr
        #[arg(long)]
        verbose: bool,
    },
}

// Resultado do processamento de um arquivo, pronto para merge determinístico.
struct FileOutput {
    entry: FileEntry,
    symbols: Vec<Symbol>,
    imports: Vec<RawImport>,
    entry_points: Vec<Entrypoint>,
    script_imports: Vec<RawScriptImport>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Command::Index {
            path,
            out,
            lang,
            jobs,
            verbose,
        } => {
            let graph = build_graph(&path, &lang, jobs, verbose)?;
            let json = serde_json::to_string_pretty(&graph)?;

            match out {
                Some(path) => {
                    fs::write(&path, json + "\n")?;
                    if verbose {
                        eprintln!("[verbose] grafo escrito em {}", path.display());
                    }
                }
                None => println!("{json}"),
            }
        }
    }

    Ok(())
}

fn build_graph(
    input: &Path,
    languages: &[String],
    jobs: Option<usize>,
    verbose: bool,
) -> Result<Graph, Box<dyn std::error::Error>> {
    let started = Instant::now();
    let root = fs::canonicalize(input)?;

    let mut paths = scan::collect_files(&root);
    paths.sort();
    if verbose {
        eprintln!(
            "[verbose] {} arquivos encontrados em {:?}",
            paths.len(),
            started.elapsed()
        );
    }

    // Parse paralelo; `collect` preserva a ordem de entrada, o merge final ordena.
    let process = || -> Vec<(Option<FileOutput>, Option<Warning>)> {
        paths
            .par_iter()
            .map(|path| process_file(path, &root, languages))
            .collect()
    };

    let results = match jobs {
        Some(threads) if threads > 0 => rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()?
            .install(process),
        _ => process(),
    };

    let mut files = Vec::new();
    let mut warnings = Vec::new();
    let mut symbols = Vec::new();
    let mut raw_imports = Vec::new();
    let mut entry_points = Vec::new();
    let mut raw_script_imports = Vec::new();

    for (output, warning) in results {
        if let Some(warning) = warning {
            warnings.push(warning);
        }
        if let Some(output) = output {
            files.push(output.entry);
            symbols.extend(output.symbols);
            raw_imports.extend(output.imports);
            entry_points.extend(output.entry_points);
            raw_script_imports.extend(output.script_imports);
        }
    }

    files.sort_by(|a, b| a.path.cmp(&b.path));
    symbols.sort_by(|a, b| (&a.id, a.line).cmp(&(&b.id, b.line)));
    warnings.sort_by(|a, b| {
        (a.path.as_deref().unwrap_or(""), a.message.as_str())
            .cmp(&(b.path.as_deref().unwrap_or(""), b.message.as_str()))
    });

    let edges = resolve::resolve_imports(&files, &raw_imports);
    let metrics = analyze::compute_metrics(&files, &edges);
    entrypoints::resolve_script_imports(&files, &raw_script_imports, &mut entry_points);
    let entry_points = entrypoints::dedupe(entry_points);

    let mut repo_languages: Vec<String> = files.iter().map(|f| f.language.clone()).collect();
    repo_languages.sort();
    repo_languages.dedup();

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

    if verbose {
        eprintln!(
            "[verbose] {} arquivos, {} simbolos, {} edges, {} warnings em {:?}",
            files.len(),
            symbols.len(),
            edges.len(),
            warnings.len(),
            started.elapsed()
        );
    }

    Ok(Graph {
        schema_version: "1.0".to_string(),
        root: root_display,
        repo_hash,
        languages: repo_languages,
        files,
        warnings,
        symbols,
        edges,
        metrics,
        entry_points,
    })
}

// Processa um arquivo isolado (roda em paralelo). Nunca aborta o run:
// erro de leitura/parse vira warning e o arquivo entra (se legível).
fn process_file(
    path: &Path,
    root: &Path,
    languages: &[String],
) -> (Option<FileOutput>, Option<Warning>) {
    let Ok(rel) = path.strip_prefix(root) else {
        return (None, None);
    };
    let rel = rel.to_string_lossy().replace('\\', "/");

    let language = language_of(path);
    if !languages.is_empty() && !languages.iter().any(|wanted| wanted == language) {
        return (None, None);
    }

    let bytes = match fs::read(path) {
        Ok(bytes) => bytes,
        Err(err) => {
            return (
                None,
                Some(Warning {
                    message: err.to_string(),
                    path: Some(rel),
                }),
            )
        }
    };

    let mut symbols = Vec::new();
    let mut raw_imports = Vec::new();
    let mut warning = None;

    if matches!(language, "python" | "javascript" | "typescript") {
        match parse::parse_file(&rel, &bytes, language) {
            Ok(ParsedFile {
                symbols: parsed_symbols,
                imports,
            }) => {
                symbols = parsed_symbols;
                raw_imports = imports;
            }
            Err(message) => {
                // Tolerante a falha: registra aviso, mas ainda emite o arquivo.
                warning = Some(Warning {
                    message,
                    path: Some(rel.clone()),
                });
            }
        }
    }

    let mut entry_points = Vec::new();
    let mut script_imports = Vec::new();
    entrypoints::detect(&rel, &bytes, &mut entry_points, &mut script_imports);

    let entry = FileEntry {
        path: rel,
        language: language.to_string(),
        loc: count_lines(&bytes),
        hash: sha256_hex(&bytes),
        parse_errors: Vec::new(),
    };

    (
        Some(FileOutput {
            entry,
            symbols,
            imports: raw_imports,
            entry_points,
            script_imports,
        }),
        warning,
    )
}

fn language_of(path: &Path) -> &'static str {
    match path.extension().and_then(|ext| ext.to_str()) {
        Some("py") => "python",
        Some("js") | Some("jsx") | Some("mjs") | Some("cjs") => "javascript",
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
