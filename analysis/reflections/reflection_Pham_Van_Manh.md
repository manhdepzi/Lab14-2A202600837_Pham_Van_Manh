# Individual Reflection - Pham Van Manh

## Information

- Name: Pham Van Manh
- Student ID: 2A202600837
- Date: 2026-06-16
- Lab: Lab 14 - AI Evaluation Factory

## 1. My Contribution

In this lab, I focused on completing the end-to-end evaluation workflow:

- Generated a 50-case golden dataset with ground-truth document IDs.
- Implemented and validated retrieval metrics: Hit Rate and MRR.
- Used a multi-judge evaluation flow with two simulated judges: GPT-4o and Claude Sonnet.
- Ran regression testing between Agent V1 and Agent V2.
- Added a release gate based on quality, retrieval stability, and latency.
- Produced `reports/summary.json`, `reports/benchmark_results.json`, and the failure analysis report.

## 2. Technical Understanding

MRR measures how early the first correct retrieved document appears in the ranked results. Hit Rate measures whether at least one relevant document appears in the retrieved set. These two metrics are important because answer quality can only be trusted when retrieval quality is known.

Multi-judge consensus reduces the risk of trusting a single evaluator. Agreement Rate shows whether judges are aligned; when scores diverge too much, the system should use conflict handling or human review.

Regression testing is important for AI agents because a new prompt or retrieval change can improve one metric while silently hurting another. The release gate makes that trade-off explicit.

## 3. Challenges

The hardest part was connecting the benchmark pieces into a reliable pipeline. A checker can pass structurally while the actual benchmark quality is still weak. After reviewing the first run, the agent was improved so that it answered from the lab knowledge source instead of returning placeholder responses.

Another challenge was reproducibility. Randomized judge/retrieval simulation can make V1 and V2 look different even when the implementation is the same, so the benchmark now uses a deterministic seed.

## 4. Results

The final benchmark result passed all 50 cases:

- Average judge score: 4.814 / 5.0
- Hit Rate: 0.900
- MRR: 0.850
- Agreement Rate: 0.994
- Release Gate: APPROVE
- Total benchmark time: 2.59 seconds

## 5. Future Improvements

With more time, I would replace the simulated retrieval logic with a real vector database such as FAISS or ChromaDB, use embedding-based similarity, and add a third judge for conflict resolution. I would also expand the adversarial dataset to test prompt injection and out-of-scope behavior more deeply.
