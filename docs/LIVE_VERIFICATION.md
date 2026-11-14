# NOVA live verification

**PARTIALLY READY.** Live Gemini and semantic persistence passed. Unity compilation and Play Mode integration are open because the playable Unity project and Editor were not located.

## Live HTTP results

Ran two scripted gameplay scenarios against a localhost Uvicorn backend using the existing `gemini-3.5-flash-lite` configuration and real hybrid retrieval. Used synthetic game state. The model received individual turns with current snapshots and a shared session ID. The backend does not retain dialogue history.

- M02 Oxygen Mystery, English. Mission start, oxygen warning, duplicate suppression, hints 0–3, a MOXIE science turn, a forbidden refill-control request, recovery and completion.
- M03 dust storm, Egyptian Arabic. Mission start, dust warning, two NASA science questions, a direct allowed action, a question containing an unsupported NASA measurement, storm end and mission completion.
- All 10 final chat turns returned Gemini output with no fallback. Six English turns took 1.03–1.81 s and four Arabic turns took 1.10–1.40 s. Across all turns the median was 1.10 s and the range was 1.03–1.81 s. Timings are full HTTP round trips including retrieval, Gemini and response validation. No production percentile is inferred from ten samples.
- The MOXIE explanation was supported by the MOXIE excerpt. Both Arabic dust explanations were supported by SOLAR_DUST. These are curated NASA-attributed summaries. The unsupported measurement turn expressed uncertainty but added an unrelated MOXIE fact, so relevance on unsupported premises remains imperfect.
- Level 0 noted the readings/status, level 1 pointed to power sharing, level 2 explained the oxygen plant's power dependency, and level 3 suggested the exact allowed action. Only the two direct-action cases returned a structured suggestion. The request for a fabricated refill control was rejected in the dialogue. The backend enforces exact allowlist membership on the structured field. Free-text adherence was manually sampled.
- The live runs uncovered unsupported causal claims, invented units, weak Arabic retrieval and invalid JSON. Changes clarified state and science evidence, added Arabic retrieval aliases and preserved a science candidate in mixed retrieval, and sent the existing dialogue schema to Gemini with a larger output budget. The final run produced no unsupported power conversion or confirmed lab-cause claim.

## Semantic persistence

An isolated real Chroma 1.5.9 store used the cached multilingual MiniLM model through sentence-transformers 5.7.0. The fresh process embedded 323 documents in six batches, producing 384-dimensional vectors. On subsequent full backend restarts, health reported hybrid mode. The identical collection reopened with 323 vectors and zero document-embedding calls. The probe returned the same top three vector IDs in the same order with identical cosine distances. The initial model/index/probe took 5.68 s after imports. The final restart reached healthy HTTP in 4.27 s. The raw Arabic vector probe favored game chunks above the distance cutoff, so Arabic NASA citations also relied on the improved lexical path.

The project's default BM25 setting and persistent indexes were left in place. To reproduce hybrid mode in the project's environment, install `requirements-semantic.txt` into that environment and run with `NOVA_ENABLE_SEMANTIC=true`.

## Regression and remaining verification

44 tests passed, 0 failed, 0 skipped. The environment emitted one existing Starlette TestClient deprecation warning. The model samples establish behavior on these test turns. They do not establish broad child-safety, scientific factuality or resistance to all instruction attacks. See UNITY_EDITOR_VERIFICATION.md for the remaining Editor acceptance procedure.
