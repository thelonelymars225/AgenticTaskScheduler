"""Tests for the bounded optional DeepSeek escalation role."""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from inference import deepseek_api


class DeepSeekEscalationTests(unittest.TestCase):
    def tearDown(self) -> None:
        deepseek_api._CLIENT = None

    def test_missing_key_is_not_available(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(deepseek_api.available())

    def test_repair_extracts_source_and_records_usage(self) -> None:
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="```python\nvalue = 2\n```"))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4),
        )
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
        )
        events: list[dict[str, object]] = []
        with patch.object(deepseek_api, "_CLIENT", client):
            repaired = deepseek_api.repair_code("value = 1", "contract", ["wrong value"], record_call=events.append)
        self.assertEqual(repaired, "value = 2")
        self.assertEqual(events[0]["prompt_tokens"], 10)
        self.assertEqual(events[0]["output_tokens"], 4)

    def test_generate_extracts_source_and_records_usage(self) -> None:
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="```python\nprint('ok')\n```"))],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=6),
        )
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))
        )
        events: list[dict[str, object]] = []
        with patch.object(deepseek_api, "_CLIENT", client):
            generated = deepseek_api.generate_code("say ok", "contract", record_call=events.append)
        self.assertEqual(generated, "print('ok')")
        self.assertEqual(events[0]["model"], "deepseek-api:deepseek-chat")
