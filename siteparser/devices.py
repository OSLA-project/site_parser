from dataclasses import dataclass, field

from siteparser.coords import Coords


@dataclass
class Relatives:
    entrypoint: Coords = Coords("entrypoint")
    positions: list = field(default_factory=list)


@dataclass
class Dev:

    _parts: list = None
    _children: dict | list | None = None
    node_id: int = 0
    dev_type: str = ""
    label: str = ""
    idx: int | None = None
    side: str | None = None
    action: str | None = None
    origin: Coords = Coords()
    plate_path: list = field(default_factory=list)
    relatives: Relatives | None = None

    def _parse_plate_path(self, data: dict | None) -> dict:
        """
        Parse a plate path specification.

        Args:
            data: A dictionary of integer positions and locations as 6-DoF arrays.

        Returns:
            A list of plate path coordinates.
        """

        if data is None:
            return []
        return [
            Coords(
                f"ppath_{i}",
                data[str(i)],
                self.origin,
            )
            for i in range(1, len(data) + 1)
        ]

    def _parse_relatives(self, data: dict):
        """
        Parse a list of relative positions.

        Should be a dictionary containing an entry point and
        any number of other positions.

        Args:
            data: A dictionary specification of relative positions
                (integer keys and 6-DoF arrays).

        Returns:
            A Relatives object.
        """
        relatives = Relatives(
            entrypoint=Coords(
                f"entrypoint",
                data.pop("entrypoint"),
                self.origin,
            )
        )
        positions = [data.get(f"pos{i+1}") for i in range(len(data))]
        for pos_idx, pos in enumerate(positions):
            if pos is not None:
                relatives.positions.append(
                    Coords(
                        f"pos_{pos_idx+1}",
                        pos,
                        self.origin,
                    )
                )

        return relatives

    def _process_parts(self):

        match len(self._parts):
            case 1:
                match self.dev_type:
                    # Special cases
                    case "rot":
                        self.side = self._parts[0]
                    case "platereader":
                        self.action = self._parts[0]
                    case _:
                        self.idx = self._parts[0]
            case 2:
                # Index, action (p/d)
                self.idx, self.action = self._parts
            case 3:
                # Index, side (long/short), action (p/d)
                self.idx, self.side, self.action = self._parts

        # Reset the parts
        self._parts = []

    def _process_children(self):

        # Populate the origin, plate path and relative positions.
        self.origin = Coords(f"origin", self._children.get("origin"))
        self.plate_path = self._parse_plate_path(self._children.get("plate_path"))
        self.relatives = self._parse_relatives(self._children.get("relatives"))

        # Reset the child entries
        self._children = {}

    def __post_init__(self):
        """
        Process the parts of the specification and the child nodes.
        """

        self._process_parts()

        # Create a predictable label
        self.label = "_".join(
            [
                item
                for item in (self.dev_type, self.idx, self.side, self.action)
                if item is not None
            ]
        )

        self._process_children()


@dataclass
class Edge:
    src: Dev
    tgt: Dev
