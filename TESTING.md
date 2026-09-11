# Testing

From the repository root, run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/v2 -p test_runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/v2 -p test_media_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/qa -p test_qa.py
```

There are 27 runtime/export checks, 7 media-pipeline checks and 16 Q&A/model-reuse checks. Fixtures are synthetic; no company corpus, API credentials or model download is needed. FFmpeg must be on PATH to execute the real pipe/seek check; otherwise that check is skipped. Model reuse is mocked, not an acoustic-quality test.

Runtime tests cover source/quote validation, scope and record consistency, exports and archive integrity. Q&A tests cover directory/ZIP retrieval, raw-source details, pagination, duplicate origins, fallback search, cache separation and corruption handling. Media tests exercise decoding, interval and process handling.

## Development evidence

Astra medium completed manual research on a supplied Voliro account against Dalus context. Six same-session follow-up questions answered all core questions and explicitly covered 21 of 22 frozen checklist facets. The omitted facet was an ancillary explanation of PEC area-averaging, not a false claim. A natural follow-up question used retained evidence without being explicitly told to enter Q&A mode. Focused fresh-session Q&A checks were also completed during development.

These are small functional checks, not a research-accuracy benchmark or proof of performance across models. Two research runs followed different source branches, including a consequential discovered case-study lead not pursued in one run. The final coverage instruction was strengthened; a separate behavioral replay of that wording change was intentionally not run. Integrity verification does not establish complete coverage or publisher truth. Private research, answer keys and agent traces are not included in this repository.
