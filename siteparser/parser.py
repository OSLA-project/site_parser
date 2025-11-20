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
            "Entrypoint",
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
                str(dev.entrypoint),
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
        notebook: bool = False,
        browser: bool = True,
    ) -> nx.Graph:
        """
        Construct a NetworkX graph from the specification.

        Args:
            output: File for saving the graph in GML format.
            visualise: Visualise the graph using PyVis.
            notebook: Visualise inside a Jupyter notebook.
            browser: Visualise in a browser.

        Returns:
            A NetworkX graph.
        """

        g = nx.Graph()

        connected_devs = set()
        for edge in self.edges:
            connected_devs = connected_devs.union(set([edge.src.label, edge.tgt.label]))

        for dev_label, dev in self.devices.items():

            # if dev_label not in connected_devs:
            #     # Don't process disconnected devices
            #     continue

            entry_args = dev.entrypoint.get_node_args(dev.origin.coords)
            g.add_node(dev.relatives.entrypoint.label, **entry_args)

            for pos_idx, pos in enumerate(dev.relatives.positions):
                # pos_id = g.number_of_nodes()
                pos_args = pos.get_node_args(dev.origin.coords)

                g.add_node(pos.label, **pos_args)

                # Add the edge from the entrypoint
                g.add_edge(
                    dev.relatives.entrypoint.label,
                    pos.label,
                )

        for edge in self.edges:

            # Add the edge from source to the target
            src_rel = edge.src.relatives
            tgt_rel = edge.tgt.relatives
            src_args = src_rel.entrypoint.get_node_args(edge.src.origin.coords)
            tgt_args = tgt_rel.entrypoint.get_node_args(edge.tgt.origin.coords)
            g.add_node(src_rel.entrypoint.label, **src_args)
            g.add_node(tgt_rel.entrypoint.label, **tgt_args)

            g.add_edge(
                src_rel.entrypoint.label,
                tgt_rel.entrypoint.label,
            )

        if output is not None:
            nx.write_gml(g, Path(output).resolve().absolute())

        if visualise:
            net = Network(
                notebook=notebook,
                height="900px",
                width="100%",
                bgcolor="#222222",
                font_color="#ffffff",
                cdn_resources="in_line" if notebook else "local",
            )
            net.from_nx(g)
            with tempfile.TemporaryDirectory() as tmp_dir:
                net.write_html(
                    str(Path(tmp_dir) / f"paths-{uuid4()}.html"),
                    open_browser=browser,
                    notebook=notebook,
                )

        return g
