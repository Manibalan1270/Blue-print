"""Test setup.

The real embedding model (sentence-transformers, ~90MB download + PyTorch) is
replaced with a tiny word-hashing stand-in, so the tests run in seconds and
offline. Everything else - the endpoint, the risk engine, the translator and the
similarity logic - is the real code.
"""
import os
import sys
import types
import zlib

import numpy as np

os.environ["SKIP_MODEL_WARMUP"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if "sentence_transformers" not in sys.modules:
    fake = types.ModuleType("sentence_transformers")

    class SentenceTransformer:  # noqa: D401 - test double
        loads = 0

        def __init__(self, *args, **kwargs):
            SentenceTransformer.loads += 1

        def encode(self, texts, **kwargs):
            single = isinstance(texts, str)
            items = [texts] if single else list(texts)
            vectors = []
            for text in items:
                v = np.zeros(64)
                for word in str(text).lower().split():
                    v[zlib.crc32(word.encode()) % 64] += 1
                vectors.append(v)
            arr = np.array(vectors)
            return arr[0] if single else arr

    fake.SentenceTransformer = SentenceTransformer
    sys.modules["sentence_transformers"] = fake
