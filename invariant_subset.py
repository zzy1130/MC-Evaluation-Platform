"""
Invariant Subset Finder for Directed Networks

Given a directed network and a target (absorbing) node, this module finds the
invariant subset after removing an edge - i.e., the set of nodes that cannot
reach the target node through any path after the edge removal.
"""

from collections import deque
from typing import Dict, List, Set, Tuple, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np


def build_reverse_graph(graph: Dict[int, List[int]]) -> Dict[int, List[int]]:
    """
    Build a reverse graph where edges point from children to parents.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
    
    Returns:
        Reverse adjacency list {node: [parent1, parent2, ...]}
    """
    reverse = {}
    
    # Initialize all nodes
    for node in graph:
        if node not in reverse:
            reverse[node] = []
        for child in graph[node]:
            if child not in reverse:
                reverse[child] = []
    
    # Add reverse edges
    for node, children in graph.items():
        for child in children:
            reverse[child].append(node)
    
    return reverse


def find_nodes_reaching_target(
    graph: Dict[int, List[int]], 
    target: int
) -> Set[int]:
    """
    Find all nodes that can reach the target node using BFS on reverse graph.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
        target: The target/absorbing node
    
    Returns:
        Set of nodes that can reach the target
    """
    reverse_graph = build_reverse_graph(graph)
    
    # BFS from target on reverse graph finds all nodes that can reach target
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


def get_all_nodes(graph: Dict[int, List[int]]) -> Set[int]:
    """Get all nodes in the graph."""
    nodes = set(graph.keys())
    for children in graph.values():
        nodes.update(children)
    return nodes


def find_invariant_subset(
    graph: Dict[int, List[int]], 
    target: int, 
    edge_to_remove: Tuple[int, int]
) -> Set[int]:
    """
    Find the invariant subset after removing an edge.
    
    The invariant subset contains all nodes that cannot reach the target node
    through any path after the specified edge is removed.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
               e.g., {0: [1, 4, 5], 1: [5, 3], ...}
        target: The target/absorbing node
        edge_to_remove: Tuple (source, destination) representing the edge to remove
    
    Returns:
        Set of nodes that cannot reach the target after edge removal
    
    Example:
        >>> graph = {0: [1, 2], 1: [2], 2: [3], 3: []}
        >>> target = 3
        >>> edge = (2, 3)
        >>> find_invariant_subset(graph, target, edge)
        {0, 1, 2}  # These nodes can no longer reach node 3
    """
    source, dest = edge_to_remove
    
    # Create a copy of the graph with the edge removed
    modified_graph = {}
    for node, children in graph.items():
        if node == source:
            # Remove the edge (source -> dest)
            modified_graph[node] = [c for c in children if c != dest]
        else:
            modified_graph[node] = children.copy()
    
    # Ensure all nodes from original graph are present
    all_nodes = get_all_nodes(graph)
    for node in all_nodes:
        if node not in modified_graph:
            modified_graph[node] = []
    
    # Find nodes that can still reach the target
    reachable = find_nodes_reaching_target(modified_graph, target)
    
    # Invariant subset = all nodes that cannot reach target
    invariant_subset = all_nodes - reachable
    
    return invariant_subset


def find_all_invariant_subsets(
    graph: Dict[int, List[int]], 
    target: int
) -> Dict[Tuple[int, int], Set[int]]:
    """
    Find invariant subsets for removing each edge in the graph.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
        target: The target/absorbing node
    
    Returns:
        Dictionary mapping each edge to its resulting invariant subset
    """
    results = {}
    
    for source, children in graph.items():
        for dest in children:
            edge = (source, dest)
            invariant = find_invariant_subset(graph, target, edge)
            results[edge] = invariant
    
    return results


def compute_reachability_layers(
    graph: Dict[int, List[int]], 
    target: int
) -> Dict[int, int]:
    """
    Compute the minimum distance (number of hops) from each node to the target.
    
    Uses BFS on the reverse graph starting from the target.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
        target: The target/absorbing node
    
    Returns:
        Dictionary mapping each node to its layer (distance to target).
        Nodes that cannot reach target will have layer = -1.
    """
    reverse_graph = build_reverse_graph(graph)
    all_nodes = get_all_nodes(graph)
    
    # BFS from target on reverse graph
    layers = {node: -1 for node in all_nodes}
    layers[target] = 0
    
    queue = deque([target])
    
    while queue:
        node = queue.popleft()
        current_layer = layers[node]
        for parent in reverse_graph.get(node, []):
            if layers[parent] == -1:  # Not yet visited
                layers[parent] = current_layer + 1
                queue.append(parent)
    
    return layers


def visualize_network(
    graph: Dict[int, List[int]], 
    target: int,
    title: str = "Directed Network with Target Node",
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None,
    highlight_edges: Optional[List[Tuple[int, int]]] = None,
    invariant_subset: Optional[Set[int]] = None
) -> None:
    """
    Visualize the directed network with the target node highlighted.
    
    Nodes are colored by their reachability layer (distance to target).
    The target node is shown in red.
    
    Args:
        graph: Adjacency list {node: [child1, child2, ...]}
        target: The target/absorbing node
        title: Title for the plot
        figsize: Figure size (width, height)
        save_path: If provided, save the figure to this path
        highlight_edges: Optional list of edges to highlight (e.g., removed edges)
        invariant_subset: Optional set of nodes to mark as invariant (cannot reach target)
    """
    # Create networkx DiGraph
    G = nx.DiGraph()
    
    # Add all nodes
    all_nodes = get_all_nodes(graph)
    G.add_nodes_from(all_nodes)
    
    # Add edges
    for node, children in graph.items():
        for child in children:
            G.add_edge(node, child)
    
    # Compute reachability layers
    layers = compute_reachability_layers(graph, target)
    max_layer = max(l for l in layers.values() if l >= 0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Use spring layout with seed for reproducibility
    # Adjust k parameter for spacing
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)
    
    # Color scheme - using a nice blue gradient for layers
    # Target node is red, unreachable nodes are gray
    cmap = plt.cm.Blues_r
    
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        if node == target:
            node_colors.append('#E74C3C')  # Red for target
            node_sizes.append(1200)
        elif invariant_subset and node in invariant_subset:
            node_colors.append('#95A5A6')  # Gray for invariant/unreachable
            node_sizes.append(900)
        elif layers[node] == -1:
            node_colors.append('#95A5A6')  # Gray for unreachable
            node_sizes.append(900)
        else:
            # Blue gradient based on layer
            intensity = 0.3 + 0.6 * (layers[node] / max(max_layer, 1))
            node_colors.append(cmap(intensity))
            node_sizes.append(900)
    
    # Draw edges with curved arrows
    edge_colors = []
    edge_widths = []
    
    for edge in G.edges():
        if highlight_edges and edge in highlight_edges:
            edge_colors.append('#E74C3C')  # Red for highlighted edges
            edge_widths.append(2.5)
        else:
            edge_colors.append('#2C3E50')  # Dark blue-gray
            edge_widths.append(1.5)
    
    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=edge_colors,
        width=edge_widths,
        arrows=True,
        arrowsize=20,
        arrowstyle='-|>',
        connectionstyle='arc3,rad=0.15',
        alpha=0.7,
        min_source_margin=15,
        min_target_margin=15
    )
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors='#2C3E50',
        linewidths=2
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=11,
        font_weight='bold',
        font_color='white'
    )
    
    # Create legend
    legend_elements = [
        mpatches.Patch(facecolor='#E74C3C', edgecolor='#2C3E50', 
                       linewidth=2, label=f'Target Node ({target})'),
        mpatches.Patch(facecolor=cmap(0.4), edgecolor='#2C3E50', 
                       linewidth=2, label='Transient Nodes (by layer)'),
    ]
    
    if invariant_subset:
        legend_elements.append(
            mpatches.Patch(facecolor='#95A5A6', edgecolor='#2C3E50', 
                          linewidth=2, label='Invariant Subset')
        )
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10,
              framealpha=0.9, edgecolor='#2C3E50')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        print(f"Figure saved to: {save_path}")
    
    plt.close(fig)


def visualize_network_hierarchical(
    graph: Dict[int, List[int]], 
    target: int,
    title: str = "Directed Network - Hierarchical Layout",
    figsize: Tuple[int, int] = (16, 12),
    save_path: Optional[str] = None,
    highlight_edges: Optional[List[Tuple[int, int]]] = None,
    invariant_subset: Optional[Set[int]] = None
) -> None:
    """
    Visualize the network with a hierarchical layout based on reachability layers.
    
    Nodes are arranged vertically by their distance to the target,
    with the target at the bottom.
    """
    # Create networkx DiGraph
    G = nx.DiGraph()
    all_nodes = get_all_nodes(graph)
    G.add_nodes_from(all_nodes)
    
    for node, children in graph.items():
        for child in children:
            G.add_edge(node, child)
    
    # Compute reachability layers
    layers = compute_reachability_layers(graph, target)
    max_layer = max(l for l in layers.values() if l >= 0)
    
    # Group nodes by layer
    nodes_by_layer = {}
    unreachable = []
    for node, layer in layers.items():
        if layer == -1:
            unreachable.append(node)
        else:
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = []
            nodes_by_layer[layer].append(node)
    
    # Create hierarchical positions
    pos = {}
    
    for layer, nodes in nodes_by_layer.items():
        nodes = sorted(nodes)
        n = len(nodes)
        # y position based on layer (target at bottom)
        y = -layer * 1.5
        # x positions spread evenly
        for i, node in enumerate(nodes):
            x = (i - (n - 1) / 2) * 1.8
            pos[node] = (x, y)
    
    # Place unreachable nodes at the top
    if unreachable:
        unreachable = sorted(unreachable)
        n = len(unreachable)
        y = -(max_layer + 2) * 1.5
        for i, node in enumerate(unreachable):
            x = (i - (n - 1) / 2) * 1.8
            pos[node] = (x, y)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Color scheme
    cmap = plt.cm.Blues_r
    
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        if node == target:
            node_colors.append('#E74C3C')  # Red for target
            node_sizes.append(1400)
        elif invariant_subset and node in invariant_subset:
            node_colors.append('#95A5A6')  # Gray
            node_sizes.append(1000)
        elif layers[node] == -1:
            node_colors.append('#95A5A6')  # Gray for unreachable
            node_sizes.append(1000)
        else:
            intensity = 0.3 + 0.5 * (layers[node] / max(max_layer, 1))
            node_colors.append(cmap(intensity))
            node_sizes.append(1000)
    
    # Edge styling
    edge_colors = []
    edge_widths = []
    
    for edge in G.edges():
        if highlight_edges and edge in highlight_edges:
            edge_colors.append('#E74C3C')
            edge_widths.append(2.5)
        else:
            edge_colors.append('#34495E')
            edge_widths.append(1.5)
    
    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=edge_colors,
        width=edge_widths,
        arrows=True,
        arrowsize=18,
        arrowstyle='-|>',
        connectionstyle='arc3,rad=0.1',
        alpha=0.7,
        min_source_margin=18,
        min_target_margin=18
    )
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors='#2C3E50',
        linewidths=2.5
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=12,
        font_weight='bold',
        font_color='white'
    )
    
    # Add layer annotations on the right side
    for layer in range(max_layer + 1):
        if layer in nodes_by_layer:
            y = -layer * 1.5
            max_x = max(pos[n][0] for n in nodes_by_layer[layer])
            ax.annotate(f'Layer {layer}', xy=(max_x + 1.5, y),
                       fontsize=10, color='#7F8C8D',
                       verticalalignment='center')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#E74C3C', edgecolor='#2C3E50', 
                       linewidth=2, label=f'Target/Absorbing Node (s_T = {target})'),
        mpatches.Patch(facecolor=cmap(0.5), edgecolor='#2C3E50', 
                       linewidth=2, label='Transient States'),
    ]
    
    if invariant_subset:
        legend_elements.append(
            mpatches.Patch(facecolor='#95A5A6', edgecolor='#2C3E50', 
                          linewidth=2, label='Invariant Subset (cannot reach target)')
        )
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11,
              framealpha=0.95, edgecolor='#2C3E50')
    
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        print(f"Figure saved to: {save_path}")
    
    plt.close(fig)


# Example usage and demonstration
if __name__ == "__main__":
    # Example network
    # 0 -> 1, 4, 5
    # 1 -> 5, 3
    # 2 -> 3
    # 3 -> 4 (target)
    # 4 -> (no outgoing)
    # 5 -> 4
    
    # ==========================================================================
    # 6-DOF Ultrasound Probe State Space (30 nodes, ~10 layers)
    # ==========================================================================
    # This network represents a simplified state space for ultrasound probe control
    # following the action space from Li et al.'s formulation:
    #   - Translations: ±5mm along local x and y axes
    #   - Rotations: ±5° about local x, y, z axes
    #
    # States are connected if they differ by exactly ONE action step.
    # Node 15 is the target state (sacrum position).
    #
    # The network has ~10 layers representing different distances to target.
    # ==========================================================================
    
    example_graph = {
        # Layer 0: TARGET
        15: [],                     # ★ TARGET NODE (absorbing state) ★
        
        # Layer 1: Direct connections to target (3 nodes)
        14: [15],                   # main approach
        20: [15],                   # secondary approach
        25: [15],                   # tertiary approach
        
        # Layer 2: Two steps from target (3 nodes)
        13: [14, 20],               # hub connecting to two L1 nodes
        19: [20, 25],               # hub
        24: [25],                   # single path
        
        # Layer 3: Three steps (4 nodes)
        8: [13, 14],                # branch point
        12: [13, 19],               # central
        18: [19, 24],               # right side
        23: [24],                   # edge path
        
        # Layer 4: Four steps (3 nodes)
        7: [8, 12],                 # hub
        11: [12, 18],               # connector
        17: [18, 23],               # right path
        
        # Layer 5: Five steps (3 nodes)
        2: [7, 8],                  # left branch
        6: [7, 11],                 # center-left
        10: [11, 17],               # center-right
        
        # Layer 6: Six steps (3 nodes)
        1: [2, 6],                  # hub
        5: [6, 10],                 # connector
        16: [17],                   # right edge (single path)
        
        # Layer 7: Seven steps (3 nodes)
        0: [1, 2],                  # far left
        4: [5, 6],                  # center
        9: [10, 16],                # right side
        
        # Layer 8: Eight steps (3 nodes)
        3: [4, 5],                  # connector
        22: [9, 16],                # right branch
        29: [23, 24],               # bottom path (connects back to L2-L3)
        
        # Layer 9: Nine steps (3 nodes)
        21: [22, 9],                # deep right
        27: [22, 29],               # connector
        28: [29],                   # edge
        
        # Layer 10: Ten steps - furthest from target (2 nodes)
        26: [21, 27],               # far corner
        99: [28, 27],               # placeholder - will use node numbers properly
    }
    
    # ==========================================================================
    # Balanced Robot Navigation Network (30 nodes, ~8 layers)
    # ==========================================================================
    # Design principles:
    #   - Layer 1-3: HIGH connectivity (cutting edges near target won't isolate branches)
    #   - Layer 4-7: MEDIUM bottlenecks (cutting creates 4-5 node invariant subsets)
    #   - Realistic: agent learned some redundant paths near goal, but specific paths far away
    # ==========================================================================
    
    example_graph = {
        # ★ TARGET: Node 0
        0: [],
        
        # === Layer 1: THREE approaches to target (robust near goal) ===
        1: [0],                     # left approach
        2: [0],                     # center approach
        3: [0],                     # right approach
        
        # === Layer 2: Cross-connected (robust) ===
        4: [1, 2],                  # left-center bridge
        5: [2, 3],                  # center-right bridge
        6: [1],                     # left branch
        7: [3],                     # right branch
        
        # === Layer 3: Still some redundancy ===
        8: [4, 6],                  # left hub
        9: [4, 5],                  # center hub
        10: [5, 7],                 # right hub
        
        # === Layer 4: ★ BOTTLENECKS START HERE ★ ===
        11: [8],                    # left-only path
        12: [8, 9],                 # left-center connector
        13: [9, 10],                # center-right connector
        14: [10],                   # right-only path
        
        # === Layer 5: ★ CRITICAL BOTTLENECKS ★ ===
        15: [11],                   # ★ depends only on 11!
        16: [11, 12],               # left side
        17: [12, 13],               # center
        18: [13, 14],               # right side
        19: [14],                   # ★ depends only on 14!
        
        # === Layer 6: Isolated branches form ===
        20: [15],                   # ★ chain: depends on 15 only!
        21: [15, 16],               # left
        22: [17],                   # center (single!)
        23: [18, 19],               # right
        24: [19],                   # ★ chain: depends on 19 only!
        
        # === Layer 7: Deep exploration ===
        25: [20, 21],               # left deep
        26: [20],                   # ★ depends on 20 only!
        27: [22, 23],               # right deep
        28: [24],                   # ★ depends on 24 only!
        
        # === Layer 8: Furthest ===
        29: [26, 25],               # far left (depends on chain)
    }
    
    target_node = 0
    
    print("=" * 60)
    print("Invariant Subset Finder - Example")
    print("=" * 60)
    print(f"\nGraph: {example_graph}")
    print(f"Target/Absorbing Node: {target_node}")
    
    # First, show which nodes can reach target in original graph
    original_reachable = find_nodes_reaching_target(example_graph, target_node)
    all_nodes = get_all_nodes(example_graph)
    original_invariant = all_nodes - original_reachable
    
    print(f"\nOriginal graph analysis:")
    print(f"  Nodes that can reach target {target_node}: {original_reachable}")
    print(f"  Nodes that cannot reach target: {original_invariant}")
    
    # Compute and display reachability layers
    layers = compute_reachability_layers(example_graph, target_node)
    print(f"\nReachability layers (distance to target):")
    for layer_num in sorted(set(layers.values())):
        nodes_in_layer = [n for n, l in layers.items() if l == layer_num]
        if layer_num == -1:
            print(f"  Unreachable: {sorted(nodes_in_layer)}")
        else:
            print(f"  Layer {layer_num}: {sorted(nodes_in_layer)}")
    
    # Test removing a specific edge - removing (1, 0) cuts off left approach
    test_edge = (1, 0)
    invariant = find_invariant_subset(example_graph, target_node, test_edge)
    print(f"\nAfter removing edge {test_edge}:")
    print(f"  Invariant subset (cannot reach target): {invariant}")
    
    # Show all edge removals
    print("\n" + "-" * 60)
    print("Invariant subsets for all possible edge removals:")
    print("-" * 60)
    
    all_results = find_all_invariant_subsets(example_graph, target_node)
    for edge, inv_subset in sorted(all_results.items()):
        if inv_subset:
            print(f"  Remove edge {edge} -> Invariant subset: {inv_subset}")
        else:
            print(f"  Remove edge {edge} -> No invariant subset (all nodes can reach target)")
    
    # Visualize the network
    print("\n" + "=" * 60)
    print("Generating Network Visualizations...")
    print("=" * 60)
    
    # Visualization 1: Spring layout - organic robot navigation view
    visualize_network(
        example_graph, 
        target_node,
        title="Robot Navigation State Space $\\mathcal{S}$\n(Target state $s_T$ = 0 in red)",
        figsize=(16, 12),
        save_path="/Users/zhongzhiyi/Downloads/inx/network_spring.png"
    )
    
    # Visualization 2: Hierarchical layout by reachability layer
    visualize_network_hierarchical(
        example_graph, 
        target_node,
        title="Robot Navigation State Space $\\mathcal{S}$ - Hierarchical View\n(Nodes arranged by distance to target $s_T$ = 0)",
        figsize=(18, 14),
        save_path="/Users/zhongzhiyi/Downloads/inx/network_hierarchical.png"
    )
    
    # Visualization 3: Show invariant subset after removing an edge
    # Removing edge (1, 0) disconnects left approach corridor
    test_edge = (1, 0)
    inv_subset = find_invariant_subset(example_graph, target_node, test_edge)
    visualize_network_hierarchical(
        example_graph,
        target_node,
        title=f"Invariant Subset after Removing Edge {test_edge}\n(Gray nodes cannot reach target $s_T$ = 0)",
        figsize=(18, 14),
        save_path="/Users/zhongzhiyi/Downloads/inx/network_invariant.png",
        highlight_edges=[test_edge],
        invariant_subset=inv_subset
    )

