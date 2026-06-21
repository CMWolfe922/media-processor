from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable, Sequence

from PIL import Image


RATIO_OPTIONS = {
    "Original": None,
    "1:1": (1, 1),
    "4:5": (4, 5),
    "16:9": (16, 9),
    "9:16": (9, 16),
    "1.91:1": (1.91, 1),
}

PLATFORM_RATIO_CHOICES = {
    "Facebook": ["1.91:1", "1:1", "4:5"],
    "Instagram": ["1:1", "4:5", "9:16"],
    "X": ["16:9", "1:1"],
    "Google Business": ["4:5", "1:1"],
    "Website": ["Original", "16:9", "1:1"],
}

SUPPORTED_PLATFORMS = ["Facebook", "Instagram", "X", "Website", "Google Business"]
DEFAULT_DOCKER_TIMEOUT_SECONDS = 30
MAX_UNIQUE_FILENAME_ATTEMPTS = 1000


def slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return value or "image"


class KeywordAnalyzer:
    def analyze(self, image_path: Path) -> list[str]:
        raise NotImplementedError


class DockerKeywordAnalyzer(KeywordAnalyzer):
    def __init__(
        self,
        docker_image: str = "seo-keyword-analyzer:latest",
        timeout_seconds: int = DEFAULT_DOCKER_TIMEOUT_SECONDS,
    ) -> None:
        self.docker_image = docker_image
        self.timeout_seconds = timeout_seconds

    def analyze(self, image_path: Path) -> list[str]:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{image_path.resolve()}:/input-image:ro",
            self.docker_image,
            "/input-image",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=True,
        )
        raw = result.stdout.strip()
        return [slugify(part) for part in re.split(r"[,\s]+", raw) if part.strip()]


class FilenameKeywordAnalyzer(KeywordAnalyzer):
    def analyze(self, image_path: Path) -> list[str]:
        return [slugify(token) for token in re.split(r"[^a-zA-Z0-9]+", image_path.stem) if token]


class SafeKeywordAnalyzer(KeywordAnalyzer):
    def __init__(self, primary: KeywordAnalyzer, fallback: KeywordAnalyzer) -> None:
        self.primary = primary
        self.fallback = fallback

    def analyze(self, image_path: Path) -> list[str]:
        try:
            terms = self.primary.analyze(image_path)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
            terms = []
        if not terms:
            terms = self.fallback.analyze(image_path)
        return [term for term in terms if term]


def center_crop_to_ratio(image: Image.Image, ratio: tuple[float, float]) -> Image.Image:
    width, height = image.size
    target_ratio = ratio[0] / ratio[1]
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))

    new_height = int(width / target_ratio)
    top = (height - new_height) // 2
    return image.crop((0, top, width, top + new_height))


@dataclass
class ImageProcessor:
    base_dir: Path
    analyzer: KeywordAnalyzer

    def destination_for(self, platform: str) -> Path:
        if platform == "Website":
            destination = self.base_dir / "storage" / "website" / "photos"
        else:
            destination = (
                self.base_dir
                / "storage"
                / "photos"
                / "social-accounts"
                / slugify(platform)
            )
        destination.mkdir(parents=True, exist_ok=True)
        return destination

    def build_output_name(
        self,
        image_path: Path,
        output_format: str,
        extra_keywords: Sequence[str] | None = None,
    ) -> str:
        keywords = list(self.analyzer.analyze(image_path))
        if extra_keywords:
            keywords.extend(extra_keywords)
        unique_keywords = list(dict.fromkeys([slugify(item) for item in keywords if item]))
        selected = unique_keywords[:8] or [slugify(image_path.stem)]
        return f"{'-'.join(selected)}-optimized.{output_format.lower()}"

    def process_images(
        self,
        image_paths: Iterable[Path],
        platform: str,
        ratio_label: str,
        output_format: str,
    ) -> list[Path]:
        destination = self.destination_for(platform)
        ratio = RATIO_OPTIONS.get(ratio_label)
        saved_files: list[Path] = []

        for image_path in image_paths:
            with Image.open(image_path) as image:
                edited = center_crop_to_ratio(image, ratio) if ratio else image.copy()
                if output_format.lower() in {"jpg", "jpeg", "webp"} and edited.mode not in {
                    "RGB",
                    "L",
                }:
                    edited = edited.convert("RGB")

                name = self.build_output_name(image_path, output_format, [platform])
                output_path = self._ensure_unique(destination / name)
                save_format = "JPEG" if output_format.lower() in {"jpg", "jpeg"} else output_format.upper()
                edited.save(output_path, format=save_format)
                saved_files.append(output_path)

        return saved_files

    def _ensure_unique(self, output_path: Path) -> Path:
        if not output_path.exists():
            return output_path
        counter = 2
        while counter <= MAX_UNIQUE_FILENAME_ATTEMPTS:
            candidate = output_path.with_name(f"{output_path.stem}-{counter}{output_path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
        raise OSError(f"Could not resolve a unique output name for {output_path}")
