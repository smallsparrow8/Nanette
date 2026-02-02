"""
Graph Renderer for Address Interaction Visualizations
Renders NetworkX graphs as dark-themed PNG images using matplotlib
"""
import matplotlib
matplotlib.use('Agg')  # Headless rendering — no GUI needed

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import io
from typing import Dict, Any, Optional, List


# Nanette's dark mystical color palette
COLORS = {
    "background": "#0d1117",
    "title": "#c9d1d9",
    "subtitle": "#8b949e",
    "center_node": "#ffd700",          # Gold — the analyzed contract
    "known_safe": "#238636",           # Green — DEXs, bridges, known safe
    "regular": "#388bfd",              # Blue — regular addresses
    "flagged": "#da3633",              # Red — suspicious/flagged
    "burn": "#6e40c9",                 # Purple — burn addresses
    "edge_default": "#30363d",         # Dark gray edges
    "edge_high_value": "#f85149",      # Red for high-value flows
    "edge_medium_value": "#d29922",    # Yellow for medium value
    "edge_low_value": "#30363d",       # Gray for low value
    "legend_bg": "#161b22",
    "legend_text": "#c9d1d9",
    "annotation": "#8b949e",
}


class GraphRenderer:
    """Renders NetworkX interaction graphs as styled PNG images"""

    def render_interaction_graph(self, graph: nx.DiGraph,
                                  center_address: str,
                                  title: str = "Address Interaction Map",
                                  stats: Optional[Dict] = None,
                                  patterns: Optional[List[Dict]] = None) -> bytes:
        """
        Render the interaction graph to a PNG image.

        Args:
            graph: NetworkX directed graph of address interactions
            center_address: The primary address being analyzed
            title: Graph title
            stats: Optional stats dict for annotation
            patterns: Optional detected patterns for annotation

        Returns:
            PNG image as bytes
        """
        if len(graph.nodes) == 0:
            return self._render_empty_graph(center_address)

        # Limit nodes for readability
        display_graph = self._limit_nodes(graph, center_address, max_nodes=25)

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(14, 10), facecolor=COLORS["background"])
        ax.set_facecolor(COLORS["background"])

        # Compute layout
        if len(display_graph.nodes) <= 10:
            pos = nx.spring_layout(display_graph, k=2.5, iterations=50, seed=42)
        else:
            pos = nx.kamada_kawai_layout(display_graph)

        # Draw edges
        self._draw_edges(display_graph, pos, ax)

        # Draw nodes
        self._draw_nodes(display_graph, pos, center_address, ax)

        # Draw labels
        self._draw_labels(display_graph, pos, ax)

        # Title
        center_short = f"{center_address[:6]}...{center_address[-4:]}"
        ax.set_title(
            f"{title}\n{center_short}",
            fontsize=16, fontweight="bold",
            color=COLORS["title"], pad=20
        )

        # Stats subtitle
        if stats:
            subtitle = (f"{stats.get('total_transactions', 0)} transactions  |  "
                        f"{stats.get('unique_addresses', 0)} addresses  |  "
                        f"{stats.get('total_value_in', 0):.4f} ETH in  |  "
                        f"{stats.get('total_value_out', 0):.4f} ETH out")
            ax.text(0.5, -0.02, subtitle,
                    transform=ax.transAxes, ha="center",
                    fontsize=9, color=COLORS["subtitle"])

        # Legend
        self._draw_legend(ax)

        # Pattern annotations
        if patterns:
            self._draw_pattern_annotations(patterns, ax)

        # Branding
        ax.text(0.99, 0.01, "Nanette — Guardian of $RIN",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color=COLORS["subtitle"], style="italic", alpha=0.7)

        ax.axis("off")
        plt.tight_layout(pad=1.5)

        # Render to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=COLORS["background"],
                    edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _draw_nodes(self, graph: nx.DiGraph, pos: Dict,
                     center_address: str, ax: plt.Axes):
        """Draw nodes with color coding"""
        center = center_address.lower()

        for node in graph.nodes:
            data = graph.nodes[node]
            x, y = pos[node]

            # Determine color and size
            if data.get("is_center"):
                color = COLORS["center_node"]
                size = 800
                edge_color = "#ffd700"
                zorder = 5
            elif _is_burn_address(node):
                color = COLORS["burn"]
                size = 400
                edge_color = "#6e40c9"
                zorder = 3
            elif data.get("is_known"):
                color = COLORS["known_safe"]
                size = 500
                edge_color = "#238636"
                zorder = 4
            else:
                # Size by interaction count
                degree = graph.degree(node)
                size = max(200, min(600, 200 + degree * 50))
                color = COLORS["regular"]
                edge_color = "#388bfd"
                zorder = 2

            ax.scatter(x, y, s=size, c=color, edgecolors=edge_color,
                       linewidths=1.5, zorder=zorder, alpha=0.9)

    def _draw_edges(self, graph: nx.DiGraph, pos: Dict, ax: plt.Axes):
        """Draw edges with width and color based on value"""
        if not graph.edges:
            return

        # Get max value for normalization
        max_weight = max(
            (d.get("weight", 1) for _, _, d in graph.edges(data=True)),
            default=1
        )

        for u, v, data in graph.edges(data=True):
            weight = data.get("weight", 1)
            value = data.get("value", 0)

            # Width based on transaction count
            width = max(0.5, min(4.0, (weight / max(max_weight, 1)) * 4.0))

            # Color based on value
            if value > 10:
                color = COLORS["edge_high_value"]
                alpha = 0.7
            elif value > 1:
                color = COLORS["edge_medium_value"]
                alpha = 0.5
            else:
                color = COLORS["edge_low_value"]
                alpha = 0.3

            x_start, y_start = pos[u]
            x_end, y_end = pos[v]

            ax.annotate(
                "", xy=(x_end, y_end), xytext=(x_start, y_start),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=width,
                    alpha=alpha,
                    connectionstyle="arc3,rad=0.1",
                ),
                zorder=1,
            )

    def _draw_labels(self, graph: nx.DiGraph, pos: Dict, ax: plt.Axes):
        """Draw address labels on nodes"""
        for node in graph.nodes:
            data = graph.nodes[node]
            x, y = pos[node]

            label = data.get("label", node[:8])
            if len(label) > 18:
                label = label[:16] + "..."

            # Offset label slightly above node
            fontsize = 7 if data.get("is_center") else 6
            fontweight = "bold" if data.get("is_center") or data.get("is_known") else "normal"
            color = COLORS["title"] if data.get("is_center") else COLORS["subtitle"]

            ax.text(x, y + 0.06, label,
                    fontsize=fontsize, fontweight=fontweight,
                    ha="center", va="bottom", color=color,
                    bbox=dict(boxstyle="round,pad=0.15",
                              facecolor=COLORS["background"],
                              edgecolor="none", alpha=0.8),
                    zorder=10)

    def _draw_legend(self, ax: plt.Axes):
        """Draw color legend"""
        legend_items = [
            mpatches.Patch(color=COLORS["center_node"], label="Analyzed Address"),
            mpatches.Patch(color=COLORS["known_safe"], label="Known (DEX/Bridge)"),
            mpatches.Patch(color=COLORS["regular"], label="Regular Address"),
            mpatches.Patch(color=COLORS["burn"], label="Burn Address"),
            mpatches.Patch(color=COLORS["flagged"], label="Flagged"),
        ]

        legend = ax.legend(
            handles=legend_items,
            loc="upper left",
            fontsize=7,
            facecolor=COLORS["legend_bg"],
            edgecolor=COLORS["edge_default"],
            labelcolor=COLORS["legend_text"],
            framealpha=0.9,
        )
        legend.set_zorder(20)

    def _draw_pattern_annotations(self, patterns: List[Dict], ax: plt.Axes):
        """Add pattern annotations to the bottom of the graph"""
        warning_patterns = [p for p in patterns if p.get("severity") in ("warning", "high")]
        if not warning_patterns:
            return

        annotation_text = "Patterns Detected: " + " | ".join(
            p["description"][:60] for p in warning_patterns[:3]
        )

        ax.text(0.5, -0.06, annotation_text,
                transform=ax.transAxes, ha="center",
                fontsize=7, color=COLORS["flagged"],
                style="italic", alpha=0.9)

    def _limit_nodes(self, graph: nx.DiGraph, center: str,
                      max_nodes: int = 25) -> nx.DiGraph:
        """Limit graph to top N nodes by interaction volume"""
        if len(graph.nodes) <= max_nodes:
            return graph

        center = center.lower()

        # Score nodes by total edge weight
        node_scores = {}
        for node in graph.nodes:
            if node == center:
                node_scores[node] = float('inf')
                continue

            score = 0
            for _, _, data in graph.edges(node, data=True):
                score += data.get("weight", 1)
            for _, _, data in graph.in_edges(node, data=True):
                score += data.get("weight", 1)

            # Bonus for known addresses
            if graph.nodes[node].get("is_known"):
                score *= 2

            node_scores[node] = score

        # Keep top nodes
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        keep_nodes = set(n for n, _ in sorted_nodes[:max_nodes])

        return graph.subgraph(keep_nodes).copy()

    def _render_empty_graph(self, center_address: str) -> bytes:
        """Render a placeholder for addresses with no transaction data"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6), facecolor=COLORS["background"])
        ax.set_facecolor(COLORS["background"])

        center_short = f"{center_address[:6]}...{center_address[-4:]}"
        ax.text(0.5, 0.5,
                f"No transaction data found\nfor {center_short}\n\n"
                f"The address may be new, inactive,\nor on a chain I can't reach.",
                ha="center", va="center",
                fontsize=14, color=COLORS["subtitle"],
                transform=ax.transAxes)

        ax.text(0.99, 0.01, "Nanette — Guardian of $RIN",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color=COLORS["subtitle"], style="italic", alpha=0.7)

        ax.axis("off")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=COLORS["background"])
        plt.close(fig)
        buf.seek(0)
        return buf.read()


def _is_burn_address(address: str) -> bool:
    """Check if address is a known burn address"""
    burn_addrs = {
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dead",
        "0xdead000000000000000000000000000000000000",
    }
    return address.lower() in burn_addrs
