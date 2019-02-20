import flippy
import unittest


class TestExample(unittest.TestCase):

    def test_example(self):
        print(flippy)
        self.assertIsInstance(flippy.version, str)
