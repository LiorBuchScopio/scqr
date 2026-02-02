from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

class MultiKeyMap:
    """A map that indexes items by multiple keys, allowing lookup by any value."""

    def __init__(self, key_names: List[str]):
        self.key_names = key_names
        self.indices: Dict[str, Dict[Any, Any]] = {name: {} for name in key_names}

    def add(self, item: tuple):
        """Add an item tuple. Must have same length as key_names."""
        if len(item) != len(self.key_names):
            raise ValueError(f"Expected {len(self.key_names)} values, got {len(item)}")
        for i, name in enumerate(self.key_names):
            self.indices[name][item[i]] = item

    def get_by(self, key_name: str, value: Any) -> Optional[tuple]:
        """Get an item by a specific key name and value."""
        return self.indices.get(key_name, {}).get(value)

    def remove(self, item: tuple):
        """Remove an item from all indices."""
        for i, name in enumerate(self.key_names):
            self.indices[name].pop(item[i], None)


# Example usage:
# CELL_MAP = MultiKeyMap(["ref_id", "observation_id", "class_id"])
# CELL_MAP.add((ref_id, observation_id, class_id))
# CELL_MAP.get_by("ref_id", some_ref_id)
# CELL_MAP.get_by("observation_id", some_obs_id)
CELL_MAP = MultiKeyMap(["ref_id", "observation_id", "class_id"])
CELL_MAP.add((0, "segmented_neutrophil", 0))
CELL_MAP.add((1, "band_neutrophil", 0))
CELL_MAP.add((2, "metamyelocyte", 0))
CELL_MAP.add((3, "myelocyte", 0))
CELL_MAP.add((4, "promyelocyte", 0))
CELL_MAP.add((5, "blast", 0))
CELL_MAP.add((6, "lymphocyte", 0))
CELL_MAP.add((7, "atypical_lymphocyte", 0))
CELL_MAP.add((8, "large_granular_lymphocyte", 0))
CELL_MAP.add((9, "aberrant_lymphocyte", 0))
CELL_MAP.add((10, "monocyte", 0))
CELL_MAP.add((11, "eosinophil", 0))
CELL_MAP.add((12, "basophil", 0))
CELL_MAP.add((13, "plasma_cell", 0))
CELL_MAP.add((14, "hairy_cell", 0))
CELL_MAP.add((15, "blast_auer_rods", 0))
CELL_MAP.add((16, "pelger_cell", 0))
CELL_MAP.add((17, "nucleated_rbc", 0))
CELL_MAP.add((18, "smudge_cell", 0))
CELL_MAP.add((19, "polychromasia", 0))
CELL_MAP.add((20, "hypochromia", 0))
CELL_MAP.add((21, "anisocytosis", 0))
CELL_MAP.add((22, "microcytes", 0))
CELL_MAP.add((23, "macrocytes", 0))
CELL_MAP.add((24, "poikilocytosis", 0))
CELL_MAP.add((25, "target_cells", 0))
CELL_MAP.add((26, "schistocytes", 0))
CELL_MAP.add((27, "helmet_cells", 0))
CELL_MAP.add((28, "sickle_cells", 0))
CELL_MAP.add((29, "spherocytes", 0))
CELL_MAP.add((30, "elliptocytes", 0))
CELL_MAP.add((31, "ovalocytes", 0))
CELL_MAP.add((32, "teardrop_cells", 0))
CELL_MAP.add((33, "stomatocytes", 0))
CELL_MAP.add((34, "acanthocytes", 0))
CELL_MAP.add((35, "echinocytes", 0))
CELL_MAP.add((36, "bite_cells", 0))
CELL_MAP.add((37, "blister_cells", 0))
CELL_MAP.add((38, "basophilic_stippling", 0))
CELL_MAP.add((39, "howell_jolly_bodies", 0))
CELL_MAP.add((40, "micro_organisms", 0))
CELL_MAP.add((41, "pappenheimer_bodies", 0))
CELL_MAP.add((42, "agglutination", 0))
CELL_MAP.add((43, "rouleaux_formation", 0))
CELL_MAP.add((44, "platelets", 0))
CELL_MAP.add((45, "large_platelets", 0))
CELL_MAP.add((46, "giant_platelets", 0))
CELL_MAP.add((47, "hypogranular_platelet", 0))
CELL_MAP.add((48, "platelet_clumps", 0))
CELL_MAP.add((49, "platelet_satellitism", 0))

def map_observation_id_to_class_id(obs_id:str)->int:
    cell = CELL_MAP.get_by('observation_id',obs_id)
    if not cell:
        return -1
    return cell[2]

def map_observation_to_ref(obs_id:str)->int:
    cell = CELL_MAP.get_by('observation_id',obs_id)
    if not cell:
        return -1
    return cell[0]

def to_epoch_seconds(expiration: Any) -> Optional[int]:
    """
    Accepts:
      - int epoch seconds
      - ISO8601 string like '2026-02-01T09:20:06Z' or with offset '...+02:00'
    Returns UTC epoch seconds.
    """
    if expiration is None:
        return None
    if isinstance(expiration, int):
        return expiration
    if isinstance(expiration, str):
        s = expiration.strip()
        # Prefer ISO8601. Support 'Z' shorthand.
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            # If you truly must accept strings like "Sunday, February 1, 2026 ...",
            # parse them *outside* this library to ISO8601 first.
            return None
        if dt.tzinfo is None:
            # treat naive as UTC (or change to your policy)
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.astimezone(timezone.utc).timestamp())
    return None