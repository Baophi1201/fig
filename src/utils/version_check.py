"""
Version checker - Kiểm tra và tự động cập nhật tool từ GitHub.

Luồng hoạt động:
  1. Fetch version.json từ GitHub
  2. Nếu version hiện tại < min_version → tự tải bản mới rồi restart
  3. Nếu version hiện tại < current_version → hỏi user, nếu đồng ý thì update rồi restart
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
CURRENT_VERSION = "1.0.12"

# URL raw của file version.json trong repo GitHub
VERSION_URL = "https://raw.githubusercontent.com/Baophi1201/fig/main/version.json"
ZIP_URL = "https://github.com/Baophi1201/fig/archive/refs/heads/main.zip"
# ====================================================


def _detect_platform() -> str:
    """Nhận diện môi trường chạy: termux, ashell, hoặc unknown."""
    if "TERMUX_VERSION" in os.environ:
        return "termux"
    elif "IOS_SYSTEM" in os.environ or "ASHELL" in os.environ or sys.platform == "ios":
        return "ashell"
    return "unknown"


def _download_and_update() -> bool:
    """
    Tải ZIP từ GitHub, giải nén và copy đè lên thư mục gốc.
    Không cần Git, chạy được trên mọi thiết bị kể cả điện thoại.
    """
    project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
    temp_dir = os.path.join(project_root, "temp_update")

    try:
        platform_name = _detect_platform()
        if platform_name == "termux":
            print("📱 Android (Termux) detected")
        elif platform_name == "ashell":
            print("🍎 iPhone/iPad (a-Shell) detected")

        print("📥 Đang tải bản mới từ GitHub...")
        response = requests.get(ZIP_URL, timeout=30)
        response.raise_for_status()

        print("📦 Đang giải nén...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(temp_dir)

        # Thư mục bên trong ZIP thường là "fig-main"
        extracted = os.path.join(temp_dir, "fig-main")
        if not os.path.isdir(extracted):
            # Fallback: lấy thư mục đầu tiên trong temp
            subdirs = [d for d in os.listdir(temp_dir)
                       if os.path.isdir(os.path.join(temp_dir, d))]
            if not subdirs:
                raise FileNotFoundError("Không tìm thấy thư mục sau khi giải nén.")
            extracted = os.path.join(temp_dir, subdirs[0])

        print("🔄 Đang cập nhật file...")
        # Copy từng file theo cấu trúc thư mục, ghi đè lên thư mục gốc
        for root, dirs, files in os.walk(extracted):
            rel_path = os.path.relpath(root, extracted)
            target_dir = os.path.join(project_root, rel_path)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_dir, file)

                shutil.copy2(src_file, dst_file)

        print("✅ Update thành công!")
        return True

    except Exception as e:
        print(f"❌ Update lỗi: {e}")
        return False

    finally:
        # Dọn dẹp thư mục tạm dù thành công hay thất bại
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def _restart() -> None:
    """Restart lại process hiện tại với cùng arguments."""
    print("\n🔄  Đang khởi động lại tool...\n")

    subprocess.Popen(
        [sys.executable] + sys.argv,
        shell=False
    )

    sys.exit(0)


def check_version() -> None:
    """
    Kiểm tra version với server GitHub.

    - version < min_version      → tự tải bản mới rồi restart
    - version < current_version  → hỏi user, nếu đồng ý thì update rồi restart
    - Không kết nối được         → cảnh báo nhẹ rồi tiếp tục
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
