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
import requests
from packaging import version

# ===================== CẤU HÌNH =====================
CURRENT_VERSION = "1.0.2"

# URL raw của file version.json trong repo GitHub
VERSION_URL = "https://raw.githubusercontent.com/Baophi1201/fig/main/version.json"
# ====================================================


def _run_git_pull() -> bool:
    """
    Chạy git pull để lấy code mới nhất.
    Trả về True nếu thành công, False nếu thất bại.
    """
    if not shutil.which("git"):
        print("⚠ Git chưa được cài trên thiết bị.")
        print("Vui lòng tải lại tool từ GitHub.")
        return False

    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )

        if result.returncode == 0:
            print("✅ Update thành công!")
            return True

        print(f"❌ git pull lỗi:\n{result.stderr}")
        return False

    except Exception as e:
        print(f"❌ Lỗi update: {e}")
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
            if _run_git_pull():
                _restart()
            else:
                print(
                    "\n❌  Không thể tự cập nhật.\n"
                    "    Vui lòng chạy thủ công: git pull\n"
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
                if _run_git_pull():
                    _restart()
                else:
                    print("⚠️  Cập nhật thất bại. Tiếp tục với phiên bản cũ...\n")
            else:
                print("⚠️  Bỏ qua cập nhật. Tiếp tục...\n")

    except requests.exceptions.RequestException:
        print("⚠️  Không thể kiểm tra phiên bản (không có kết nối). Tiếp tục...\n")
    except Exception as e:
        print(f"⚠️  Lỗi kiểm tra phiên bản: {e}. Tiếp tục...\n")
