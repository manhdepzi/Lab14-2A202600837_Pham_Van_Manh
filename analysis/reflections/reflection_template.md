# Individual Reflection - Nguyễn Kim Hoàng

## Thông tin
- **Họ và tên**: Nguyễn Kim Hoàng
- **Mã sinh viên**: 2A202600987
- **Ngày**: 2026-06-16
- **Lab**: Lab 14 — AI Evaluation Factory (Team Edition)

---

## 1. Tôi đã làm gì trong buổi Lab này?

Trong buổi Lab 14, tôi đã tham gia xây dựng toàn bộ hệ thống **AI Evaluation Factory** từ đầu, bao gồm:

**Giai đoạn 1 — Thiết kế Golden Dataset (SDG):**
- Viết lại script `data/synthetic_gen.py` để tự động sinh **50 test cases** chất lượng cao.
- Thiết kế 5 loại câu hỏi đa dạng: Fact-check (20), Reasoning (12), Edge-case (8), Adversarial (5), Multi-turn (3), Multi-hop (2).
- Đảm bảo mỗi test case có `ground_truth_id` để phục vụ tính toán Hit Rate trong Retrieval Evaluation.

**Giai đoạn 2 — Multi-Judge Consensus Engine:**
- Cài đặt `engine/llm_judge.py` với **2 Judge model** giả lập: `gpt-4o` (nghiêm khắc hơn) và `claude-3-5-sonnet` (hào phóng hơn).
- Xây dựng logic tính **Agreement Rate** dựa trên độ chênh lệch điểm số giữa 2 Judge.
- Xử lý xung đột tự động: nếu chênh lệch > 1.0 điểm → dùng **Conservative Min** (lấy điểm thấp hơn để an toàn).
- Cài đặt thêm hàm `check_position_bias()` để phát hiện thiên lệch theo vị trí.

**Giai đoạn 3 — Benchmark Runner & Release Gate:**
- Xây dựng lớp `ExpertEvaluator` trong `main.py` để tính:
  - **Faithfulness** (độ trung thành với context)
  - **Answer Relevancy** (độ liên quan với câu hỏi)
  - **Hit Rate & MRR** (đánh giá Retrieval stage)
- Cài đặt `CostTracker` để theo dõi chi phí token và ước tính tiết kiệm khi dùng model routing.
- Xây dựng **Release Gate** logic: tự động quyết định APPROVE hoặc ROLLBACK dựa trên delta score, hit rate, và latency.

**Giai đoạn 4 — Báo cáo & Kiểm tra:**
- Chạy toàn bộ pipeline, sinh ra `reports/summary.json` và `reports/benchmark_results.json`.
- Hoàn thiện `analysis/failure_analysis.md` với phân tích 5 Whys cho 3 case tệ nhất.
- Xác nhận `python check_lab.py` PASS tất cả tiêu chí.

---

## 2. Điều tôi học được

### Về kỹ thuật AI Evaluation

- **RAGAS framework**: Hiểu rõ sự khác biệt giữa các metric — **Faithfulness** đo xem agent có "bịa" thông tin không (tức hallucination), còn **Answer Relevancy** đo xem câu trả lời có thực sự trả lời đúng câu hỏi không. Hai metric này đo hai lỗi hoàn toàn khác nhau.

- **Retrieval phải được đánh giá riêng**: Trước Lab này, tôi nghĩ chỉ cần nhìn vào điểm trả lời của agent là đủ. Nhưng qua Lab này tôi nhận ra: nếu **Hit Rate thấp** (agent không lấy được đúng tài liệu), thì dù generation có giỏi đến đâu cũng thất bại. Đây là bài học về "đừng chẩn đoán sai tầng gây lỗi".

- **Multi-Judge giảm thiên lệch**: Một Judge duy nhất (dù là GPT-4o) có thể có *systematic bias* — ví dụ luôn cho điểm cao với câu trả lời dài. Dùng 2 Judge khác nhau và so sánh Agreement Rate giúp phát hiện bias này.

- **Async programming thực chiến**: Dùng `asyncio.gather()` để chạy 50 test cases song song, tốc độ từ ~25 giây tuần tự xuống còn **7 giây** — cải thiện 3.5x. Đây là yêu cầu bắt buộc cho hệ thống Eval trong sản xuất.

### Về quy trình phát triển AI

- **Không nên nhìn vào điểm tổng hợp mà bỏ qua chi tiết**: avg_score = 2.0/5.0 không nói được gì nhiều. Phải nhìn vào phân nhóm lỗi (Hallucination vs Low Relevancy vs Adversarial Bypass) mới biết cần sửa ở đâu.

- **5 Whys là công cụ cực kỳ hiệu quả**: Thay vì kết luận "agent trả lời sai", phương pháp 5 Whys buộc tôi đào sâu hơn để tìm ra nguyên nhân gốc rễ — ví dụ lỗi không phải ở LLM mà ở **Chunking strategy** hoặc **thiếu Safety Layer**.

- **Release Gate là văn hóa DevOps quan trọng**: Tự động hóa quyết định APPROVE/ROLLBACK dựa trên dữ liệu cụ thể, không để quyết định phát hành phụ thuộc vào cảm tính của developer.

---

## 3. Điều tôi thấy khó nhất

**1. Thiết kế rubrics đánh giá chất lượng:**
Rất khó định nghĩa ngưỡng cụ thể cho "đủ tốt". Ví dụ: Faithfulness = 0.7 là tốt hay tệ? Phụ thuộc vào domain và use case. Không có con số tuyệt đối, cần kinh nghiệm từ nhiều lần benchmark.

**2. Xử lý conflict giữa các Judge:**
Khi GPT-4o cho 4/5 và Claude cho 2/5 (chênh 2 điểm), nên tin Judge nào? Tôi đã chọn **Conservative Min** (lấy điểm thấp nhất) nhưng đây chỉ là một chiến lược. Trong thực tế có thể cần Judge thứ 3 (tie-breaker) hoặc human review.

**3. Phân biệt lỗi Retrieval với lỗi Generation:**
Khi agent cho câu trả lời sai, khó biết ngay đó là do Retrieval lấy sai document, hay do Generation không đọc đúng document. Phải đo song song cả Hit Rate và Faithfulness mới có thể phân loại được.

---

## 4. Nếu có thêm thời gian, tôi sẽ cải thiện

- [ ] **Tích hợp Vector DB thực tế** (ChromaDB hoặc FAISS) thay cho mock Retrieval — đây là cải tiến quan trọng nhất, sẽ đưa Faithfulness từ 0.17 lên ~0.75+.
- [ ] **Embedding model thực** (`text-embedding-3-small` của OpenAI) để tính cosine similarity thực sự cho Hit Rate và MRR chính xác.
- [ ] **Semantic Chunking** thay vì Fixed-size — dự kiến tăng Hit Rate từ 86% lên 92%+.
- [ ] **Reranking layer** (cross-encoder model) sau bước retrieval để cải thiện MRR.
- [ ] **Position Bias detection** đầy đủ: swap response A/B, chạy lại Judge, so sánh kết quả.
- [ ] **Cost Routing thực tế**: phân loại độ khó câu hỏi tự động, route easy cases sang `gpt-4o-mini` để tiết kiệm 56% chi phí.
- [ ] **Thêm 50 adversarial cases** phức tạp hơn: multi-hop reasoning, conflicting information, ambiguous questions.

---

## 5. Câu hỏi mở

> **Câu hỏi 1:** Khi Agreement Rate của 2 Judge chỉ đạt 0.3 (conflict cao), kết quả Eval có còn đáng tin không? Hay cần bắt buộc có Human-in-the-loop review những case conflict này trước khi đưa vào Release Gate?

> **Câu hỏi 2:** Trong thực tế sản xuất, tần suất chạy Benchmark nên là bao nhiêu? Chạy mỗi commit (CI/CD) có quá tốn kém không khi dataset lớn? Có nên dùng subset nhỏ hơn cho "fast check" và full dataset cho "release check" không?

> **Câu hỏi 3:** Faithfulness của hệ thống mock chỉ đạt 0.168 — nhưng sau khi tích hợp RAG thực tế, Faithfulness kỳ vọng sẽ đạt bao nhiêu là "production-ready"? Ngưỡng 0.8 có phải là tiêu chuẩn ngành không?

---

## 6. Kết luận cá nhân

Lab 14 là một trong những Lab thực tế nhất tôi từng làm — nó không chỉ dạy cách *đo* chất lượng AI mà còn dạy cách *suy nghĩ hệ thống* về toàn bộ pipeline từ Ingestion → Chunking → Retrieval → Generation → Evaluation.

Bài học lớn nhất: **"Nếu bạn không thể đo lường nó, bạn không thể cải thiện nó."** Và đo lường đúng nghĩa là phải đo từng bước trong pipeline, không chỉ đo kết quả cuối.
