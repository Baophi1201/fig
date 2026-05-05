"""
Version checker - Kiểm tra và tự động cập nhật tool từ GitHub.

Luồng hoạt động:
  1. Fetch version.json từ GitHub
  2. Nếu version hiện tại < min_version → bắt buộc update (tự git pull + restart)
  3. Nếu version hiện tại < current_version → hỏi user có muốn update không
  4. Nếu không có mạng → cảnh báo rồi tiếp tục
"""
import os
import sys
import subprocess
import shutil
import zipfile
import io
import requests
from packaging import version

# ===================== CẤU HÌNH =====================
CURRENT_VERSION = "1.0.3"

# URL raw của file version.json trong repo GitHub
VERSION_URL = "https://raw.githubusercontent.com/Baophi1201/fig/main/version.json"
ZIP_URL = "https://github.com/Baophi1201/fig/archive/refs/heads/main.zip"
# ====================================================


def _download_and_update() -> bool:
    """
    Tải ZIP từ GitHub và giải nén để cập nhật tool.
    Không cần Git, chạy được trên mọi thiết bị.
    """
    try:
        print("📥 Đang tải bản mới...")

        response = requests.get(ZIP_URL, timeout=20)
        response.raise_for_status()

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            temp_dir = os.path.join(project_root, "temp_update")
            zip_ref.extractall(temp_dir)

        print("✅ Update thành công!")
        return True

    except Exception as e:
        print(f"❌ Update lỗi: {e}")
        return False


def _restart() -> None:
    """Restart lại process hiện tại với cùng arguments."""
    print("\n🔄  Đang khởi động lại tool...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def check_version() -> None:
    """
    Kiểm tra version với server GitHub.

    - version < min_version  → bắt buộc update, tự git pull rồi restart
    - version < current_version → hỏi user, nếu đồng ý thì git pull + restart
    - Không kết nối được     → cảnh báo nhẹ rồi tiếp tục
    """
    try:
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        min_ver = data.get("min_version", "0.0.0")
        latest_ver = data.get("current_version", CURRENT_VERSION)
        current = version.parse(CURRENT_VERSION)

        # ── Trường hợp 1: BẮT BUỘC update ──────────────────────────────────
        if current < version.parse(min_ver):
            print(
                f"\n🚫  Phiên bản v{CURRENT_VERSION} không còn được hỗ trợ.\n"
                f"    Phiên bản tối thiểu yêu cầu: v{min_ver}\n"
                f"    Tool sẽ tự động cập nhật ngay bây giờ...\n"
            )
            if _download_and_update():
                _restart()
            else:
                print(
                    "\n❌  Không thể tự cập nhật.\n"
                    "    Vui lòng tải bản mới thủ công từ GitHub.\n"
                    "    rồi mở lại tool.\n"
                )
                sys.exit(1)

        # ── Trường hợp 2: Có bản mới, hỏi user ─────────────────────────────
        if current < version.parse(latest_ver):
            print(
                f"\n🆕  Có phiên bản mới: v{latest_ver} "
                f"(bạn đang dùng v{CURRENT_VERSION})."
            )
            try:
                answer = input("    Cập nhật ngay? (Y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"

            if answer in ("", "y", "yes"):
                if _download_and_update():
                    _restart()
                else:
                    print("⚠️  Cập nhật thất bại. Tiếp tục với phiên bản cũ...\n")
            else:
                print("⚠️  Bỏ qua cập nhật. Tiếp tục...\n")

    except requests.exceptions.RequestException:
        print("⚠️  Không thể kiểm tra phiên bản (không có kết nối). Tiếp tục...\n")
    except Exception as e:
        print(f"⚠️  Lỗi kiểm tra phiên bản: {e}. Tiếp tục...\n")
