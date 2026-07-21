import os

# Tests are offline and deterministic; production defaults to GPT-5.6 when a key exists.
os.environ["NALMAI_LLM_MODE"] = "demo"
os.environ["NALMAI_MEMORY_MODE"] = "off"
