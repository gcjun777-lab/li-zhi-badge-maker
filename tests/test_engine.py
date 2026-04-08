from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from li_zhi_badge_maker.engine import render_badge
from li_zhi_badge_maker.models import BadgeRecord


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class EngineTestCase(unittest.TestCase):
    def test_render_badge_with_example_image(self) -> None:
        record = BadgeRecord(
            image_path=str(PROJECT_ROOT / "examples" / "input_images" / "冯兵.png"),
            name="冯兵",
            join_date="2022-12-02",
            days="1193",
            output_name="冯兵-离职厂牌-.png",
        )
        image = render_badge(record)
        self.assertEqual(image.size, (319, 508))

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / record.output_name
            image.save(target)
            self.assertTrue(target.exists())
            self.assertGreater(target.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
