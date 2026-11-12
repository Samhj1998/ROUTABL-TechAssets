"""Render the local structured handoff without overwriting any file."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render(source):
    parts = ["# " + source["title"]]
    for heading, paragraphs in source["sections"]:
        part = ["## " + heading, *paragraphs]
        if heading == source["reference_heading"]:
            part.append("\n".join(f"- {asset} | \x60{path}\x60 | \x60{digest}\x60"
                                  for asset, path, digest in source["refs"]))
        parts.append("\n\n".join(part))
    return ("\n\n".join(parts) + "\n").encode("utf-8")


if __name__ == "__main__":
    data = json.loads((HERE / "HANDOFF_SOURCE.json").read_text(encoding="utf-8"))
    with (HERE / "HANDOFF_GENERATED.md").open("xb") as output:
        output.write(render(data))
