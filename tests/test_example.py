import flippy
import unittest


class TestExample(unittest.TestCase):

    def test_example(self):
        self.assertIsInstance(flippy.version, str)
