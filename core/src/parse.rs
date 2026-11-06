use tree_sitter::{Node, Parser};

use crate::models::Symbol;

pub fn new_parser() -> Result<Parser, tree_sitter::LanguageError> {
    let mut parser = Parser::new();
    parser.set_language(&tree_sitter_python::LANGUAGE.into())?;
    Ok(parser)
}

pub fn parse_python(
    file: &str,
    bytes: &[u8],
    parser: &mut Parser,
) -> Result<Vec<Symbol>, String> {
    let tree = parser
        .parse(bytes, None)
        .ok_or_else(|| "parser nao retornou arvore".to_string())?;

    let root = tree.root_node();
    if root.has_error() {
        return Err("erro de sintaxe no arquivo".to_string());
    }

    let mut symbols = Vec::new();

    let mut cursor = root.walk();
    for child in root.named_children(&mut cursor) {
        let child = unwrap_decorated(child);
        match child.kind() {
            "function_definition" => {
                push_symbol(&mut symbols, file, bytes, child, "function", None);
            }
            "class_definition" => {
                let Some(name_node) = child.child_by_field_name("name") else {
                    continue;
                };
                let class_name = text(name_node, bytes);
                push_symbol(&mut symbols, file, bytes, child, "class", None);

                let Some(body) = child.child_by_field_name("body") else {
                    continue;
                };
                let mut body_cursor = body.walk();
                for item in body.named_children(&mut body_cursor) {
                    let item = unwrap_decorated(item);
                    if item.kind() == "function_definition" {
                        push_symbol(
                            &mut symbols,
                            file,
                            bytes,
                            item,
                            "method",
                            Some(&class_name),
                        );
                    }
                }
            }
            _ => {}
        }
    }

    symbols.sort_by(|a, b| (&a.id, a.line).cmp(&(&b.id, b.line)));
    Ok(symbols)
}

fn push_symbol(
    out: &mut Vec<Symbol>,
    file: &str,
    bytes: &[u8],
    node: Node<'_>,
    kind: &str,
    parent: Option<&str>,
) {
    let Some(name_node) = node.child_by_field_name("name") else {
        return;
    };
    let name = text(name_node, bytes);
    if name.is_empty() {
        return;
    }

    let id = match parent {
        Some(parent) => format!("{file}::{parent}.{name}"),
        None => format!("{file}::{name}"),
    };

    out.push(Symbol {
        id,
        file: file.to_string(),
        name: name.clone(),
        kind: kind.to_string(),
        line: node.start_position().row + 1,
        exported: !name.starts_with('_'),
    });
}

fn text(node: Node<'_>, bytes: &[u8]) -> String {
    node.utf8_text(bytes).unwrap_or("").to_string()
}

fn unwrap_decorated(node: Node<'_>) -> Node<'_> {
    if node.kind() == "decorated_definition" {
        node.child_by_field_name("definition").unwrap_or(node)
    } else {
        node
    }
}
