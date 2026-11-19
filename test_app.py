import unittest

from app import apply_screen, review


class ReviewTests(unittest.TestCase):
    def test_empty_input_goes_to_manual_and_clears_draft(self):
        status, body = review("   ")
        screen = apply_screen("старый черновик", status, body)

        self.assertEqual(status, 422)
        self.assertEqual(body["reason"], "empty_input")
        self.assertEqual(screen["draft"], "")
        self.assertTrue(screen["manual"])

    def test_timeout_goes_to_manual_and_clears_draft(self):
        status, body = review("заявка таймаут")
        screen = apply_screen("старый черновик", status, body)

        self.assertEqual(status, 504)
        self.assertEqual(body["reason"], "timeout")
        self.assertEqual(screen["draft"], "")
        self.assertTrue(screen["manual"])

    def test_blank_model_json_is_not_a_ready_draft(self):
        status, body = review("битый ответ модели")
        screen = apply_screen("старый черновик", status, body)

        self.assertEqual(status, 422)
        self.assertEqual(body["reason"], "invalid_ai")
        self.assertEqual(body["draft"], "")
        self.assertEqual(screen["draft"], "")
        self.assertTrue(screen["manual"])

    def test_valid_reply_replaces_previous_draft(self):
        status, body = review("клиент не получил квитанцию")
        screen = apply_screen("старый черновик", status, body)

        self.assertEqual(status, 200)
        self.assertFalse(screen["manual"])
        self.assertIn("квитанцию", screen["draft"])


if __name__ == "__main__":
    unittest.main()
