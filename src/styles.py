"""
Styles và themes cho CLI application
"""
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.box import ROUNDED
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from pyfiglet import figlet_format

# ============================================================================
# ICONS - Emoji icons cho các thành phần
# ============================================================================
class Icons:
    """Collection of icons used throughout the app"""
    # Menu & Navigation
    MENU = "📋"
    HOME = "🏠"
    BACK = "◀️"
    NEXT = "▶️"
    EXIT = "🚪"
    
    # Actions
    ADD = "➕"
    EDIT = "✏️"
    DELETE = "🗑️"
    SAVE = "💾"
    REFRESH = "🔄"
    SEARCH = "🔍"
    SETTINGS = "⚙️"
    
    # Status
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    DONE = "✔️"
    PENDING = "⏸️"
    
    # Social Media
    INSTAGRAM = "📷"
    FACEBOOK = "📘"
    TWITTER = "🐦"
    YOUTUBE = "📺"
    TIKTOK = "🎵"
    
    # GoLike Specific
    ACCOUNT = "👤"
    ACCOUNTS = "👥"
    JOB = "💼"
    JOBS = "📦"
    MONEY = "💰"
    COIN = "🪙"
    CHART = "📊"
    REPORT = "📈"
    
    # Automation
    ROBOT = "🤖"
    ROCKET = "🚀"
    FIRE = "🔥"
    STAR = "⭐"
    LIGHTNING = "⚡"
    
    # Time
    CLOCK = "🕐"
    TIMER = "⏱️"
    CALENDAR = "📅"
    
    # Misc
    LOCK = "🔒"
    UNLOCK = "🔓"
    KEY = "🔑"
    BELL = "🔔"
    FLAG = "🚩"
    TROPHY = "🏆"
    PARTY = "🎉"
    WAVE = "👋"
    TARGET = "🎯"
    SWITCH = "🔀"
    NUMBER = "🔢"
    TROPHY = "🏆"
    GIFT = "🎁"
    HEART = "❤️"
    THUMBS_UP = "👍"
    WAVE = "👋"
    PARTY = "🎉"


# ============================================================================
# COLORS - Color palette
# ============================================================================
class Colors:
    """Color definitions"""
    PRIMARY = "magenta"
    SECONDARY = "cyan"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "blue"
    MUTED = "dim white"
    HIGHLIGHT = "bold yellow"
    
    # Gradients
    GRADIENT_1 = ["magenta", "blue", "cyan"]
    GRADIENT_2 = ["red", "yellow", "green"]


# ============================================================================
# THEME
# ============================================================================
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "primary": "bold magenta",
    "secondary": "blue",
    "highlight": "bold yellow",
    "muted": "dim white",
    "title": "bold cyan",
    "subtitle": "italic magenta",
    "border": "cyan",
})

# Console với theme
console = Console(theme=custom_theme)


# ============================================================================
# LOGO & HEADER
# ============================================================================
def create_logo():
    """Tạo header đơn giản với text"""
    # Header với icons
    header = Text()
    header.append(f"\n{Icons.FIRE} ", style="bold red")
    header.append("═" * 50, style="bold white")
    header.append(f" {Icons.FIRE}\n", style="bold red")
    
    # Title
    title = Text()
    title.append("  GOLIKE AUTOMATION TOOL  \n", style="bold bright_cyan")
    
    # Subtitle với nhiều icons
    subtitle = Text()
    subtitle.append(f"  {Icons.INSTAGRAM} ", style="bold magenta")
    subtitle.append("Instagram Automation", style="bold white")
    subtitle.append(f" {Icons.ROBOT} {Icons.LIGHTNING}  \n", style="bold yellow")
    
    # Info line
    info = Text()
    info.append(f"  {Icons.STAR} ", style="bold yellow")
    info.append("Version 1.0.0", style="cyan")
    info.append(" │ ", style="dim white")
    info.append(f"{Icons.TROPHY} Premium Edition", style="green")
    info.append(f" {Icons.STAR}  \n", style="bold yellow")
    
    # Footer với icons
    footer = Text()
    footer.append(f"{Icons.FIRE} ", style="bold red")
    footer.append("═" * 50, style="bold white")
    footer.append(f" {Icons.FIRE}\n", style="bold red")
    
    # Combine tất cả
    combined = Text()
    combined.append(header)
    combined.append(title)
    combined.append(subtitle)
    combined.append(info)
    combined.append(footer)
    
    # Wrap trong panel với viền trắng
    panel = Panel(
        Align.center(combined),
        border_style="bold cyan",
        box=ROUNDED,
        padding=(0, 2),
    )
    
    return Align.center(panel)


def print_header():
    """In header với logo"""
    console.clear()
    console.print()
    console.print(create_logo())
    console.print()


# ============================================================================
# MENU & PANELS
# ============================================================================
def create_menu_panel(title="MENU CHÍNH", items=None, icon=Icons.MENU):
    """
    Tạo menu panel với viền tròn
    
    Args:
        title: Tiêu đề menu
        items: List of tuples (number, name, description, icon)
        icon: Icon cho title
    """
    if items is None:
        items = [
            ("1", "Thêm tài khoản GoLike", "Thêm hoặc quản lý tài khoản", Icons.ADD),
            ("2", "Chạy nhiệm vụ", "Bắt đầu tự động làm nhiệm vụ", Icons.ROCKET),
            ("3", "Báo cáo", "Xem thống kê và báo cáo", Icons.CHART),
            ("0", "Thoát", "Thoát chương trình", Icons.EXIT),
        ]
    
    # Tạo table cho menu
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Option", style="bold cyan", width=10, justify="center")
    table.add_column("Name", style="bold white", width=35)
    table.add_column("Description", style="muted", width=40)
    
    for item in items:
        if len(item) == 4:
            num, name, desc, item_icon = item
        else:
            num, name, desc = item
            item_icon = Icons.NEXT
        
        table.add_row(
            f"[bold cyan][{num}][/bold cyan]",
            f"{item_icon} {name}",
            desc
        )
    
    # Wrap trong panel với viền tròn
    panel = Panel(
        Align.center(table),
        title=f"[bold magenta]{icon} {title}[/bold magenta]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    
    return Align.center(panel)


def create_info_panel(content, title="THÔNG TIN", style="info", icon=Icons.INFO):
    """Tạo panel thông tin với icon"""
    panel = Panel(
        Align.center(Text(content, style=style)),
        title=f"[bold]{icon} {title}[/bold]",
        border_style=style,
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    return Align.center(panel)


# ============================================================================
# TABLES
# ============================================================================
def create_stats_table(stats_data, title="THỐNG KÊ", icon=Icons.CHART):
    """
    Tạo bảng thống kê với icons
    
    Args:
        stats_data: Dict với các key-value cần hiển thị
        title: Tiêu đề bảng
        icon: Icon cho title
    """
    table = Table(
        show_header=True, 
        header_style="bold magenta", 
        box=ROUNDED,
        padding=(0, 2)
    )
    table.add_column("Chỉ số", style="cyan", width=35)
    table.add_column("Giá trị", style="bold green", width=25, justify="right")
    
    # Icon mapping cho các loại stats
    stat_icons = {
        "Tổng số tài khoản": Icons.ACCOUNTS,
        "Tài khoản đang hoạt động": Icons.FIRE,
        "Nhiệm vụ hoàn thành": Icons.DONE,
        "Tổng thu nhập": Icons.MONEY,
        "Đang chạy": Icons.ROCKET,
        "Thành công": Icons.SUCCESS,
        "Thất bại": Icons.ERROR,
        "Chờ xử lý": Icons.PENDING,
    }
    
    for key, value in stats_data.items():
        # Tìm icon phù hợp
        stat_icon = stat_icons.get(key, Icons.INFO)
        table.add_row(f"{stat_icon} {key}", str(value))
    
    panel = Panel(
        Align.center(table),
        title=f"[bold magenta]{icon} {title}[/bold magenta]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    
    return Align.center(panel)


def create_account_table(accounts, title="DANH SÁCH TÀI KHOẢN"):
    """
    Tạo bảng hiển thị danh sách tài khoản
    
    Args:
        accounts: List of account dicts
        title: Tiêu đề bảng
    """
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=ROUNDED,
        padding=(0, 1)
    )
    
    table.add_column("STT", style="cyan", width=6, justify="center")
    table.add_column("Username", style="bold white", width=20)
    table.add_column("Instagram", style="green", width=15, justify="center")
    table.add_column("Trạng thái", style="yellow", width=15, justify="center")
    table.add_column("Thu nhập", style="bold green", width=15, justify="right")
    
    for idx, acc in enumerate(accounts, 1):
        status = f"{Icons.FIRE} Hoạt động" if acc.get('active') else f"{Icons.PENDING} Chờ"
        ig_count = f"{Icons.INSTAGRAM} {acc.get('ig_count', 0)}"
        earnings = f"{Icons.MONEY} {acc.get('earnings', 0):,}"
        
        table.add_row(
            str(idx),
            acc.get('username', 'N/A'),
            ig_count,
            status,
            earnings
        )
    
    panel = Panel(
        Align.center(table),
        title=f"[bold magenta]{Icons.ACCOUNTS} {title}[/bold magenta]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    
    return Align.center(panel)


def create_job_table(jobs, title="NHIỆM VỤ"):
    """
    Tạo bảng hiển thị nhiệm vụ
    
    Args:
        jobs: List of job dicts
        title: Tiêu đề bảng
    """
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=ROUNDED,
        padding=(0, 1)
    )
    
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Loại", style="bold white", width=15)
    table.add_column("Tài khoản", style="green", width=20)
    table.add_column("Trạng thái", style="yellow", width=15, justify="center")
    table.add_column("Thưởng", style="bold green", width=12, justify="right")
    
    for job in jobs:
        job_type_icons = {
            'follow': f"{Icons.ACCOUNTS} Follow",
            'like': f"{Icons.HEART} Like",
            'comment': f"{Icons.INFO} Comment",
        }
        
        job_type = job_type_icons.get(job.get('type'), job.get('type', 'N/A'))
        
        status_map = {
            'pending': f"{Icons.PENDING} Chờ",
            'running': f"{Icons.ROCKET} Đang chạy",
            'completed': f"{Icons.SUCCESS} Hoàn thành",
            'failed': f"{Icons.ERROR} Thất bại",
        }
        
        status = status_map.get(job.get('status'), job.get('status', 'N/A'))
        reward = f"{Icons.COIN} {job.get('reward', 0):,}"
        
        table.add_row(
            job.get('id', 'N/A'),
            job_type,
            job.get('account', 'N/A'),
            status,
            reward
        )
    
    panel = Panel(
        Align.center(table),
        title=f"[bold magenta]{Icons.JOBS} {title}[/bold magenta]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    
    return Align.center(panel)


def create_progress_panel(current, total, message="Đang xử lý...", icon=Icons.LOADING):
    """Tạo panel hiển thị tiến trình với icon"""
    percentage = (current / total * 100) if total > 0 else 0
    bar_length = 40
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    
    # Chọn icon dựa trên progress
    if percentage >= 100:
        status_icon = Icons.SUCCESS
    elif percentage >= 50:
        status_icon = Icons.FIRE
    else:
        status_icon = Icons.ROCKET
    
    content = f"{message}\n\n{bar}\n\n{status_icon} {current}/{total} ({percentage:.1f}%)"
    
    panel = Panel(
        Align.center(Text(content, style="cyan")),
        title=f"[bold magenta]{icon} TIẾN TRÌNH[/bold magenta]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2),
        expand=False,
    )
    
    return Align.center(panel)


# ============================================================================
# PRINT FUNCTIONS
# ============================================================================
def print_separator(char="─", style="dim cyan"):
    """In đường phân cách"""
    console.print(char * console.width, style=style)


def print_success(message, icon=Icons.SUCCESS):
    """In thông báo thành công"""
    console.print(f"{icon} [success]{message}[/success]")


def print_error(message, icon=Icons.ERROR):
    """In thông báo lỗi"""
    console.print(f"{icon} [error]{message}[/error]")


def print_warning(message, icon=Icons.WARNING):
    """In thông báo cảnh báo"""
    console.print(f"{icon} [warning]{message}[/warning]")


def print_info(message, icon=Icons.INFO):
    """In thông báo thông tin"""
    console.print(f"{icon} [info]{message}[/info]")


def get_input(prompt="Nhập lựa chọn", style="bold cyan"):
    """Lấy input từ user với style"""
    return console.input(f"[{style}]{prompt}: [/{style}]")


def confirm(prompt="Bạn có chắc chắn?", default=False):
    """Hỏi xác nhận yes/no"""
    default_text = "Y/n" if default else "y/N"
    response = console.input(f"[bold yellow]{prompt} [{default_text}]: [/bold yellow]").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'có', 'c']


def print_divider(char="─", style="dim cyan"):
    """In đường phân cách đẹp"""
    width = console.width
    console.print(char * width, style=style)
