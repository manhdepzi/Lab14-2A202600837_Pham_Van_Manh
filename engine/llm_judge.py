"""
llm_judge.py - Multi-Judge Consensus Engine
Sử dụng ít nhất 2 Judge model để đánh giá câu trả lời của Agent.
Tính Agreement Rate và xử lý xung đột điểm số tự động.
"""

import asyncio
import random
from typing import Dict, Any, List


# -------------------------------------------------------------------
# Rubrics chấm điểm (thang 1-5) cho từng tiêu chí
# -------------------------------------------------------------------
RUBRICS = {
    "accuracy": {
        5: "Câu trả lời hoàn toàn chính xác, trả lời đầy đủ câu hỏi và phù hợp với Ground Truth.",
        4: "Câu trả lời chính xác, có thể thiếu một vài chi tiết nhỏ không quan trọng.",
        3: "Câu trả lời tương đối đúng nhưng thiếu thông tin hoặc có điểm chưa chính xác nhỏ.",
        2: "Câu trả lời có một số thông tin đúng nhưng sai lệch đáng kể so với Ground Truth.",
        1: "Câu trả lời sai hoàn toàn, không liên quan hoặc là Hallucination.",
    },
    "faithfulness": {
        5: "Câu trả lời hoàn toàn dựa trên context, không có thông tin bịa đặt.",
        4: "Hầu hết dựa trên context, có thể có suy luận nhỏ nhưng hợp lý.",
        3: "Dựa phần lớn vào context nhưng có một vài thông tin không xác minh được.",
        2: "Có dấu hiệu Hallucination, một số thông tin không có trong context.",
        1: "Hallucination nghiêm trọng: phần lớn thông tin không có trong context.",
    },
    "relevancy": {
        5: "Câu trả lời rất liên quan, trực tiếp trả lời câu hỏi được đặt ra.",
        4: "Câu trả lời liên quan, có thể có một chút thông tin thừa.",
        3: "Câu trả lời liên quan một phần, có thể lạc đề ở một số chỗ.",
        2: "Câu trả lời ít liên quan, không trực tiếp trả lời câu hỏi.",
        1: "Câu trả lời không liên quan đến câu hỏi.",
    },
    "professionalism": {
        5: "Ngôn ngữ rất chuyên nghiệp, lịch sự, phù hợp với môi trường doanh nghiệp.",
        4: "Ngôn ngữ chuyên nghiệp, có thể có chút không trang trọng nhưng chấp nhận được.",
        3: "Ngôn ngữ tương đối ổn, có một vài điểm cần cải thiện về sự chuyên nghiệp.",
        2: "Ngôn ngữ không phù hợp, quá thân mật hoặc thiếu lịch sự.",
        1: "Ngôn ngữ hoàn toàn không chuyên nghiệp, thô lỗ hoặc không phù hợp.",
    },
}


class LLMJudge:
    """
    Judge đơn lẻ mô phỏng một LLM model đánh giá câu trả lời.
    Trong production, đây sẽ gọi API thực tế (OpenAI, Anthropic, v.v.)
    """

    def __init__(self, model: str = "gpt-4o", bias_offset: float = 0.0):
        """
        Args:
            model: Tên model Judge.
            bias_offset: Offset nhỏ để mô phỏng sự khác biệt giữa các model
                         (ví dụ: GPT-4o có xu hướng chặt hơn Claude một chút).
        """
        self.model = model
        self.rubrics = RUBRICS
        self.bias_offset = bias_offset  # GPT-4o chặt hơn Claude một chút

    def _compute_score_from_text(self, answer: str, ground_truth: str) -> Dict[str, float]:
        """
        Mô phỏng scoring logic của một LLM Judge dựa trên so sánh văn bản.
        Trong production: gọi LLM API với rubrics prompt.
        """
        if not answer or not ground_truth:
            return {"accuracy": 1.0, "faithfulness": 1.0, "relevancy": 1.0, "professionalism": 3.0}

        answer_lower = answer.lower()
        gt_lower = ground_truth.lower()

        # --- Accuracy score ---
        # Tính dựa trên tỉ lệ từ khóa chính trong ground_truth xuất hiện trong answer
        gt_keywords = set(gt_lower.split()) - {"là", "của", "và", "trong", "đến", "cho", "với", "một", "các", "có", "được", "này", "những"}
        if gt_keywords:
            matched = sum(1 for kw in gt_keywords if kw in answer_lower)
            overlap_ratio = matched / len(gt_keywords)
        else:
            overlap_ratio = 0.5

        accuracy = min(5, max(1, round(1 + overlap_ratio * 4 + self.bias_offset)))

        # --- Faithfulness score ---
        # Nếu answer rất dài so với ground truth -> có thể hallucinate
        len_ratio = len(answer) / max(len(ground_truth), 1)
        if len_ratio > 3:
            faithfulness = max(1, accuracy - 1)
        elif "không có trong" in answer_lower or "tôi không biết" in answer_lower:
            faithfulness = max(1, accuracy - 1)  # Từ chối trả lời -> faithfulness thấp hơn
        else:
            faithfulness = min(5, accuracy + random.choice([-1, 0, 0, 1]))

        # --- Relevancy score ---
        relevancy = min(5, max(1, accuracy + random.choice([-1, 0, 0])))

        # --- Professionalism score ---
        informal_phrases = ["bịa", "hack", "độc hại", "xỏ lá", "dối trá"]
        if any(p in answer_lower for p in informal_phrases):
            professionalism = random.randint(1, 2)
        else:
            professionalism = random.randint(4, 5)

        return {
            "accuracy": float(accuracy),
            "faithfulness": float(faithfulness),
            "relevancy": float(relevancy),
            "professionalism": float(professionalism),
        }

    async def judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Gọi Judge để chấm điểm một câu trả lời.

        Returns:
            Dict chứa scores, reasoning, và model name.
        """
        # Mô phỏng latency của API call
        await asyncio.sleep(random.uniform(0.05, 0.2))

        scores = self._compute_score_from_text(answer, ground_truth)
        final_score = (
            scores["accuracy"] * 0.4
            + scores["faithfulness"] * 0.3
            + scores["relevancy"] * 0.2
            + scores["professionalism"] * 0.1
        )

        reasoning = (
            f"[{self.model}] Accuracy={scores['accuracy']}/5, "
            f"Faithfulness={scores['faithfulness']}/5, "
            f"Relevancy={scores['relevancy']}/5, "
            f"Professionalism={scores['professionalism']}/5. "
            f"Weighted final={final_score:.2f}/5."
        )

        return {
            "model": self.model,
            "scores": scores,
            "final_score": round(final_score, 2),
            "reasoning": reasoning,
        }


class MultiModelJudge:
    """
    Multi-Judge Consensus Engine: dùng ít nhất 2 model Judge khác nhau.
    Tính Agreement Rate và xử lý xung đột tự động.
    """

    CONFLICT_THRESHOLD = 1.0  # Nếu lệch > 1.0 điểm thì coi là conflict

    def __init__(self):
        # Khởi tạo 2 Judge với độ lệch nhỏ để mô phỏng thực tế
        self.judges: List[LLMJudge] = [
            LLMJudge(model="gpt-4o", bias_offset=-0.2),      # GPT-4o nghiêm khắc hơn
            LLMJudge(model="claude-3-5-sonnet", bias_offset=0.2),  # Claude hào phóng hơn chút
        ]

    def _compute_agreement_rate(self, scores: List[float]) -> float:
        """
        Tính Agreement Rate dựa trên độ chênh lệch điểm số.
        - Lệch <= 0.5 điểm: đồng ý cao (1.0)
        - Lệch <= 1.0 điểm: đồng ý vừa (0.7)
        - Lệch > 1.0 điểm: xung đột (0.3)
        """
        if len(scores) < 2:
            return 1.0
        max_diff = max(scores) - min(scores)
        if max_diff <= 0.5:
            return 1.0
        elif max_diff <= 1.0:
            return 0.7
        else:
            return 0.3

    def _resolve_conflict(self, results: List[Dict[str, Any]]) -> float:
        """
        Xử lý xung đột khi các Judge lệch nhau quá nhiều.
        Chiến lược: lấy điểm thấp hơn (conservative approach) để đảm bảo an toàn.
        """
        scores = [r["final_score"] for r in results]
        # Conservative: lấy điểm thấp hơn trong trường hợp conflict
        return min(scores)

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        """
        Gọi tất cả Judge song song, tổng hợp kết quả và xử lý xung đột.

        Returns:
            Dict chứa final_score, agreement_rate, individual_scores, reasoning, conflict_detected.
        """
        # Chạy tất cả Judge song song (async)
        tasks = [judge.judge(question, answer, ground_truth) for judge in self.judges]
        results = await asyncio.gather(*tasks)

        individual_scores = {r["model"]: r["final_score"] for r in results}
        scores_list = list(individual_scores.values())

        agreement_rate = self._compute_agreement_rate(scores_list)
        conflict_detected = agreement_rate < 0.5  # Conflict nếu lệch > 1.0

        if conflict_detected:
            # Xử lý xung đột: dùng conservative approach (min)
            final_score = self._resolve_conflict(results)
            resolution_method = "conservative_min"
        else:
            # Đồng thuận: lấy trung bình
            final_score = sum(scores_list) / len(scores_list)
            resolution_method = "average"

        combined_reasoning = " | ".join(r["reasoning"] for r in results)

        return {
            "final_score": round(final_score, 2),
            "agreement_rate": round(agreement_rate, 2),
            "individual_scores": individual_scores,
            "conflict_detected": conflict_detected,
            "resolution_method": resolution_method,
            "reasoning": combined_reasoning,
            "judges_count": len(self.judges),
        }

    async def check_position_bias(
        self, response_a: str, response_b: str, question: str = "", ground_truth: str = ""
    ) -> Dict[str, Any]:
        """
        Kiểm tra Position Bias: đổi thứ tự response A và B, chạy lại Judge.
        Nếu kết quả thay đổi đáng kể, hệ thống bị Position Bias.
        """
        # Chạy với thứ tự ban đầu
        result_ab = await self.evaluate_multi_judge(question, response_a, ground_truth)
        # Chạy với thứ tự đảo ngược
        result_ba = await self.evaluate_multi_judge(question, response_b, ground_truth)

        score_diff = abs(result_ab["final_score"] - result_ba["final_score"])
        has_position_bias = score_diff > 0.5

        return {
            "order_ab_score": result_ab["final_score"],
            "order_ba_score": result_ba["final_score"],
            "score_difference": round(score_diff, 2),
            "has_position_bias": has_position_bias,
            "bias_severity": "high" if score_diff > 1.0 else ("medium" if score_diff > 0.5 else "low"),
        }


# -------------------------------------------------------------------
# Test nhanh
# -------------------------------------------------------------------
if __name__ == "__main__":
    async def demo():
        judge = MultiModelJudge()

        question = "RAGAS đo những chỉ số gì?"
        answer = "RAGAS đo Faithfulness, Answer Relevancy, Context Recall và Context Precision."
        ground_truth = "RAGAS đo Faithfulness, Answer Relevancy, Context Recall và Context Precision."

        result = await judge.evaluate_multi_judge(question, answer, ground_truth)
        print("=== Multi-Judge Result ===")
        print(f"Final Score:     {result['final_score']}/5.0")
        print(f"Agreement Rate:  {result['agreement_rate']}")
        print(f"Conflict:        {result['conflict_detected']}")
        print(f"Individual:      {result['individual_scores']}")
        print(f"Resolution:      {result['resolution_method']}")

        # Kiểm tra position bias
        bias_result = await judge.check_position_bias(answer, "Câu trả lời khác không liên quan.", question, ground_truth)
        print("\n=== Position Bias Check ===")
        print(f"Bias Detected:   {bias_result['has_position_bias']}")
        print(f"Severity:        {bias_result['bias_severity']}")

    asyncio.run(demo())
