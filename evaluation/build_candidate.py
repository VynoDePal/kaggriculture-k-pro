"""Build the standalone K Pro 6 + CARE horizon candidate."""

from argparse import ArgumentParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "k_pro" / "k_pro6.py"
ADAPTER = ROOT / "research" / "pro6-next" / "care_horizon_fp.py"
DEFAULT_OUTPUT = ROOT / "candidates" / "k_pro6_care_fp.py"


def render(parent=PARENT, adapter=ADAPTER):
    """Return a reproducible standalone source made only from the two archives."""
    parent_source = Path(parent).read_text(encoding="utf-8")
    adapter_source = Path(adapter).read_text(encoding="utf-8")
    suffix = f'''\n\n# Archived CARE horizon adapter, embedded for standalone execution.\n_care_fp = _embedded({adapter_source!r}, "care_horizon_fp")\n_care_fp.install(_reference)\ndel _care_fp\n\n# This must remain the final callable selected by the Kaggle loader.\ndef kaggle_agent(observation, configuration=None):\n    return _decision(observation, configuration)\n'''
    return parent_source.rstrip() + suffix


def build(output=DEFAULT_OUTPUT, parent=PARENT, adapter=ADAPTER):
    """Create *output* exclusively; existing paths are never overwritten."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render(parent, adapter))
    return output


def main():
    parser = ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
