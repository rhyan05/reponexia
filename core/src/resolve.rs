use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path};

use crate::models::{Edge, FileEntry};
use crate::parse::RawImport;

pub fn build_index(files: &[FileEntry]) -> BTreeMap<String, String> {
    let mut index = BTreeMap::new();

    for file in files {
        if file.language != "python" {
            continue;
        }
        let Some(stem) = file.path.strip_suffix(".py") else {
            continue;
        };
        let mut parts: Vec<&str> = stem.split('/').collect();
        if parts.last() == Some(&"__init__") {
            parts.pop();
        }
        if parts.is_empty() {
            continue;
        }
        for start in (0..parts.len()).rev() {
            let module = parts[start..].join(".");
            index.entry(module).or_insert_with(|| file.path.clone());
        }
    }

    index
}

fn resolve_one(
    index: &BTreeMap<String, String>,
    known: &BTreeSet<&str>,
    importer: &str,
    raw: &RawImport,
) -> Option<String> {
    if raw.level == 0 {
        return index.get(&raw.module).cloned();
    }

    let dir = importer.rsplit_once('/').map(|(d, _)| d).unwrap_or("");
    let mut parts: Vec<&str> = if dir.is_empty() {
        Vec::new()
    } else {
        dir.split('/').collect()
    };

    let up = raw.level.saturating_sub(1);
    if up > parts.len() {
        return None;
    }
    parts.truncate(parts.len() - up);

    if !raw.module.is_empty() {
        parts.extend(raw.module.split('.'));
    }

    let base = parts.join("/");
    if base.is_empty() {
        return None;
    }

    let file = format!("{base}.py");
    if known.contains(file.as_str()) {
        return Some(file);
    }

    let init = format!("{base}/__init__.py");
    if known.contains(init.as_str()) {
        return Some(init);
    }

    None
}

pub fn resolve_imports(files: &[FileEntry], imports: &[RawImport]) -> Vec<Edge> {
    let index = build_index(files);
    let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
    let languages: BTreeMap<&str, &str> = files
        .iter()
        .map(|file| (file.path.as_str(), file.language.as_str()))
        .collect();

    let mut edges = Vec::new();
    for raw in imports {
        let target = match languages.get(raw.file.as_str()) {
            Some(&lang) if lang == "javascript" || lang == "typescript" => {
                resolve_js(&raw.file, &raw.module, &known)
            }
            _ => resolve_one(&index, &known, &raw.file, raw),
        };
        let Some(to) = target else {
            continue;
        };
        if to == raw.file {
            continue;
        }
        edges.push(Edge {
            from: raw.file.clone(),
            to,
            kind: "import".to_string(),
            line: raw.line,
            symbol: if raw.module.is_empty() {
                None
            } else {
                Some(raw.module.clone())
            },
        });
    }

    edges.sort_by(|a, b| (&a.from, &a.to, a.line).cmp(&(&b.from, &b.to, b.line)));
    edges
}

// Resolve import relativo de JS/TS ("./x", "../core/y") para um arquivo do repo.
fn resolve_js(importer: &str, module: &str, known: &BTreeSet<&str>) -> Option<String> {
    if !(module.starts_with('.') || module.starts_with('/')) {
        return None; // pacote externo (npm)
    }

    let parent = Path::new(importer).parent().unwrap_or_else(|| Path::new(""));
    let base = normalize_path(&parent.join(module))?;

    let mut candidates = vec![base.clone()];
    for ext in [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"] {
        candidates.push(format!("{base}{ext}"));
    }
    for ext in [".ts", ".tsx", ".js", ".jsx"] {
        candidates.push(format!("{base}/index{ext}"));
    }

    candidates
        .into_iter()
        .find(|candidate| known.contains(candidate.as_str()))
}

fn normalize_path(path: &Path) -> Option<String> {
    let mut parts: Vec<String> = Vec::new();
    for component in path.components() {
        match component {
            Component::Normal(part) => parts.push(part.to_string_lossy().into_owned()),
            Component::ParentDir => {
                parts.pop()?;
            }
            Component::CurDir => {}
            Component::RootDir | Component::Prefix(_) => {}
        }
    }

    if parts.is_empty() {
        None
    } else {
        Some(parts.join("/"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entry(path: &str) -> FileEntry {
        FileEntry {
            path: path.to_string(),
            language: "python".to_string(),
            loc: 1,
            hash: String::new(),
            parse_errors: Vec::new(),
        }
    }

    #[test]
    fn registra_sufixos_do_layout_src() {
        let files = vec![entry("src/reponexia/core_runner.py")];
        let index = build_index(&files);
        assert_eq!(
            index.get("reponexia.core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
        assert_eq!(
            index.get("core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
        assert_eq!(
            index.get("src.reponexia.core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
    }

    #[test]
    fn registra_init_como_pacote() {
        let files = vec![entry("src/reponexia/__init__.py")];
        let index = build_index(&files);
        assert_eq!(
            index.get("reponexia").unwrap(),
            "src/reponexia/__init__.py"
        );
        assert!(index.get("__init__").is_none());
    }

    #[test]
    fn resolve_import_relativo() {
        let files = vec![entry("src/pkg/app.py"), entry("src/pkg/util.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/app.py".into(),
            module: "util".into(),
            level: 1,
            line: 3,
        };
        assert_eq!(
            resolve_one(&index, &known, &raw.file, &raw),
            Some("src/pkg/util.py".to_string())
        );
    }

    #[test]
    fn resolve_import_relativo_subindo() {
        let files = vec![entry("src/pkg/sub/app.py"), entry("src/pkg/util.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/sub/app.py".into(),
            module: "util".into(),
            level: 2,
            line: 3,
        };
        assert_eq!(
            resolve_one(&index, &known, &raw.file, &raw),
            Some("src/pkg/util.py".to_string())
        );
    }

    #[test]
    fn externo_nao_resolve() {
        let files = vec![entry("src/pkg/app.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/app.py".into(),
            module: "json".into(),
            level: 0,
            line: 1,
        };
        assert_eq!(resolve_one(&index, &known, &raw.file, &raw), None);
    }

    #[test]
    fn descarta_self_import() {
        let files = vec![entry("src/pkg/app.py")];
        let imports = vec![RawImport {
            file: "src/pkg/app.py".into(),
            module: "app".into(),
            level: 0,
            line: 1,
        }];
        assert!(resolve_imports(&files, &imports).is_empty());
    }

    fn script(path: &str, language: &str) -> FileEntry {
        FileEntry {
            path: path.to_string(),
            language: language.to_string(),
            loc: 1,
            hash: String::new(),
            parse_errors: Vec::new(),
        }
    }

    #[test]
    fn resolve_import_relativo_ts() {
        let files = vec![
            script("src/app/main.ts", "typescript"),
            script("src/app/util.ts", "typescript"),
        ];
        let imports = vec![RawImport {
            file: "src/app/main.ts".into(),
            module: "./util".into(),
            level: 0,
            line: 1,
        }];

        let edges = resolve_imports(&files, &imports);
        assert_eq!(edges.len(), 1);
        assert_eq!(edges[0].to, "src/app/util.ts");
    }

    #[test]
    fn resolve_import_subindo_js() {
        let files = vec![
            script("src/app/sub/main.ts", "typescript"),
            script("src/app/util.js", "javascript"),
        ];
        let imports = vec![RawImport {
            file: "src/app/sub/main.ts".into(),
            module: "../util".into(),
            level: 0,
            line: 1,
        }];

        let edges = resolve_imports(&files, &imports);
        assert_eq!(edges.len(), 1);
        assert_eq!(edges[0].to, "src/app/util.js");
    }

    #[test]
    fn pacote_npm_nao_resolve() {
        let files = vec![script("src/main.ts", "typescript")];
        let imports = vec![RawImport {
            file: "src/main.ts".into(),
            module: "react".into(),
            level: 0,
            line: 1,
        }];

        assert!(resolve_imports(&files, &imports).is_empty());
    }
}
