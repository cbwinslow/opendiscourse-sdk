import os
import unittest


class TestApiKeys(unittest.TestCase):
    def test_govinfo_api_key(self):
        key = os.getenv("GOVINFO_API_KEY")
        self.assertIsNotNone(key, "GOVINFO_API_KEY is not set")
        self.assertNotEqual(
            key, "YOUR_API_KEY_HERE", "GOVINFO_API_KEY uses placeholder"
        )

    def test_congress_api_key(self):
        key = os.getenv("CONGRESS_API_KEY")
        self.assertIsNotNone(key, "CONGRESS_API_KEY is not set")
        self.assertNotEqual(
            key, "YOUR_API_KEY_HERE", "CONGRESS_API_KEY uses placeholder"
        )


if __name__ == "__main__":
    unittest.main()
