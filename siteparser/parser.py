import json
from pathlib import Path
import networkx as nx
import re
from rich.table import Table
from rich.console import Console
from pyvis.network import Network
import tempfile
from uuid import uuid4

from siteparser.conf import log, LOCAL_DIR
from siteparser.devices import Dev, Edge


class SiteParser:

    _ignore = {"node_name", "path_nodes"}

    def __init__(self, fpath: str | Path):
        """
        Parse a JSON file containing device location specifications.

        Args:
            fpath: Path to the JSON file.

        Raises:
            FileNotFoundError: Raised if the file path is invalid.
        """
        if isinstance(fpath, str):
            fpath = Path(fpath)
        if not fpath.exists():
            raise FileNotFoundError(f"Invalid file path: '{fpath}'")
        self._spec = json.loads(fpath.read_text())
        self.devices = {}
        self.edges = []

        # Search patterns
        self.dev_regex = re.compile(rf"([a-zA-Z]+)(.+)?", re.I)
        self.edge_regex = re.compile(rf"(conn|dest)(.+)?", re.I)

        self.parse()

    def summarise(self):
        """
        Print a summary about the available devices.
        """
        tbl = Table(
            "Node ID",
            "Device type",
            "Label",
            "Index",
            "Side",
            "Action",
            "Relative positions",
            "Origin",
            "Plate path nodes",
            "Relative entrypoint",
            "Relative positions",
        )
        con = Console()

        for devtype, dev in self.devices.items():
            tbl.add_row(
                str(dev.node_id),
                dev.dev_type,
                dev.label,
                str(dev.idx),
                dev.side,
                dev.action,
                str(len(dev.relatives.positions)),
                str(dev.origin),
                str(len(dev.plate_path)),
                str(dev.relatives.entrypoint),
                str(len(dev.relatives.positions)),
            )

        con.print(tbl)

    def _make_dev(
        self,
        label: str,
        value: dict | list | None,
    ) -> Dev:
        """
        Split a name string into components.

        Args:
            key: The key to parse.

        Returns:
            A device (see above).
        """

        # Find if this is a device and whether it's enumerated.
        matches = self.dev_regex.search(label.lower())

        if matches is None:
            return

        dev_type, rest = matches.groups()

        if rest is None:
            rest = []
        elif isinstance(rest, str):
            rest = rest.split("_")

        rest = [r for r in rest if len(r) > 0]

        dev = Dev(rest, value, len(self.devices), dev_type)
        self.devices[label] = dev

        return dev

    def parse(self):
        """
        Parse the JSON specification and populate
        the specification attributes.
        """

        self.devices.clear()
        for name, props in self._spec.items():

            name = name.lower()

            if name in SiteParser._ignore:
                continue

            # Split the name into useful components
            dev = self._make_dev(name, props)

        # Create paths
        # ==================================================
        self.edges.clear()
        for edge_name, entry in self._spec["path_nodes"].items():
            matches = self.edge_regex.search(edge_name)
            if matches is None:
                continue
            src = self.devices.get(entry[0])
            tgt = self.devices.get(entry[1])
            if src and tgt:
                self.edges.append(Edge(src, tgt))

    def make_graph(
        self,
        output: str | Path | None = None,
        visualise: bool = False,
        skip_disconnected: bool = True,
    ) -> nx.Graph:
        """
        Construct a NetworkX graph from the specification.

        Args:
            output: File for saving the graph in GML format.
            visualise: Visualise the graph using PyVis.
            skip_disconnected: Don't add disconnected nodes to the GML graph.

        Returns:
            A NetworkX graph.
        """

        g = nx.Graph()

        connected_devs = set()
        for edge in self.edges:

            # Add the edge from source to the target
            src_ep = edge.src.relatives.entrypoint
            src_label = "_".join([edge.src.label, src_ep.label])

            tgt_ep = edge.tgt.relatives.entrypoint
            tgt_label = "_".join([edge.tgt.label, tgt_ep.label])
            g.add_edge(src_label, tgt_label)

            connected_devs.add(src_label)
            connected_devs.add(tgt_label)

        for dev in self.devices.values():


            pos = dev.relatives.entrypoint
            label = "_".join([dev.label, pos.label])
            if skip_disconnected and label not in connected_devs:
                continue

            args = pos.get_node_args()
            g.add_node(label, **args)
            ep_node = label

            for pos in dev.relatives.positions:

                # Start from the entrypoint
                cur_node = ep_node

                # Plate path nodes (if any)
                for ppath in dev.plate_path:
                    args = ppath.get_node_args(pos)
                    label = "_".join([dev.label, pos.label, ppath.label])
                    g.add_node(label, **args)
                    next_node = label
                    g.add_edge(cur_node, next_node)
                    cur_node = next_node

                args = pos.get_node_args()
                label = "_".join([dev.label, pos.label])
                g.add_node(label, **args)
                next_node = label

                # Add an edge to the position
                g.add_edge(cur_node, next_node)

        if output is not None:
            nx.write_gml(g, Path(output).resolve().absolute())

        net = None
        if visualise:
            net = Network(
                bgcolor="#222222",
                font_color="#ffffff",
                layout="hierarchical",
                select_menu=True,
                filter_menu=True,
            )
            net.from_nx(g)
            net.show_buttons()
            with tempfile.TemporaryDirectory(delete=False) as tmp_dir:
                net.write_html(
                    str(Path(tmp_dir) / f"paths-{uuid4()}.html"),
                    open_browser=True,
                    notebook=False,
                )

        return g, net
