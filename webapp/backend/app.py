"""
Flask Backend for Invariant Subset Analyzer
============================================
Provides API endpoints and generates pyvis graph visualizations.
Based on robustness-analyzer structure.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pyvis.network import Network
from collections import deque
from bs4 import BeautifulSoup
import json
import os
import tempfile

app = Flask(__name__)
CORS(app)

# Store generated HTML files
GRAPH_DIR = tempfile.mkdtemp()

# Background color matching robustness-analyzer
BACKGROUND_COLOR = "#E8E8E8"

# ============================================================================
# Core Algorithm Functions
# ============================================================================

def build_reverse_graph(graph):
    reverse = {}
    for node in graph:
        if node not in reverse:
            reverse[node] = []
        for child in graph[node]:
            if child not in reverse:
                reverse[child] = []
    for node, children in graph.items():
        for child in children:
            reverse[child].append(node)
    return reverse


def get_all_nodes(graph):
    nodes = set(graph.keys())
    for children in graph.values():
        nodes.update(children)
    return nodes


def find_nodes_reaching_target(graph, target):
    reverse_graph = build_reverse_graph(graph)
    reachable = set()
    queue = deque([target])
    reachable.add(target)
    while queue:
        node = queue.popleft()
        for parent in reverse_graph.get(node, []):
            if parent not in reachable:
                reachable.add(parent)
                queue.append(parent)
    return reachable


def find_invariant_subset(graph, target, edge_to_remove):
    source, dest = edge_to_remove
    modified_graph = {}
    for node, children in graph.items():
        if node == source:
            modified_graph[node] = [c for c in children if c != dest]
        else:
            modified_graph[node] = children.copy()
    
    all_nodes = get_all_nodes(graph)
    for node in all_nodes:
        if node not in modified_graph:
            modified_graph[node] = []
    
    reachable = find_nodes_reaching_target(modified_graph, target)
    return all_nodes - reachable


def find_all_invariant_subsets(graph, target):
    results = {}
    for source, children in graph.items():
        for dest in children:
            edge = (source, dest)
            invariant = find_invariant_subset(graph, target, edge)
            results[edge] = invariant
    return results


def compute_reachability_layers(graph, target):
    reverse_graph = build_reverse_graph(graph)
    all_nodes = get_all_nodes(graph)
    layers = {node: -1 for node in all_nodes}
    layers[target] = 0
    queue = deque([target])
    while queue:
        node = queue.popleft()
        current_layer = layers[node]
        for parent in reverse_graph.get(node, []):
            if layers[parent] == -1:
                layers[parent] = current_layer + 1
                queue.append(parent)
    return layers


def find_unreachable_subsets(graph, target):
    """
    Find all nodes that cannot reach the target.
    Returns a list of connected components (invariant subsets) that cannot reach target.
    """
    all_nodes = get_all_nodes(graph)
    reachable = find_nodes_reaching_target(graph, target)
    unreachable = all_nodes - reachable
    
    if not unreachable:
        return []
    
    # Find connected components within unreachable nodes
    # Build subgraph of unreachable nodes (considering both directions for connectivity)
    visited = set()
    components = []
    
    for start_node in unreachable:
        if start_node in visited:
            continue
        
        # BFS to find connected component (undirected connectivity)
        component = set()
        queue = deque([start_node])
        component.add(start_node)
        
        while queue:
            node = queue.popleft()
            # Check outgoing edges
            for neighbor in graph.get(node, []):
                if neighbor in unreachable and neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
            # Check incoming edges (reverse graph)
            for other_node, children in graph.items():
                if other_node in unreachable and node in children and other_node not in component:
                    component.add(other_node)
                    queue.append(other_node)
        
        visited.update(component)
        components.append(sorted(list(component)))
    
    return components


def find_scc_tarjan(graph, nodes_subset):
    """
    Find strongly connected components using Tarjan's algorithm.
    Only considers nodes in nodes_subset.
    """
    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    on_stack = {}
    sccs = []
    
    def strongconnect(node):
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack[node] = True
        
        for neighbor in graph.get(node, []):
            if neighbor not in nodes_subset:
                continue
            if neighbor not in index:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif on_stack.get(neighbor, False):
                lowlinks[node] = min(lowlinks[node], index[neighbor])
        
        if lowlinks[node] == index[node]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == node:
                    break
            if len(scc) > 1 or (len(scc) == 1 and scc[0] in graph.get(scc[0], [])):
                # Only include if it's a real SCC (more than one node or self-loop)
                sccs.append(sorted(scc))
            elif len(scc) == 1:
                # Single node without self-loop - still an attractor if no outgoing edges to reachable nodes
                sccs.append(sorted(scc))
    
    for node in nodes_subset:
        if node not in index:
            strongconnect(node)
    
    return sccs


def find_attractors_in_subset(graph, subset, all_reachable):
    """
    Find attractor nodes in an unreachable subset.
    An attractor is a node/SCC that has no outgoing edges to reachable nodes.
    For recovery, we need to add an edge from an attractor to a reachable node.
    """
    subset_set = set(subset)
    
    # Find SCCs in the subset
    sccs = find_scc_tarjan(graph, subset_set)
    
    # Find attractors (SCCs with no outgoing edges to other nodes)
    attractors = []
    for scc in sccs:
        scc_set = set(scc)
        has_external_edge = False
        for node in scc:
            for neighbor in graph.get(node, []):
                if neighbor not in scc_set:
                    has_external_edge = True
                    break
            if has_external_edge:
                break
        
        if not has_external_edge:
            # This SCC is an attractor (bottom SCC)
            attractors.append(scc)
    
    # If no true attractors found, take all single nodes as potential attractors
    if not attractors:
        for node in subset:
            outgoing = [n for n in graph.get(node, []) if n in subset_set]
            if not outgoing:
                attractors.append([node])
    
    # If still no attractors, just use all nodes in subset
    if not attractors:
        attractors = [[n] for n in subset]
    
    return attractors


def compute_recovery_plan(graph, target):
    """
    Compute minimal recovery plan for an infeasible network.
    For each unreachable subset, find an attractor and suggest adding an edge
    from a node in the attractor to a random reachable node (not target itself).
    """
    import random
    
    all_nodes = get_all_nodes(graph)
    reachable = find_nodes_reaching_target(graph, target)
    unreachable_subsets = find_unreachable_subsets(graph, target)
    
    recovery_edges = []
    
    for subset in unreachable_subsets:
        # Find attractors in this subset
        attractors = find_attractors_in_subset(graph, subset, reachable)
        
        if attractors:
            # Pick the first attractor
            attractor = attractors[0]
            # Pick a node from the attractor
            source_node = attractor[0]
            
            # Find a reachable node to connect to (exclude target itself if possible)
            reachable_non_target = [n for n in reachable if n != target]
            
            if reachable_non_target:
                # Randomly pick from non-target reachable nodes
                dest_node = random.choice(reachable_non_target)
            elif reachable:
                # If only target is reachable, use target
                dest_node = target
            else:
                continue
                
            recovery_edges.append({
                'source': source_node,
                'dest': dest_node,
                'subset': subset,
                'attractor': attractor
            })
    
    return {
        'unreachable_subsets': unreachable_subsets,
        'recovery_edges': recovery_edges,
        'total_unreachable': sum(len(s) for s in unreachable_subsets)
    }


# ============================================================================
# PyVis Graph Generation
# ============================================================================

def create_visualize_graph(graph, target):
    """Create visualization graph with blue gradient (lighter = closer to target)."""
    net = Network(
        height="100%",
        width="100%",
        bgcolor=BACKGROUND_COLOR,
        directed=True
    )
    
    # Force-directed layout
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.005,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4
            },
            "stabilization": {
                "enabled": true,
                "iterations": 200
            }
        },
        "edges": {
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.1
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
        }
    }
    """)
    
    all_nodes = get_all_nodes(graph)
    layers = compute_reachability_layers(graph, target)
    max_layer = max(l for l in layers.values() if l >= 0) if any(l >= 0 for l in layers.values()) else 1
    
    # Add nodes with BLUE gradient (lighter = closer to target)
    for node in all_nodes:
        layer = layers.get(node, -1)
        if node == target:
            # Target node is RED
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                font={"size": 20, "color": "red", "align": "center"}
            )
        else:
            # Blue gradient: layer 0 = lightest, higher layer = darker
            if layer >= 0 and max_layer > 0:
                # Interpolate from light blue (#93c5fd) to dark blue (#1e3a8a)
                ratio = layer / max_layer
                # Light to dark blue gradient
                r = int(147 - ratio * (147 - 30))
                g = int(197 - ratio * (197 - 58))
                b = int(253 - ratio * (253 - 138))
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#6b7280"  # Gray for unreachable
            
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color=color,
                font={"size": 20, "color": "black", "align": "center"}
            )
    
    # Add edges - black
    for source, children in graph.items():
        for dest in children:
            net.add_edge(source, dest, font={"color": "black", "size": 20})
    
    return net


def create_analyze_graph(graph, target, results):
    """Create hierarchical analysis graph with red critical edges."""
    net = Network(
        height="100%",
        width="100%",
        bgcolor=BACKGROUND_COLOR,
        directed=True
    )
    
    # Hierarchical layout (left to right)
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "LR",
                "sortMethod": "directed",
                "levelSeparation": 150,
                "nodeSpacing": 120
            }
        },
        "physics": {
            "enabled": true
        },
        "edges": {
            "smooth": {
                "type": "curvedCW"
            }
        }
    }
    """)
    
    all_nodes = get_all_nodes(graph)
    layers = compute_reachability_layers(graph, target)
    n = len(all_nodes)
    
    # Add nodes
    for node in all_nodes:
        layer = layers.get(node, -1)
        if node == target:
            # Target node is RED
            net.add_node(
                node,
                label=str(node),
                shape="circle",
                size=30,
                font={"size": 20, "color": "red", "align": "center"},
                level=0
            )
        else:
            net.add_node(
                node,
                label=str(node),
                shape="circle",
                size=30,
                font={"size": 20, "color": "black", "align": "center"},
                level=int(layer) if layer >= 0 else max(layers.values()) + 1
            )
    
    # Add edges with analysis results
    for source, children in graph.items():
        for dest in children:
            edge = (source, dest)
            if edge in results:
                inv_set = results[edge]
                if inv_set:
                    # Critical edge - RED with ρ(i,j) label
                    robustness = 1 - len(inv_set) / (n - 1) if n > 1 else 1.0
                    net.add_edge(
                        source, dest,
                        label=f"inx={robustness:.3f}",
                        font={"color": "red", "size": 14},
                        color="red",
                        width=2
                    )
                else:
                    # Safe edge - no label
                    net.add_edge(source, dest, font={"color": "black", "size": 14})
            else:
                net.add_edge(source, dest, font={"color": "black", "size": 14})
    
    return net


# Color palette for different invariant subsets
SUBSET_COLORS = [
    "#ef4444",  # Red
    "#f97316",  # Orange
    "#eab308",  # Yellow
    "#22c55e",  # Green
    "#06b6d4",  # Cyan
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#6366f1",  # Indigo
]


def get_shuffled_colors(n_subsets):
    """Get a shuffled list of colors for subsets."""
    import random
    colors = SUBSET_COLORS.copy()
    # If we need more colors than available, extend with variations
    while len(colors) < n_subsets:
        colors.extend(SUBSET_COLORS)
    random.shuffle(colors)
    return colors[:n_subsets] if n_subsets > 0 else colors


def create_infeasible_graph(graph, target, unreachable_subsets):
    """Create visualization graph for infeasible network with colored invariant subsets."""
    net = Network(
        height="100%",
        width="100%",
        bgcolor=BACKGROUND_COLOR,
        directed=True
    )
    
    # Force-directed layout
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.005,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4
            },
            "stabilization": {
                "enabled": true,
                "iterations": 200
            }
        },
        "edges": {
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.1
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
        }
    }
    """)
    
    all_nodes = get_all_nodes(graph)
    reachable = find_nodes_reaching_target(graph, target)
    
    # Get shuffled colors for subsets
    subset_colors = get_shuffled_colors(len(unreachable_subsets))
    
    # Create node to subset mapping
    node_to_subset = {}
    for idx, subset in enumerate(unreachable_subsets):
        for node in subset:
            node_to_subset[node] = idx
    
    # Add nodes
    for node in all_nodes:
        if node == target:
            # Target node - RED with special styling
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color="#dc2626",
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Target Node {node}"
            )
        elif node in reachable:
            # Reachable nodes - Blue
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color="#3b82f6",
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Node {node} (Reachable)"
            )
        else:
            # Unreachable nodes - colored by subset
            subset_idx = node_to_subset.get(node, 0)
            color = subset_colors[subset_idx] if subset_idx < len(subset_colors) else SUBSET_COLORS[0]
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color=color,
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Node {node} (Invariant Subset {subset_idx + 1})"
            )
    
    # Add edges - black for existing edges
    for source, children in graph.items():
        for dest in children:
            net.add_edge(source, dest, color="#374151", font={"color": "black", "size": 20})
    
    return net


def create_recovery_graph(graph, target, recovery_plan, subset_colors=None):
    """Create visualization graph showing recovery edges."""
    net = Network(
        height="100%",
        width="100%",
        bgcolor=BACKGROUND_COLOR,
        directed=True
    )
    
    # Force-directed layout
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.005,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4
            },
            "stabilization": {
                "enabled": true,
                "iterations": 200
            }
        },
        "edges": {
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.1
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
        }
    }
    """)
    
    all_nodes = get_all_nodes(graph)
    reachable = find_nodes_reaching_target(graph, target)
    unreachable_subsets = recovery_plan['unreachable_subsets']
    recovery_edges = recovery_plan['recovery_edges']
    
    # Get shuffled colors for subsets (or use provided)
    if subset_colors is None:
        subset_colors = get_shuffled_colors(len(unreachable_subsets))
    
    # Create node to subset mapping
    node_to_subset = {}
    for idx, subset in enumerate(unreachable_subsets):
        for node in subset:
            node_to_subset[node] = idx
    
    # Track attractor nodes
    attractor_nodes = set()
    for edge in recovery_edges:
        attractor_nodes.update(edge['attractor'])
    
    # Add nodes
    for node in all_nodes:
        if node == target:
            # Target node - RED with special styling
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color="#dc2626",
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Target Node {node}"
            )
        elif node in reachable:
            # Reachable nodes - Blue
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color="#3b82f6",
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Node {node} (Reachable)"
            )
        elif node in attractor_nodes:
            # Attractor nodes - highlighted with subtle border
            subset_idx = node_to_subset.get(node, 0)
            color = subset_colors[subset_idx] if subset_idx < len(subset_colors) else SUBSET_COLORS[0]
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=52,
                color={"background": color, "border": "#ffffff"},
                borderWidth=2,
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Node {node} (Attractor in Subset {subset_idx + 1})"
            )
        else:
            # Unreachable nodes - colored by subset
            subset_idx = node_to_subset.get(node, 0)
            color = subset_colors[subset_idx] if subset_idx < len(subset_colors) else SUBSET_COLORS[0]
            net.add_node(
                node,
                label=f" {node} ",
                shape="circle",
                size=50,
                color=color,
                font={"size": 20, "color": "white", "align": "center"},
                title=f"Node {node} (Invariant Subset {subset_idx + 1})"
            )
    
    # Add existing edges - dark gray
    for source, children in graph.items():
        for dest in children:
            net.add_edge(source, dest, color="#374151", font={"color": "black", "size": 20})
    
    # Add recovery edges - RED with dashed style
    for edge in recovery_edges:
        net.add_edge(
            edge['source'],
            edge['dest'],
            color="#ef4444",
            width=4,
            dashes=True,
            label="Recovery",
            font={"color": "#ef4444", "size": 14, "strokeWidth": 0},
            title=f"Recovery edge: {edge['source']} → {edge['dest']}"
        )
    
    return net


def clean_pyvis_html(filepath):
    """Clean up pyvis HTML for embedding in iframe."""
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Add background color and hide scrollbar
    html_tag = soup.find("html")
    if html_tag:
        html_tag["style"] = f"scrollbar-width: none; background-color: {BACKGROUND_COLOR}; height: 100%;"
    
    # Add comprehensive CSS for full-height graph
    additional_css = """
    html, body { 
        height: 100%; 
        margin: 0; 
        padding: 0; 
        overflow: hidden;
        scrollbar-width: none;
    }
    body::-webkit-scrollbar { display: none; }
    h1 { display: none !important; }
    .card { 
        border: none !important; 
        height: 100% !important;
        margin: 0 !important;
    }
    .card-body { 
        padding: 0 !important; 
        height: 100% !important;
    }
    #mynetwork { 
        border: none !important; 
        padding: 0 !important;
        width: 100% !important;
        height: 100% !important;
    }
    """
    
    head_tag = soup.find("head")
    if head_tag:
        style_tag = soup.new_tag("style")
        style_tag.string = additional_css
        head_tag.append(style_tag)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(soup))
    
    return filepath


# ============================================================================
# API Endpoints
# ============================================================================

def check_feasibility(graph, target):
    """
    Check if the MDP is feasible:
    1. All nodes can reach the target node
    2. Target node has no outgoing edges
    """
    all_nodes = get_all_nodes(graph)
    
    # Check if target has no outgoing edges
    target_outgoing = graph.get(target, [])
    if len(target_outgoing) > 0:
        return False
    
    # Check if all nodes can reach target
    reachable = find_nodes_reaching_target(graph, target)
    if reachable != all_nodes:
        return False
    
    return True


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze the graph and return results."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        # Parse graph - convert string keys to int
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        # Get all nodes
        all_nodes = get_all_nodes(graph)
        n = len(all_nodes)
        
        # Check feasibility
        feasible = check_feasibility(graph, target)
        
        # Compute invariant subsets
        results = find_all_invariant_subsets(graph, target)
        
        # Compute layers
        layers = compute_reachability_layers(graph, target)
        
        # Format results for JSON
        formatted_results = []
        for edge, inv_set in sorted(results.items(), key=lambda x: (-len(x[1]), x[0])):
            robustness = 1 - len(inv_set) / (n - 1) if inv_set else 1.0
            formatted_results.append({
                'edge': list(edge),
                'invariant_subset': sorted(list(inv_set)),
                'robustness': robustness,
                'size': len(inv_set)
            })
        
        # Format layers
        layers_by_level = {}
        for node, layer in layers.items():
            if layer not in layers_by_level:
                layers_by_level[layer] = []
            layers_by_level[layer].append(node)
        
        return jsonify({
            'success': True,
            'feasible': feasible,
            'results': formatted_results,
            'node_count': n,
            'edge_count': sum(len(v) for v in graph.values()),
            'layers': {int(k): sorted(v) for k, v in layers_by_level.items()},
            'target': target
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/graph/visualize', methods=['POST'])
def get_visualize_graph():
    """Generate visualization graph with blue gradient colors."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        net = create_visualize_graph(graph, target)
        
        filepath = os.path.join(GRAPH_DIR, 'visualize.html')
        net.save_graph(filepath)
        clean_pyvis_html(filepath)
        
        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=True,
            download_name='network_visualization.html'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/graph/analyze', methods=['POST'])
def get_analyze_graph():
    """Generate hierarchical analysis graph with red critical edges."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        results = find_all_invariant_subsets(graph, target)
        net = create_analyze_graph(graph, target, results)
        
        filepath = os.path.join(GRAPH_DIR, 'analyze.html')
        net.save_graph(filepath)
        clean_pyvis_html(filepath)
        
        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=True,
            download_name='hierarchical_analysis.html'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/default-graph', methods=['GET'])
def get_default_graph():
    """Return the default example graph."""
    default_graph = {
        0: [],
        1: [0],
        2: [0],
        3: [0],
        4: [1, 2],
        5: [2, 3],
        6: [1],
        7: [3],
        8: [4, 6],
        9: [4, 5],
        10: [5, 7],
        11: [8],
        12: [8, 9],
        13: [9, 10],
        14: [10],
        15: [11],
        16: [11, 12],
        17: [12, 13],
        18: [13, 14],
        19: [14],
        20: [15],
        21: [15, 16],
        22: [17],
        23: [18, 19],
        24: [19],
        25: [20, 21],
        26: [20],
        27: [22, 23],
        28: [24],
        29: [26, 25]
    }
    return jsonify({
        'graph': default_graph,
        'target': 0
    })


@app.route('/api/check-feasibility', methods=['POST'])
def check_feasibility_api():
    """Check feasibility and return basic stats (for Visualize button)."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        all_nodes = get_all_nodes(graph)
        feasible = check_feasibility(graph, target)
        
        # Get basic stats
        node_count = len(all_nodes)
        edge_count = sum(len(v) for v in graph.values())
        
        result = {
            'success': True,
            'feasible': feasible,
            'node_count': node_count,
            'edge_count': edge_count,
            'target': target
        }
        
        # If not feasible, include unreachable subsets info
        if not feasible:
            unreachable_subsets = find_unreachable_subsets(graph, target)
            result['unreachable_subsets'] = unreachable_subsets
            result['unreachable_count'] = sum(len(s) for s in unreachable_subsets)
            result['subset_count'] = len(unreachable_subsets)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/recovery', methods=['POST'])
def get_recovery():
    """Compute and return recovery plan for infeasible network."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        recovery_plan = compute_recovery_plan(graph, target)
        
        # Format for JSON
        formatted_edges = []
        for edge in recovery_plan['recovery_edges']:
            formatted_edges.append({
                'source': edge['source'],
                'dest': edge['dest'],
                'subset': edge['subset'],
                'attractor': edge['attractor']
            })
        
        return jsonify({
            'success': True,
            'unreachable_subsets': recovery_plan['unreachable_subsets'],
            'recovery_edges': formatted_edges,
            'total_unreachable': recovery_plan['total_unreachable'],
            'edges_needed': len(formatted_edges)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/graph/infeasible', methods=['POST'])
def get_infeasible_graph():
    """Generate visualization for infeasible network with colored subsets."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        unreachable_subsets = find_unreachable_subsets(graph, target)
        net = create_infeasible_graph(graph, target, unreachable_subsets)
        
        filepath = os.path.join(GRAPH_DIR, 'infeasible.html')
        net.save_graph(filepath)
        clean_pyvis_html(filepath)
        
        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=True,
            download_name='infeasible_network.html'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/graph/recovery', methods=['POST'])
def get_recovery_graph():
    """Generate visualization for recovery plan with red recovery edges."""
    try:
        data = request.json
        graph_str = data.get('graph', '{}')
        target = int(data.get('target', 0))
        
        graph_raw = json.loads(graph_str) if isinstance(graph_str, str) else graph_str
        graph = {int(k): v for k, v in graph_raw.items()}
        
        recovery_plan = compute_recovery_plan(graph, target)
        net = create_recovery_graph(graph, target, recovery_plan)
        
        filepath = os.path.join(GRAPH_DIR, 'recovery.html')
        net.save_graph(filepath)
        clean_pyvis_html(filepath)
        
        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=True,
            download_name='recovery_network.html'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')

