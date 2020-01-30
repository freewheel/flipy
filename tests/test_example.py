import flipy
import unittest


class TestExample(unittest.TestCase):

    def test_example(self):
        self.assertIsInstance(flipy.version, str)
