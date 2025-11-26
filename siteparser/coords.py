from __future__ import annotations
import numpy as np
from copy import deepcopy


class Coords:

    def __init__(
        self,
        label: str = "",
        coords: list | tuple | np.ndarray | Coords | None = None,
        origin: list | tuple | np.ndarray | Coords | None = None,
    ):

        self.label = label
        self.coords = self._numpify(coords)
        self.origin = self._numpify(origin)

    def _numpify(self, coords: list | tuple | np.ndarray | None = None) -> np.ndarray:
        """
        Ensure that coordinates are represented as NumPy arrays.

        Args:
            coords: Coordinates (x, y, z, roll, pitch, yaw).

        Raises:
            AttributeError: Raised if the coordinates do not follow the expected format.

        Returns:
            The coordinates as a NumPy array.
        """
        _dtype = np.float32
        if coords is None:
            coords = np.zeros((6,), dtype=_dtype)

        elif isinstance(coords, (list, tuple)):
            coords = np.array(coords, dtype=_dtype)

        elif isinstance(coords, Coords):
            coords = deepcopy(coords.coords)

        if len(coords) != 6:
            raise AttributeError(
                f"Invalid coordinate vector: expected size is 6, got {len(coords)}"
            )

        # Deep-copy the array to preempt weirdness
        return deepcopy(coords)

    def get_node_args(
        self,
        *offsets: list[Coords],
    ) -> dict:
        """
        Construct an argument dictionary for nodes in a
        NetworkX-compatible representation of the coordinates.

        Optionally takes a list of Coord objects as relative offsets.

        Returns:
            A dictionary of NetworkX node properties.
        """
        coords = ["x", "y", "z", "roll", "pitch", "yaw"]

        arr = deepcopy(self.coords) + self.origin
        for offset in offsets:
            arr += offset.coords

        return dict(zip(coords, arr.tolist()))

    def __repr__(self) -> str:
        """
        Convert the coordinates to a string.

        Returns:
            The stringified array.
        """
        return np.array2string(
            self.coords, precision=3, formatter={"float_kind": lambda x: f"{x:>8.4}"}
        )
