#!/usr/bin/env python3
"""Convert raster floor-plan PDFs into app assets and a machine-readable graph.

The source maps are still images, so topology cannot be recovered reliably from
pixels alone. This tool automates lossless page extraction, a yellow walkable-area
mask, provenance, and merging of reviewed semantic annotations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "source_data" / "floorplan_sources.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "assets" / "floorplans" / "taipei_main_station",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_to_image(document: fitz.Document, page_number: int) -> Image.Image:
    page = document[page_number - 1]
    images = page.get_images(full=True)

    # The provided map uses one page-sized JPEG per page. Extract it directly to
    # avoid introducing another lossy rendering pass. Render vector PDFs instead.
    if len(images) == 1:
        extracted = document.extract_image(images[0][0])
        from io import BytesIO

        return Image.open(BytesIO(extracted["image"])).convert("RGB")

    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def yellow_walkable_mask(image: Image.Image) -> Image.Image:
    """Return a transparent mask of the yellow station circulation area.

    It is deliberately only a visual aid for annotation. Routing must use the
    reviewed graph because labels and line badges can share the same colour.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    yellow = (
        (red >= 185)
        & (green >= 135)
        & (blue <= 125)
        & ((red - blue) >= 90)
        & ((green - blue) >= 55)
    )
    mask = Image.fromarray(np.where(yellow, 255, 0).astype(np.uint8), mode="L")
    # Close small JPEG/text holes without attempting to infer full topology.
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    # Use the binary result as alpha as well as luminance. Browsers commonly
    # interpret PNG masks by alpha, where an opaque black pixel is still part of
    # the mask. Transparent background makes the asset unambiguous in CSS,
    # Flutter, design tools, and image-processing code.
    transparent_mask = Image.new("RGBA", mask.size, (255, 255, 255, 0))
    transparent_mask.putalpha(mask)
    return transparent_mask


def pixel_position(position: dict[str, float], width: int, height: int) -> dict[str, int]:
    return {
        "x": round(position["x"] * width),
        "y": round(position["y"] * height),
    }


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_json(config_path)
    source_dir = config_path.parent
    annotations = load_json(source_dir / config["annotations"])
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    floors: list[dict[str, Any]] = []
    dimensions: dict[str, tuple[int, int]] = {}
    sources: list[dict[str, Any]] = []

    for document_config in config["documents"]:
        pdf_path = source_dir / document_config["path"]
        document = fitz.open(pdf_path)
        sources.append(
            {
                "file": document_config["path"],
                "sha256": sha256(pdf_path),
                "sourceUrl": document_config.get("sourceUrl"),
                "notes": document_config.get("notes"),
            }
        )

        for page_config in document_config["pages"]:
            floor_id = page_config["floorId"]
            stem = floor_id.lower()
            image = page_to_image(document, page_config["page"])
            image_path = output_dir / f"{stem}.png"
            mask_path = output_dir / f"{stem}_walkable_mask.png"
            image.save(image_path, format="PNG", optimize=True)
            yellow_walkable_mask(image).save(mask_path, format="PNG", optimize=True)

            width, height = image.size
            dimensions[floor_id] = (width, height)
            floors.append(
                {
                    "id": floor_id,
                    "label": page_config["label"],
                    "source": {
                        "pdf": document_config["path"],
                        "page": page_config["page"],
                    },
                    "image": f"assets/floorplans/taipei_main_station/{stem}.png",
                    "walkableMask": f"assets/floorplans/taipei_main_station/{stem}_walkable_mask.png",
                    "width": width,
                    "height": height,
                }
            )
        document.close()

    nodes = []
    for node in annotations["nodes"]:
        width, height = dimensions[node["floorId"]]
        nodes.append(
            {
                **node,
                "pixelPosition": pixel_position(node["position"], width, height),
            }
        )

    manifest = {
        "schemaVersion": config["schemaVersion"],
        "stationId": config["stationId"],
        "stationNames": config["stationNames"],
        "coordinateSystem": annotations["coordinateSystem"],
        "reviewStatus": annotations["reviewStatus"],
        "costUnit": annotations["costUnit"],
        "sources": sources,
        "floors": floors,
        "nodes": nodes,
        "edges": annotations["edges"],
        "destinations": annotations["destinations"],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(floors)} floors, {len(nodes)} nodes, and {len(annotations['edges'])} edges")
    print(manifest_path)


if __name__ == "__main__":
    main()
