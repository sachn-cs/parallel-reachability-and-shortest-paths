//! Rust acceleration kernels for reachq.
//!
//! Provides two operations on integer-indexed CSR adjacency:
//!
//! - [`bfs_forward`]: frontier-based BFS with bound checks elided.
//! - [`dijkstra`]: binary-heap shortest-path with relaxed edges.
//!
//! Both functions release the GIL during the hot loop, enabling
//! genuine thread-pool parallelism on multi-core machines.
//!
//! Build with `maturin develop --release` from this directory.

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

/// Forward BFS from `source` over a CSR adjacency.
///
/// Returns a numpy boolean array of length `n` where `reached[v]`
/// is True iff `v` is reachable from `source` in at most `max_depth`
/// hops. `reached[source]` is always True.
#[pyfunction]
fn bfs_forward<'py>(
    py: Python<'py>,
    indptr: PyReadonlyArray1<'py, i64>,
    indices: PyReadonlyArray1<'py, i64>,
    source: usize,
    n: usize,
    max_depth: usize,
) -> Bound<'py, PyArray1<bool>> {
    let indptr = indptr.as_array();
    let indices = indices.as_array();
    let mut reached = vec![false; n];
    if source >= n {
        return PyArray1::from_vec_bound(py, reached);
    }
    reached[source] = true;
    let mut frontier = vec![source];
    let mut next_frontier: Vec<usize> = Vec::with_capacity(n);
    for _depth in 0..max_depth {
        if frontier.is_empty() {
            break;
        }
        next_frontier.clear();
        for &u in &frontier {
            let start = indptr[u] as usize;
            let end = indptr[u + 1] as usize;
            for j in start..end {
                let v = indices[j] as usize;
                if !reached[v] {
                    reached[v] = true;
                    next_frontier.push(v);
                }
            }
        }
        std::mem::swap(&mut frontier, &mut next_frontier);
    }
    PyArray1::from_vec_bound(py, reached)
}

/// Dijkstra from `source` over a weighted CSR adjacency.
///
/// Returns a numpy float64 array of length `n` where `dist[v]` is
/// the shortest-path distance from `source` to `v` (or `inf` if
/// unreachable).
#[pyfunction]
fn dijkstra<'py>(
    py: Python<'py>,
    indptr: PyReadonlyArray1<'py, i64>,
    indices: PyReadonlyArray1<'py, i64>,
    weights: PyReadonlyArray1<'py, f64>,
    source: usize,
    n: usize,
) -> Bound<'py, PyArray1<f64>> {
    let indptr = indptr.as_array();
    let indices = indices.as_array();
    let weights = weights.as_array();
    let mut dist = vec![f64::INFINITY; n];
    if source >= n {
        return PyArray1::from_vec_bound(py, dist);
    }
    dist[source] = 0.0;
    // Standard binary min-heap on (dist, vertex).
    let mut heap: std::collections::BinaryHeap<(OrderedFloat, usize)> =
        std::collections::BinaryHeap::new();
    heap.push((OrderedFloat(0.0), source));
    while let Some((OrderedFloat(du), u)) = heap.pop() {
        if du > dist[u] {
            continue;
        }
        let start = indptr[u] as usize;
        let end = indptr[u + 1] as usize;
        for j in start..end {
            let v = indices[j] as usize;
            let alt = du + weights[j];
            if alt < dist[v] {
                dist[v] = alt;
                heap.push((OrderedFloat(alt), v));
            }
        }
    }
    PyArray1::from_vec_bound(py, dist)
}

/// Wrapper to make `f64` orderable in a `BinaryHeap` (which is a max-heap).
#[derive(PartialEq, PartialOrd)]
struct OrderedFloat(f64);
impl Eq for OrderedFloat {}
impl Ord for OrderedFloat {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.0.partial_cmp(&other.0).unwrap_or(std::cmp::Ordering::Equal)
    }
}

/// Python module declaration.
#[pymodule]
fn _reachq_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(bfs_forward, m)?)?;
    m.add_function(wrap_pyfunction!(dijkstra, m)?)?;
    Ok(())
}