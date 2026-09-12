"""Build the standalone K Pro 6 sale-pressure candidate."""

from argparse import ArgumentParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "k_pro" / "k_pro6.py"
ADAPTER = ROOT / "research" / "sale_pressure.py"
DEFAULT_OUTPUT = ROOT / "candidates" / "k_pro6_sale_pressure.py"


def render(parent=PARENT, adapter=ADAPTER):
    """Render from the exact parent plus an independently embedded adapter."""
    parent_source = Path(parent).read_text(encoding="utf-8")
    adapter_source = Path(adapter).read_text(encoding="utf-8")
    suffix = f'''\n\n# Sale-pressure adapter, embedded for standalone execution.\n_sale_pressure = _embedded({adapter_source!r}, "sale_pressure")\n_decision = _sale_pressure.make_agent(_decision)\ndel _sale_pressure\n\n# This must remain the final callable selected by the Kaggle loader.\ndef kaggle_agent(observation, configuration=None):\n    return _decision(observation, configuration)\n'''
    return parent_source.rstrip() + suffix


def build(output=DEFAULT_OUTPUT, parent=PARENT, adapter=ADAPTER):
    """Create *output* exclusively after all source rendering succeeds."""
    source = render(parent, adapter)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(source)
    return output


def main():
    parser = ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
