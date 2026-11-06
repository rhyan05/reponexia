use std::collections::{BTreeMap, BTreeSet};

use petgraph::Graph;
use petgraph::algo::page_rank;
use petgraph::graph::NodeIndex;

use crate::models::{Edge, FileEntry, Metric};

pub fn compute_metrics(files: &[FileEntry], edges: &[Edge]) -> Vec<Metric> {
    let mut graph: Graph<(), ()> = Graph::new();
    let mut nodes: BTreeMap<&str, NodeIndex> = BTreeMap::new();

    for file in files {
        let idx = graph.add_node(());
        nodes.insert(file.path.as_str(), idx);
    }

    let unique: BTreeSet<(&str, &str)> = edges
        .iter()
        .map(|edge| (edge.from.as_str(), edge.to.as_str()))
        .collect();

    for (from, to) in &unique {
        if let (Some(&a), Some(&b)) = (nodes.get(*from), nodes.get(*to)) {
            graph.add_edge(a, b, ());
        }
    }

    let ranks = page_rank(&graph, 0.85_f64, 100);

    let mut fan_in: BTreeMap<&str, usize> = BTreeMap::new();
    let mut fan_out: BTreeMap<&str, usize> = BTreeMap::new();
    for (from, to) in &unique {
        *fan_out.entry(*from).or_insert(0) += 1;
        *fan_in.entry(*to).or_insert(0) += 1;
    }

    let mut metrics: Vec<Metric> = files
        .iter()
        .map(|file| {
            let idx = nodes[file.path.as_str()];
            let rank = ranks[idx.index()];
            Metric {
                path: file.path.clone(),
                fan_in: *fan_in.get(file.path.as_str()).unwrap_or(&0),
                fan_out: *fan_out.get(file.path.as_str()).unwrap_or(&0),
                page_rank: (rank * 1_000_000.0).round() / 1_000_000.0,
            }
        })
        .collect();

    metrics.sort_by(|a, b| a.path.cmp(&b.path));
    metrics
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

    fn edge(from: &str, to: &str, line: usize) -> Edge {
        Edge {
            from: from.to_string(),
            to: to.to_string(),
            kind: "import".to_string(),
            line,
            symbol: None,
        }
    }

    fn metric<'a>(metrics: &'a [Metric], path: &str) -> &'a Metric {
        metrics.iter().find(|m| m.path == path).unwrap()
    }

    #[test]
    fn conta_vizinhos_distintos() {
        let files = vec![entry("a.py"), entry("b.py"), entry("c.py")];
        let edges = vec![
            edge("a.py", "b.py", 1),
            edge("a.py", "b.py", 2),
            edge("a.py", "c.py", 3),
            edge("b.py", "c.py", 4),
        ];

        let metrics = compute_metrics(&files, &edges);

        assert_eq!(metric(&metrics, "a.py").fan_out, 2);
        assert_eq!(metric(&metrics, "a.py").fan_in, 0);
        assert_eq!(metric(&metrics, "b.py").fan_in, 1);
        assert_eq!(metric(&metrics, "b.py").fan_out, 1);
        assert_eq!(metric(&metrics, "c.py").fan_in, 2);
        assert_eq!(metric(&metrics, "c.py").fan_out, 0);
    }

    #[test]
    fn page_rank_privilegia_arquivo_central() {
        let files = vec![entry("a.py"), entry("b.py"), entry("c.py")];
        let edges = vec![edge("a.py", "c.py", 1), edge("b.py", "c.py", 2)];

        let metrics = compute_metrics(&files, &edges);

        let central = metric(&metrics, "c.py").page_rank;
        assert!(central > metric(&metrics, "a.py").page_rank);

        let total: f64 = metrics.iter().map(|m| m.page_rank).sum();
        assert!((total - 1.0).abs() < 0.01, "soma={total}");
    }

    #[test]
    fn arquivo_sem_aresta_tem_fan_zero() {
        let files = vec![entry("a.py"), entry("b.py")];

        let metrics = compute_metrics(&files, &[]);

        assert_eq!(metrics.len(), 2);
        assert!(metrics.iter().all(|m| m.fan_in == 0 && m.fan_out == 0));
    }
}
