import json
import unittest
from pathlib import Path

from PIL import Image


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "live2d"
    / "haru_greeter_t05"
    / "runtime"
    / "haru_greeter_t05.model3.json"
)


class Live2DTextureTests(unittest.TestCase):
    def test_model_references_existing_black_red_textures(self):
        model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        texture_paths = model["FileReferences"]["Textures"]

        self.assertEqual(
            texture_paths,
            [
                "haru_greeter_t05.2048/texture_00_black_red.png",
                "haru_greeter_t05.2048/texture_01_black_red.png",
            ],
        )
        for texture_path in texture_paths:
            self.assertTrue((MODEL_PATH.parent / texture_path).is_file())

    def test_iris_atlas_region_contains_recolored_red_pixels(self):
        texture_path = (
            MODEL_PATH.parent
            / "haru_greeter_t05.2048"
            / "texture_00_black_red.png"
        )
        hsv = Image.open(texture_path).convert("HSV")
        eye_region = hsv.crop((1450, 1120, 1741, 1321))
        red_pixels = sum(
            1
            for y in range(eye_region.height)
            for x in range(eye_region.width)
            for hue, saturation, value in (eye_region.getpixel((x, y)),)
            if (hue <= 8 or hue >= 247) and saturation > 90 and value > 45
        )

        self.assertGreater(red_pixels, 5000)


if __name__ == "__main__":
    unittest.main()
