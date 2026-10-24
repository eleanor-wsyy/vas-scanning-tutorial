import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "skills/vas-scanning/scripts/preflight.py"
spec = importlib.util.spec_from_file_location("preflight", SCRIPT)
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def image(self, name="photo.png", size=(800, 600), mode="RGB"):
        path = self.root / name
        Image.new(mode, size).save(path)
        return path

    def test_valid_rgb_unchanged(self):
        path = self.image()
        before = path.read_bytes()
        item = pf.inspect_image(path)
        self.assertTrue(item["meets_recommended_dimensions"])
        self.assertEqual(item["warnings"], [])
        self.assertEqual(item["errors"], [])
        self.assertEqual(item["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(path.read_bytes(), before)

    def test_short_dimension_warns(self):
        item = pf.inspect_image(self.image(size=(2400, 400)))
        self.assertFalse(item["meets_recommended_dimensions"])
        self.assertTrue(item["warnings"])
        self.assertFalse(item["errors"])

    def test_transparency(self):
        item = pf.inspect_image(self.image(mode="RGBA"))
        self.assertEqual(item["color_mode"], "RGBA")
        self.assertTrue(any("background" in w for w in item["warnings"]))

    def test_cmyk_not_converted(self):
        path = self.image("print.jpg", mode="CMYK")
        self.assertEqual(pf.inspect_image(path)["color_mode"], "CMYK")
        with Image.open(path) as im:
            self.assertEqual(im.mode, "CMYK")

    def test_exif_orientation(self):
        path = self.root / "rotated.jpg"
        im = Image.new("RGB", (800, 600))
        exif = im.getexif()
        exif[274] = 6
        im.save(path, exif=exif)
        item = pf.inspect_image(path)
        self.assertEqual(item["exif_orientation"], 6)
        self.assertTrue(any("orientation" in w for w in item["warnings"]))

    def test_corrupt_and_missing(self):
        broken = self.root / "broken.png"
        broken.write_bytes(b"not a png")
        for path in [broken, self.root / "missing.jpg"]:
            self.assertTrue(pf.inspect_image(path)["errors"])

    def test_duplicate_bytes(self):
        first = self.image()
        second = self.root / "copy.png"
        second.write_bytes(first.read_bytes())
        manifest = pf.build_manifest([first, second])
        self.assertEqual(manifest["images"][1]["duplicate_of_index"], 0)
        self.assertTrue(manifest["visual_review_required"])

    def test_cli_refuses_overwrite(self):
        out = self.root / "manifest.json"
        out.write_text("keep", encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.image()), "--output", str(out)], capture_output=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(out.read_text(encoding="utf-8"), "keep")

    def test_cli_exit_codes(self):
        good = subprocess.run([sys.executable, str(SCRIPT), str(self.image())], capture_output=True)
        bad = subprocess.run([sys.executable, str(SCRIPT), str(self.root / "missing.png")], capture_output=True)
        self.assertEqual(good.returncode, 0)
        self.assertEqual(bad.returncode, 1)

if __name__ == "__main__":
    unittest.main()
