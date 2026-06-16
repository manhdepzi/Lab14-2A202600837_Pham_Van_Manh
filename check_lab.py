import json
import os
import sys


def _ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def validate_lab():
    _ensure_utf8_stdout()
    print("🔍 Đang kiểm tra định dạng bài nộp...")

    required_files = [
        "reports/summary.json",
        "reports/benchmark_results.json",
        "analysis/failure_analysis.md",
    ]

    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Tìm thấy: {file_path}")
        else:
            print(f"❌ Thiếu file: {file_path}")
            missing.append(file_path)

    if missing:
        print(f"\n❌ Thiếu {len(missing)} file. Hãy bổ sung trước khi nộp bài.")
        return

    try:
        with open("reports/summary.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"❌ File reports/summary.json không phải JSON hợp lệ: {exc}")
        return

    if "metrics" not in data or "metadata" not in data:
        print("❌ File summary.json thiếu trường 'metrics' hoặc 'metadata'.")
        return

    metrics = data["metrics"]

    print("\n--- Thống kê nhanh ---")
    print(f"Tổng số cases: {data['metadata'].get('total', 'N/A')}")
    print(f"Điểm trung bình: {metrics.get('avg_score', 0):.2f}")

    if "hit_rate" in metrics:
        print(f"✅ Đã tìm thấy Retrieval Metrics (Hit Rate: {metrics['hit_rate'] * 100:.1f}%)")
    else:
        print("⚠️ CẢNH BÁO: Thiếu Retrieval Metrics (hit_rate).")

    if "agreement_rate" in metrics:
        print(f"✅ Đã tìm thấy Multi-Judge Metrics (Agreement Rate: {metrics['agreement_rate'] * 100:.1f}%)")
    else:
        print("⚠️ CẢNH BÁO: Thiếu Multi-Judge Metrics (agreement_rate).")

    if data["metadata"].get("version"):
        print("✅ Đã tìm thấy thông tin phiên bản Agent (Regression Mode)")

    print("\n🚀 Bài lab đã sẵn sàng để chấm điểm!")


if __name__ == "__main__":
    validate_lab()
