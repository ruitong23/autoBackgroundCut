from __future__ import annotations

import io
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


@dataclass
class ProcessConfig:
    input_dir: Path
    output_dir: Path
    random_pick_enabled: bool = False
    random_pick_count: int = 10


@dataclass
class ProcessStats:
    total: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0


class PersonExtractor:
    """Detect person regions and generate transparent-background outputs."""

    def __init__(self) -> None:
        self._yolo = self._init_yolo()

    def _init_yolo(self):
        try:
            from ultralytics import YOLO  # type: ignore

            model = YOLO("yolov8n.pt")
            return model
        except Exception:
            return None

    def _detect_person_bbox(self, image_path: Path) -> Optional[Tuple[int, int, int, int]]:
        if self._yolo is None:
            return None

        result = self._yolo.predict(
            source=str(image_path),
            conf=0.25,
            classes=[0],  # person
            verbose=False,
            device="cpu",
        )
        if not result:
            return None

        boxes = result[0].boxes
        if boxes is None or len(boxes) == 0:
            return None

        areas = []
        for box in boxes.xyxy.tolist():
            x1, y1, x2, y2 = [int(round(v)) for v in box]
            areas.append((max(0, x2 - x1) * max(0, y2 - y1), (x1, y1, x2, y2)))

        areas.sort(key=lambda x: x[0], reverse=True)
        return areas[0][1]

    def _remove_bg(self, crop: Image.Image) -> Optional[Image.Image]:
        try:
            from rembg import remove
        except Exception:
            return None

        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        cutout_data = remove(buf.getvalue())
        cutout = Image.open(io.BytesIO(cutout_data)).convert("RGBA")
        return cutout

    def process_single(self, image_path: Path, output_path: Path) -> bool:
        with Image.open(image_path) as im:
            im = im.convert("RGBA")
            width, height = im.size
            bbox = self._detect_person_bbox(image_path)
            if bbox is None:
                return False

            x1, y1, x2, y2 = bbox
            x1 = max(0, min(x1, width - 1))
            y1 = max(0, min(y1, height - 1))
            x2 = max(x1 + 1, min(x2, width))
            y2 = max(y1 + 1, min(y2, height))

            crop = im.crop((x1, y1, x2, y2))
            cutout = self._remove_bg(crop)
            if cutout is None:
                return False

            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            canvas.paste(cutout, (x1, y1), cutout)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output_path.with_suffix(".png"))
            return True


def collect_images(root: Path) -> List[Path]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    files.sort()
    return files


def choose_targets(files: Sequence[Path], random_enabled: bool, count: int) -> List[Path]:
    if not random_enabled:
        return list(files)

    count = max(0, count)
    if count >= len(files):
        return list(files)

    return random.sample(list(files), count)


def process_folder(config: ProcessConfig, progress_callback=None) -> ProcessStats:
    extractor = PersonExtractor()
    all_files = collect_images(config.input_dir)
    targets = choose_targets(all_files, config.random_pick_enabled, config.random_pick_count)

    stats = ProcessStats(total=len(targets))

    for index, image_path in enumerate(targets, start=1):
        rel = image_path.relative_to(config.input_dir)
        output_path = (config.output_dir / rel).with_suffix(".png")
        try:
            ok = extractor.process_single(image_path, output_path)
            if ok:
                stats.success += 1
            else:
                stats.skipped += 1
        except Exception:
            stats.failed += 1

        if progress_callback:
            progress_callback(index, stats.total, image_path.name, stats)

    return stats
