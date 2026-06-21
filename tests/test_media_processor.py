from pathlib import Path
import tempfile
import unittest

from media_processor import ImageProcessor, KeywordAnalyzer, slugify


class StaticAnalyzer(KeywordAnalyzer):
    def __init__(self, words: list[str]) -> None:
        self.words = words

    def analyze(self, image_path: Path) -> list[str]:
        return self.words


class MediaProcessorTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("Blue Sky & Beach"), "blue-sky-beach")

    def test_destination_for_website(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            processor = ImageProcessor(Path(tmp), StaticAnalyzer(["demo"]))
            destination = processor.destination_for("Website")
            self.assertEqual(destination, Path(tmp) / "storage" / "website" / "photos")

    def test_destination_for_social_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            processor = ImageProcessor(Path(tmp), StaticAnalyzer(["demo"]))
            destination = processor.destination_for("Google Business")
            self.assertEqual(
                destination,
                Path(tmp) / "storage" / "photos" / "social-accounts" / "google-business",
            )

    def test_output_name_contains_keywords_and_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            processor = ImageProcessor(Path(tmp), StaticAnalyzer(["sea", "sunset", "sea"]))
            name = processor.build_output_name(Path("photo.jpg"), "webp", ["Instagram"])
            self.assertEqual(name, "sea-sunset-instagram-optimized.webp")


if __name__ == "__main__":
    unittest.main()
