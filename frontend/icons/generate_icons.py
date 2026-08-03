"""Generate deterministic PNG PWA icons from simple vector-like primitives."""

from pathlib import Path

from PIL import Image, ImageDraw


def generate(size: int) -> None:
    scale = size / 512
    image = Image.new("RGB", (size, size), "#1f5136")
    draw = ImageDraw.Draw(image)

    def xy(points):
        return [(round(x * scale), round(y * scale)) for x, y in points]

    margin = round(18 * scale)
    radius = round(94 * scale)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill="#1f5136",
    )
    draw.ellipse((161 * scale, 92 * scale, 351 * scale, 386 * scale), fill="#f2bd3f")
    draw.polygon(
        xy([(258, 405), (248, 202), (303, 94), (297, 256)]),
        fill="#8fc878",
    )
    draw.polygon(
        xy([(242, 407), (150, 248), (162, 120), (224, 270)]),
        fill="#67a85b",
    )
    for x, y in [
        (218, 146), (259, 139), (299, 151), (200, 184), (240, 180),
        (281, 185), (318, 193), (199, 226), (240, 222), (281, 226),
        (317, 235), (205, 269), (246, 264), (286, 270), (311, 282),
        (220, 310), (259, 307), (294, 315),
    ]:
        r = 12 * scale
        draw.ellipse((x * scale - r, y * scale - r, x * scale + r, y * scale + r), fill="#9b6411")
    draw.ellipse((145 * scale, 370 * scale, 260 * scale, 410 * scale), fill="#b9dc91")
    draw.ellipse((252 * scale, 370 * scale, 367 * scale, 410 * scale), fill="#b9dc91")
    output = Path(__file__).with_name(f"maize-icon-{size}.png")
    image.save(output, "PNG", optimize=True)


if __name__ == "__main__":
    generate(192)
    generate(512)
