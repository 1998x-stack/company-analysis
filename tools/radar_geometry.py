from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, UnidentifiedImageError

DIMENSIONS = ("cashFlow", "profitability", "debt", "operations", "sustainability")
DOT_COLOR = b"\xf5\x9e\x0b"


def fit_error(points: list[tuple[float, float]], scores: dict) -> float:
    vectors = [(scores[key] * math.sin(index * 2 * math.pi / 5),
                -scores[key] * math.cos(index * 2 * math.pi / 5))
               for index, key in enumerate(DIMENSIONS)]
    mean_vector = [sum(point[axis] for point in vectors) / 5 for axis in (0, 1)]
    mean_point = [sum(point[axis] for point in points) / 5 for axis in (0, 1)]
    scale = sum((vector[axis] - mean_vector[axis]) * (point[axis] - mean_point[axis])
                for vector, point in zip(vectors, points) for axis in (0, 1)) / sum(
                    (vector[axis] - mean_vector[axis]) ** 2
                    for vector in vectors for axis in (0, 1))
    center = [mean_point[axis] - scale * mean_vector[axis] for axis in (0, 1)]
    return max(math.dist(point, [center[axis] + scale * vector[axis]
                                 for axis in (0, 1)])
               for point, vector in zip(points, vectors))


def png_dots(path: Path) -> list[tuple[float, float]]:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width = rgb.width
        raw = rgb.tobytes()
    points = set()
    offset = 0
    while (position := raw.find(DOT_COLOR, offset)) != -1:
        if position % 3 == 0:
            pixel = position // 3
            points.add((pixel % width, pixel // width))
        offset = position + 3
    groups = []
    while points:
        seed = points.pop()
        pending = [seed]
        group = [seed]
        while pending:
            x, y = pending.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in points:
                    points.remove(neighbor)
                    pending.append(neighbor)
                    group.append(neighbor)
        if len(group) >= 60:
            groups.append((sum(x for x, _ in group) / len(group),
                           sum(y for _, y in group) / len(group)))
    if len(groups) != 5:
        return []
    groups.sort()
    left = sorted(groups[:2], key=lambda point: point[1])
    right = sorted(groups[3:], key=lambda point: point[1])
    return [groups[2], right[0], right[1], left[1], left[0]]


def svg_dots(path: Path) -> list[tuple[float, float]]:
    root = ElementTree.parse(path).getroot()
    points = [(float(node.attrib["cx"]), float(node.attrib["cy"]))
              for node in root.iter() if node.tag.endswith("circle")
              and node.attrib.get("fill") == "#f0b15e"]
    return points if len(points) == 5 else []


def verify(path: Path, scores: dict) -> dict:
    try:
        points = png_dots(path) if path.suffix.lower() == ".png" else svg_dots(path)
    except (OSError, ValueError, ElementTree.ParseError, UnidentifiedImageError):
        points = []
    if len(points) != 5:
        return {"status": "geometry_unavailable", "max_pixel_residual": None}
    residual = fit_error(points, scores)
    threshold = 3 if path.suffix.lower() == ".png" else 1
    return {"status": "geometry_matches_catalog" if residual <= threshold
            else "geometry_differs_from_catalog",
            "max_pixel_residual": round(residual, 2)}
