import json
from pathlib import Path
from typing import Any, List, Dict

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def slate_dir(slate_id: str) -> Path:
    d = DATA_DIR / slate_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_json(path: Path, obj: Any) -> None:
    with path.open("w") as f:
        json.dump(obj, f, indent=2)

def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)

def save_projections(slate_id: str, items: List[Dict[str, Any]]) -> None:
    save_json(slate_dir(slate_id) / "projections.json", items)

def save_ownership(slate_id: str, items: List[Dict[str, Any]]) -> None:
    save_json(slate_dir(slate_id) / "ownership.json", items)

def get_inputs_info(slate_id: str) -> Dict[str, Any]:
    d = slate_dir(slate_id)
    proj = load_json(d / "projections.json") or []
    own = load_json(d / "ownership.json") or []
    return {
        "slate_id": slate_id,
        "projections_count": len(proj),
        "ownership_count": len(own),
        "has_projections": len(proj) > 0,
        "has_ownership": len(own) > 0,
    }
