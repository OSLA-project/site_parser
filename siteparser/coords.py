from __future__ import annotations
import numpy as np
from copy import deepcopy


class Coords:

    def __init__(
        self,
        label: str = "",
        coords: list | tuple | np.ndarray | None = None,
    ):

        self.label = label

        # Sanity checks
        # ==================================================
        _dtype = np.float32
        if coords is None:
            coords = np.zeros((6,), dtype=_dtype)

        elif isinstance(coords, (list, tuple)):
            coords = np.array(coords, dtype=_dtype)

        if len(coords) != 6:
            raise AttributeError(
                f"Invalid coordinate vector: expected size is 6, got {len(coords)}"
            )

        # Preempt weirdness
        self.coords = deepcopy(coords)

    def get_node_args(
        self,
        origin: np.ndarray | None = None,
    ) -> dict:
        """
        Construct an argument dictionary for constructing
        NetworkX-compatible representation of the coordinates,
        optionally relative to an origin point.

        Returns:
            An dictionary.
        """
        coords = ["x", "y", "z", "roll", "pitch", "yaw"]

        arr = deepcopy(self.coords)
        if origin is not None:
            arr += origin

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
