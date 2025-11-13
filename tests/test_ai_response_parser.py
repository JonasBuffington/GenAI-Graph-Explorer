import unittest

from app.services.ai_response_parser import parse_ai_response_text


class TestAIResponseParser(unittest.TestCase):
    def test_parses_code_fenced_json(self):
        raw = """```json
        {"nodes": [], "edges": []}
        ```"""
        parsed = parse_ai_response_text(raw)
        self.assertEqual(parsed, {"nodes": [], "edges": []})

    def test_escapes_problematic_backslashes(self):
        raw = r'{"nodes": [{"name": "Integral", "description": "Uses \_subscripts and \lambda"}], "edges": []}'
        parsed = parse_ai_response_text(raw)
        self.assertEqual(parsed["nodes"][0]["description"], "Uses \\_subscripts and \\lambda")

    def test_drops_thought_signature(self):
        raw = r'{"nodes": [], "edges": [], "thought-signature": {"id": "abc"}}'
        parsed = parse_ai_response_text(raw)
        self.assertNotIn("thought-signature", parsed)


if __name__ == "__main__":
    unittest.main()
