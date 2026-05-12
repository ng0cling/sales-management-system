"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: csv_export.py
CSV export helper — được gọi từ GUI khi user bấm nút Export.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime


EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


def export_csv(filename: str, rows: list[dict]) -> str:
    """
    Ghi danh sách dict ra file CSV trong thư mục exports/.

    Trả về đường dẫn file nếu thành công, chuỗi rỗng nếu không có data.

    Dùng encoding utf-8-sig để Excel (Windows) đọc được tiếng Việt.
    """
    if not rows:
        return ""

    # Thêm timestamp vào tên file để tránh ghi đè
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    timestamped = f"{name}_{timestamp}{ext or '.csv'}"
    path = os.path.join(EXPORT_DIR, timestamped)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return path