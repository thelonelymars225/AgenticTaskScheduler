"""Fast, reliability-first Ollama code-generation pipeline."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ollama

from timer import Timer

CLIENT = ollama.Client()
PRIMARY_MODEL = os