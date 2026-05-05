# fig

Tool tự động hóa Instagram, hỗ trợ chạy trên máy tính và điện thoại.

---

## Cài đặt & Chạy

```bash
pip install -r requirements.txt
python main.py
```

---

## Cập nhật tool

### 1. Android — Termux

**Cách A: Dùng Git**

```bash
pkg update
pkg install git
git clone https://github.com/Baophi1201/fig.git
cd fig
git pull
```

Phù hợp khi bạn muốn quản lý source qua GitHub và update thường xuyên.

**Cách B: Không cần Git (khuyên dùng trên mobile)**

Chạy script update tích hợp sẵn:

```bash
pkg install python
python main.py
```

Tool sẽ tự kiểm tra phiên bản và hỏi bạn có muốn cập nhật không.  
Hoặc tải ZIP thủ công:

```bash
curl -L https://github.com/Baophi1201/fig/archive/refs/heads/main.zip -o tool.zip
unzip -o tool.zip
```

---

### 2. iPhone / iPad — a-Shell

**Cách A: Dùng lg2 (Git cho iOS)**

a-Shell dùng `lg2` thay cho `git`:

```bash
lg2 clone https://github.com/Baophi1201/fig.git
cd fig
lg2 pull
```

**Cách B: Script update hoặc tải ZIP**

```bash
python main.py
```

Tool tự tải bản mới và cập nhật, không cần Git.  
Hoặc tải thủ công:

```bash
curl -L https://github.com/Baophi1201/fig/archive/refs/heads/main.zip -o tool.zip
unzip -o tool.zip
```

---

## Lưu ý

- Tool tự động kiểm tra phiên bản mỗi lần khởi động.
- Nếu có bản mới, tool sẽ hỏi bạn có muốn cập nhật không.
- Nếu phiên bản quá cũ (dưới `min_version`), tool bắt buộc cập nhật trước khi chạy.
- Không cần cài Git — tool tự tải ZIP từ GitHub và cập nhật tự động.
