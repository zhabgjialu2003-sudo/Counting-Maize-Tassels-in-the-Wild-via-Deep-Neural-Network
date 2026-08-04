"""Generate editable per-story UML sources and low-fidelity wireframes."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "docs" / "requirements" / "user-story-extension-details.json"
UML_ROOT = ROOT / "docs" / "design" / "uml" / "story-extensions"
WIREFRAME_ROOT = ROOT / "docs" / "evidence" / "user-story-extensions" / "wireframes"


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "", value)


def story_dir(story_id: str) -> Path:
    return UML_ROOT / story_id.lower().replace(".", "-")


def escape_mermaid(value: str) -> str:
    return value.replace('"', "'").replace("<", "").replace(">", "")


def class_source(story: dict) -> str:
    boundary = safe_id(story["boundary"])
    control = safe_id(story["control"])
    entity = safe_id(story["entity"])
    lines = [
        "classDiagram",
        "direction LR",
        f'class {boundary}["Boundary: {escape_mermaid(story["boundary"])}"] {{',
    ]
    lines.extend(f"  +{escape_mermaid(item)}" for item in story["boundary_ops"])
    lines.extend(["}", f'class {control}["Control: {escape_mermaid(story["control"])}"] {{'])
    lines.extend(f"  +{escape_mermaid(item)}" for item in story["control_ops"])
    lines.extend(["}", f'class {entity}["Entity: {escape_mermaid(story["entity"])}"] {{'])
    lines.extend(f"  +{escape_mermaid(item)}" for item in story["entity_fields"])
    lines.extend([
        "}",
        f"{boundary} --> {control} : calls",
        f"{control} --> {entity} : reads / persists",
    ])
    return "\n".join(lines) + "\n"


def sequence_source(story: dict) -> str:
    actor = safe_id(story["role"] or "System")
    boundary = safe_id(story["boundary"])
    control = safe_id(story["control"])
    entity = safe_id(story["entity"])
    steps = [escape_mermaid(item) for item in story["sequence_steps"]]
    return "\n".join([
        "sequenceDiagram",
        "autonumber",
        f"actor {actor} as {escape_mermaid(story['role'])}",
        f"participant {boundary} as Boundary: {escape_mermaid(story['boundary'])}",
        f"participant {control} as Control: {escape_mermaid(story['control'])}",
        f"participant {entity} as Entity: {escape_mermaid(story['entity'])}",
        f"{actor}->>{boundary}: {steps[0]}",
        f"{boundary}->>{control}: {steps[1]}",
        f"{control}->>{entity}: {steps[2]}",
        f"{entity}-->>{control}: {steps[3]}",
        f"{control}-->>{boundary}: {steps[4]}",
        f"{boundary}-->>{actor}: {steps[5]}",
    ]) + "\n"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, selected_font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_wireframe(story: dict, output: Path) -> None:
    width, height = 1100, 760
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    green = "#2f7a42"
    pale = "#f5f7f5"
    line = "#9aa3a0"
    title_font = font(28, bold=True)
    label_font = font(22, bold=True)
    body_font = font(20)

    draw.rectangle((35, 28, width - 35, height - 28), outline="#444444", width=3)
    draw.rectangle((35, 28, width - 35, 84), fill=green)
    draw.text((52, 42), f"{story['id']}  {story['title']}", fill="white", font=title_font)
    draw.rectangle((52, 106, width - 52, 152), fill=pale, outline=line, width=2)
    draw.text((68, 117), f"Role: {story['role']}  |  Boundary: {story['boundary']}", fill="#26332b", font=body_font)

    y = 174
    available = width - 104
    for index, item in enumerate(story["wireframe"], start=1):
        lines = wrap(draw, item, body_font, available - 100)
        row_height = max(58, 22 + len(lines) * 25)
        draw.rectangle((52, y, width - 52, y + row_height), fill="white" if index % 2 else pale, outline=line, width=2)
        draw.rounded_rectangle((68, y + 12, 108, y + 46), radius=6, fill="#e6f2e8", outline=green, width=2)
        draw.text((80, y + 17), str(index), fill=green, font=label_font)
        for line_index, text_line in enumerate(lines):
            draw.text((128, y + 16 + line_index * 25), text_line, fill="#1f2923", font=body_font)
        y += row_height

    draw.text((52, height - 54), "Low-fidelity wireframe - implementation surface shown separately", fill="#59635d", font=font(17))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)


def build() -> None:
    stories = json.loads(DATA.read_text(encoding="utf-8"))
    UML_ROOT.mkdir(parents=True, exist_ok=True)
    WIREFRAME_ROOT.mkdir(parents=True, exist_ok=True)
    index_lines = ["# Per-Story Extension Diagrams", "", "Editable Mermaid sources and rendered PNGs for the 15 extension User Stories.", ""]
    for story in stories:
        directory = story_dir(story["id"])
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "bce-class.mmd").write_text(class_source(story), encoding="utf-8")
        (directory / "sequence.mmd").write_text(sequence_source(story), encoding="utf-8")
        make_wireframe(story, WIREFRAME_ROOT / f"{story['id'].replace('.', '_')}.png")
        index_lines.append(f"- `{story['id']}` - [{story['title']}]({directory.relative_to(UML_ROOT).as_posix()}/)")
    (UML_ROOT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Generated sources for {len(stories)} stories")


if __name__ == "__main__":
    build()
