from pathlib import Path
import tempfile
import unittest

from PIL import Image

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
            self.assertEqual(name.split("-").count("sea"), 1)

    def test_output_name_limits_to_eight_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keywords = [f"term{i}" for i in range(1, 11)]
            processor = ImageProcessor(Path(tmp), StaticAnalyzer(keywords))
            name = processor.build_output_name(Path("photo.jpg"), "png")
            self.assertEqual(
                name,
                "term1-term2-term3-term4-term5-term6-term7-term8-optimized.png",
            )

    def test_process_images_crops_and_saves_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.png"
            Image.new("RGB", (1200, 800), "blue").save(source)

            processor = ImageProcessor(tmp_path, StaticAnalyzer(["beach", "sunset"]))
            output_files = processor.process_images(
                image_paths=[source],
                platform="Instagram",
                ratio_label="1:1",
                output_format="jpg",
            )

            self.assertEqual(len(output_files), 1)
            self.assertTrue(output_files[0].exists())
            with Image.open(output_files[0]) as result:
                self.assertEqual(result.size, (800, 800))


if __name__ == "__main__":
    unittest.main()
