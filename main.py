"""
GoLike Instagram Automation Tool - CLI Version
Main entry point
"""
import sys
import time
import json
import os
from datetime import datetime

# Kiểm tra version ngay khi khởi động
from src.utils.version_check import check_version
check_version()
from rich.box import ROUNDED
from rich.table import Table
from rich.panel import Panel
from src.styles import (
    console,
    print_header,
    create_menu_panel,
    create_info_panel,
    get_input,
    print_success,
    print_error,
    print_warning,
    print_info,
    confirm,
    Icons,
    create_stats_table,
    create_account_table,
    create_job_table,
)
# ✅ Only import services - no direct core module access
from src.services.account_service import AccountService
from src.services.cookie_service import CookieService
from src.services.runner_service import RunnerService


class GoLikeApp:
    """Main application class"""
    
    def __init__(self):
        self.running = True
        
        # ✅ Initialize services
        self.account_service = AccountService()
        self.cookie_service = CookieService()
        self.runner_service = RunnerService()
        
        # Get data from services
        self.accounts = self.account_service.get_accounts()
        self.config = self.runner_service.get_config()
        
        # Stats from account service
        self.stats = self.account_service.get_stats()
    
    def refresh_data(self):
        """✅ Refresh data from services"""
        self.accounts = self.account_service.get_accounts()
        self.config = self.runner_service.get_config()
        self.stats = self.account_service.get_stats()
    
    def show_menu(self):
        """Hiển thị menu chính"""
        print_header()
        
        menu_items = [
            ("1", "Thêm tài khoản GoLike", "Thêm hoặc quản lý tài khoản", Icons.ADD),
            ("2", "Chạy nhiệm vụ", "Bắt đầu tự động làm nhiệm vụ", Icons.ROCKET),
            ("3", "Báo cáo", "Xem thống kê và báo cáo", Icons.CHART),
            ("0", "Thoát", "Thoát chương trình", Icons.EXIT),
        ]
        
        console.print(create_menu_panel("MENU CHÍNH", menu_items, icon=Icons.MENU))
        console.print()
    
    def add_account(self):
        """Option 1: Thêm tài khoản GoLike"""
        print_header()
        console.print(create_info_panel(
            "Thêm tài khoản GoLike để bắt đầu kiếm tiền",
            title="QUẢN LÝ TÀI KHOẢN",
            style="primary",
            icon=Icons.ACCOUNT
        ))
        console.print()
        
        print_info(f"Nhập Authorization Token từ GoLike:", icon=Icons.KEY)
        console.print()
        
        try:
            authorization = get_input(f"{Icons.LOCK} Authorization Token")
            if not authorization:
                print_warning("Authorization không được để trống!", icon=Icons.WARNING)
                time.sleep(2)
                return
            
            console.print()
            print_info("Đang kiểm tra tài khoản GoLike...", icon=Icons.LOADING)
            
            # ✅ Use AccountService instead of direct API calls
            result = self.account_service.add_account(authorization)
            
            if result['success']:
                account_info = result['account']
                
                # Hiển thị thông tin tài khoản
                console.print()
                print_success(f"Tìm thấy tài khoản GoLike!", icon=Icons.PARTY)
                console.print()
                
                # Tạo bảng thông tin
                info_table = Table(show_header=False, box=None, padding=(0, 2))
                info_table.add_column("Field", style="cyan", width=25)
                info_table.add_column("Value", style="bold white", width=40)
                
                info_table.add_row(f"{Icons.ACCOUNT} Username", account_info.get('username_account', 'N/A'))
                info_table.add_row(f"{Icons.INFO} Tên", account_info.get('name_account', 'N/A'))
                info_table.add_row(f"{Icons.INFO} Email", account_info.get('email_account', 'N/A'))
                info_table.add_row(f"{Icons.INSTAGRAM} Instagram accounts", str(len(account_info.get('instagram_accounts', []))))
                info_table.add_row(f"{Icons.COIN} Pending coin", f"{account_info.get('pending_coin', 0):,}")
                info_table.add_row(f"{Icons.MONEY} Total coin", f"{account_info.get('total_coin', 0):,}")
                
                panel = Panel(
                    info_table,
                    title=f"[bold green]{Icons.SUCCESS} THÔNG TIN TÀI KHOẢN[/bold green]",
                    border_style="green",
                    padding=(1, 2)
                )
                console.print(panel)
                console.print()
                
                # Xác nhận thêm
                if confirm(f"{Icons.ADD} Bạn có muốn thêm tài khoản này?", default=True):
                    print_success(result['message'], icon=Icons.PARTY)
                    self.refresh_data()  # ✅ Refresh data from services
                else:
                    print_warning("Đã hủy thêm tài khoản!", icon=Icons.WARNING)
            else:
                console.print()
                print_error(result['message'], icon=Icons.ERROR)
            
            console.print()
            get_input(f"{Icons.NEXT} Nhấn Enter để tiếp tục")
            
        except KeyboardInterrupt:
            print_warning("\nĐã hủy thao tác!", icon=Icons.WARNING)
            time.sleep(1)
    
    def run_jobs(self):
        """Option 2: Chạy nhiệm vụ"""
        print_header()
        console.print(create_info_panel(
            "Tự động làm nhiệm vụ Instagram và kiếm tiền",
            title="AUTOMATION",
            style="success",
            icon=Icons.ROBOT
        ))
        console.print()
        
        if self.stats['total_accounts'] == 0:
            print_warning("Chưa có tài khoản nào! Vui lòng thêm tài khoản trước.", icon=Icons.WARNING)
            console.print()
            get_input(f"{Icons.BACK} Nhấn Enter để quay lại")
            return
        
        # Hiển thị danh sách tài khoản GoLike
        print_info(f"Tìm thấy {len(self.accounts)} tài khoản GoLike:", icon=Icons.ACCOUNTS)
        console.print()
        
        # Tạo bảng danh sách tài khoản
        account_table = Table(
            show_header=True,
            header_style="bold magenta",
            box=ROUNDED,
            padding=(0, 2)
        )
        
        account_table.add_column("STT", style="cyan", width=6, justify="center")
        account_table.add_column("Username", style="bold white", width=25)
        account_table.add_column("Tên", style="green", width=30)
        account_table.add_column("Instagram", style="yellow", width=12, justify="center")
        account_table.add_column("Pending", style="bold cyan", width=15, justify="right")
        account_table.add_column("Total", style="bold green", width=15, justify="right")
        
        for idx, acc in enumerate(self.accounts, 1):
            ig_count = len(acc.get('instagram_accounts', []))
            pending = f"{Icons.COIN} {acc.get('pending_coin', 0):,}"
            total = f"{Icons.MONEY} {acc.get('total_coin', 0):,}"
            
            account_table.add_row(
                str(idx),
                f"{Icons.ACCOUNT} {acc.get('username_account', 'N/A')}",
                acc.get('name_account', 'N/A'),
                f"{Icons.INSTAGRAM} {ig_count}",
                pending,
                total
            )
        
        panel = Panel(
            account_table,
            title=f"[bold magenta]{Icons.ACCOUNTS} DANH SÁCH TÀI KHOẢN GOLIKE[/bold magenta]",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
        console.print(panel)
        console.print()
        
        # Yêu cầu chọn tài khoản
        try:
            print_info("Chọn tài khoản muốn chạy:", icon=Icons.SEARCH)
            console.print()
            
            choice = get_input(f"{Icons.NEXT} Nhập số thứ tự (hoặc 'all' để chạy tất cả, '0' để hủy)")
            
            if choice == '0':
                print_warning("Đã hủy!", icon=Icons.WARNING)
                time.sleep(1)
                return
            
            selected_accounts = []
            
            if choice.lower() == 'all':
                selected_accounts = self.accounts.copy()
                print_success(f"Đã chọn tất cả {len(selected_accounts)} tài khoản!", icon=Icons.FIRE)
            else:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(self.accounts):
                        selected_accounts = [self.accounts[idx - 1]]
                        print_success(f"Đã chọn tài khoản: {selected_accounts[0].get('username_account')}", icon=Icons.SUCCESS)
                    else:
                        print_error(f"Số thứ tự không hợp lệ! Vui lòng chọn từ 1 đến {len(self.accounts)}", icon=Icons.ERROR)
                        time.sleep(2)
                        return
                except ValueError:
                    print_error("Vui lòng nhập số hợp lệ hoặc 'all'!", icon=Icons.ERROR)
                    time.sleep(2)
                    return
            
            console.print()
            
            # Hiển thị thông tin tài khoản đã chọn
            if len(selected_accounts) == 1:
                acc = selected_accounts[0]
                info_text = f"""
Tài khoản: {acc.get('username_account')}
Instagram accounts: {len(acc.get('instagram_accounts', []))}
Pending coin: {acc.get('pending_coin', 0):,}
                """
                console.print(create_info_panel(
                    info_text.strip(),
                    title="TÀI KHOẢN ĐÃ CHỌN",
                    style="success",
                    icon=Icons.SUCCESS
                ))
                console.print()
            
            # ========== CÀI ĐẶT THÔNG SỐ ==========
            print_info("Cài đặt thông số chạy:", icon=Icons.SETTINGS)
            console.print()
            
            # Hiển thị cấu hình hiện tại
            print_info(f"  • Chuyển nick sau: {self.config['jobs_per_account_min']}-{self.config['jobs_per_account_max']} job")
            print_info(f"  • Mục tiêu tổng: {self.config['total_jobs_target']} job")
            print_info(f"  • Delay giữa job: {self.config['delay_between_jobs_min']}-{self.config['delay_between_jobs_max']}s")
            console.print()
            
            if confirm(f"{Icons.EDIT} Bạn có muốn thay đổi cài đặt?", default=False):
                console.print()
                
                # Số job trước khi chuyển nick
                print_info("Số job trước khi chuyển nick:", icon=Icons.SWITCH)
                min_jobs = get_input(f"  Tối thiểu (Enter = {self.config['jobs_per_account_min']})")
                max_jobs = get_input(f"  Tối đa (Enter = {self.config['jobs_per_account_max']})")
                
                if min_jobs.strip():
                    try:
                        self.config['jobs_per_account_min'] = int(min_jobs)
                    except:
                        pass
                
                if max_jobs.strip():
                    try:
                        self.config['jobs_per_account_max'] = int(max_jobs)
                    except:
                        pass
                
                # Tổng số job mục tiêu
                console.print()
                print_info("Tổng số job mục tiêu:", icon=Icons.TARGET)
                total = get_input(f"  Tổng job (Enter = {self.config['total_jobs_target']})")
                
                if total.strip():
                    try:
                        self.config['total_jobs_target'] = int(total)
                    except:
                        pass
                
                # Delay giữa các job
                console.print()
                print_info("Delay giữa các job (giây):", icon=Icons.CLOCK)
                min_delay = get_input(f"  Tối thiểu (Enter = {self.config['delay_between_jobs_min']})")
                max_delay = get_input(f"  Tối đa (Enter = {self.config['delay_between_jobs_max']})")
                
                if min_delay.strip():
                    try:
                        self.config['delay_between_jobs_min'] = int(min_delay)
                    except:
                        pass
                
                if max_delay.strip():
                    try:
                        self.config['delay_between_jobs_max'] = int(max_delay)
                    except:
                        pass
                
                # Lưu config
                self.runner_service.update_config(self.config)
                
                console.print()
                print_success("Đã lưu cài đặt!", icon=Icons.SUCCESS)
                console.print()
            
            # ========== NHẬP COOKIE ==========
            # Kiểm tra xem có cookie đã lưu TRONG TÀI KHOẢN ĐÃ CHỌN không
            # ✅ Use CookieService to get saved cookies
            existing_cookies = self.cookie_service.get_saved_cookies(selected_accounts)
            
            if existing_cookies:
                console.print()
                print_info(f"Tìm thấy {len(existing_cookies)} cookie đã lưu trong tài khoản này:", icon=Icons.INFO)
                for item in existing_cookies:
                    last_check = item.get('last_check', 'Chưa check')
                    if last_check and last_check != 'Chưa check':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                            last_check = dt.strftime('%d/%m/%Y %H:%M')
                        except:
                            pass
                    print_success(f"  {Icons.INSTAGRAM} {item['username']} (Check: {last_check})", icon=Icons.SUCCESS)
                console.print()
                
                if confirm(f"{Icons.ROCKET} Sử dụng cookie đã lưu?", default=True):
                    # Sử dụng cookie đã lưu
                    live_cookies = existing_cookies
                    print_success(f"Đã load {len(live_cookies)} cookie từ database!", icon=Icons.SUCCESS)
                    console.print()
                    
                    # Skip phần nhập cookie, nhảy thẳng đến chạy nhiệm vụ
                    goto_run_jobs = True
                else:
                    goto_run_jobs = False
            else:
                print_warning("Không tìm thấy cookie đã lưu cho tài khoản này!", icon=Icons.WARNING)
                console.print()
                goto_run_jobs = False
            
            if not goto_run_jobs:
                print_info("Nhập Instagram accounts (định dạng: username|cookie)", icon=Icons.INSTAGRAM)
                print_info("Có thể nhập nhiều dòng, nhấn Enter 2 lần để kết thúc", icon=Icons.INFO)
                console.print()
                
                # Nhập nhiều dòng
                lines = []
                console.print("[bold cyan]Nhập từng dòng (Enter 2 lần để kết thúc):[/bold cyan]")
                empty_count = 0
                while True:
                    try:
                        line = input().strip()
                        if not line:
                            empty_count += 1
                            if empty_count >= 2:  # 2 Enter liên tiếp
                                break
                        else:
                            empty_count = 0
                            lines.append(line)
                    except EOFError:
                        break
                
                if not lines:
                    print_warning("Không có dữ liệu nào được nhập!", icon=Icons.WARNING)
                    time.sleep(2)
                    return
                
                console.print()
                print_info(f"Đã nhập {len(lines)} dòng, đang xử lý...", icon=Icons.LOADING)
                console.print()
                
                # ✅ Use CookieService for parsing and validation
                valid_cookies, invalid_lines = self.cookie_service.parse_cookie_input(lines)
                
                # Validate cookies belong to selected accounts
                validated_cookies, invalid_cookies = self.cookie_service.validate_cookies_for_account(valid_cookies, selected_accounts)
                
                # Combine all invalid entries
                all_invalid = invalid_lines + invalid_cookies
                
                # Hiển thị kết quả parse
                if all_invalid:
                    print_warning(f"Có {len(all_invalid)} dòng không hợp lệ:", icon=Icons.WARNING)
                    for line_num, line, reason in all_invalid[:5]:  # Chỉ hiển thị 5 dòng đầu
                        print_error(f"  Dòng {line_num}: {reason}", icon=Icons.ERROR)
                    if len(all_invalid) > 5:
                        print_warning(f"  ... và {len(all_invalid) - 5} dòng khác", icon=Icons.WARNING)
                    console.print()
                
                if not validated_cookies:
                    print_error("Không có cookie hợp lệ nào!", icon=Icons.ERROR)
                    console.print()
                    get_input(f"{Icons.BACK} Nhấn Enter để quay lại")
                    return
                
                print_success(f"Tìm thấy {len(validated_cookies)} cookie hợp lệ, đang kiểm tra...", icon=Icons.SUCCESS)
                console.print()
                
                # ========== KIỂM TRA COOKIE ==========
                # ✅ Use CookieService instead of direct InstagramCookieChecker
                cookie_results = self.cookie_service.check_cookies(validated_cookies)
                
                live_cookies = cookie_results['live']
                die_cookies = cookie_results['die']
                error_cookies = cookie_results['error']
                
                # Show summary from service
                summary = cookie_results['summary']
                
                # ========== KẾT QUẢ ==========
                console.print()
                print_info("=" * 60, icon=Icons.CHART)
                print_success(f"LIVE: {summary['live_count']}", icon=Icons.SUCCESS)
                print_error(f"DIE: {summary['die_count']}", icon=Icons.ERROR)
                print_warning(f"ERROR: {summary['error_count']}", icon=Icons.WARNING)
                print_info("=" * 60, icon=Icons.CHART)
                console.print()
                
                if not live_cookies:
                    print_error("Không có cookie LIVE nào! Không thể chạy nhiệm vụ.", icon=Icons.ERROR)
                    console.print()
                    get_input(f"{Icons.BACK} Nhấn Enter để quay lại")
                    return
                
                # Hiển thị danh sách LIVE
                print_success(f"Tìm thấy {len(live_cookies)} cookie LIVE:", icon=Icons.PARTY)
                for item in live_cookies:
                    print_info(f"  {Icons.INSTAGRAM} {item['ig_username']}", icon=Icons.SUCCESS)
                console.print()
                
                # ========== LƯU COOKIE VÀO DATA ==========
                print_info("Đang lưu cookie vào database...", icon=Icons.SAVE)
                
                # ✅ Use AccountService to update cookies
                if self.account_service.update_instagram_cookies(choice, live_cookies):
                    print_success("Đã lưu tất cả cookie vào database!", icon=Icons.SUCCESS)
                    self.refresh_data()  # ✅ Refresh data from services
                else:
                    print_error("Không thể lưu cookie!", icon=Icons.ERROR)
                
                console.print()
            
            # ========== CHẠY NHIỆM VỤ ==========
            
            # Xác nhận chạy
            if confirm(f"{Icons.ROCKET} Bạn có muốn bắt đầu chạy nhiệm vụ?", default=True):
                print_success("Đang khởi động automation...", icon=Icons.LIGHTNING)
                console.print()
                
                # ✅ Use RunnerService instead of direct InstagramAutomation
                automation_data = self.runner_service.prepare_automation_data(selected_accounts, live_cookies)
                
                if not automation_data['golike_accounts']:
                    print_error("Không có tài khoản nào có cookie!", icon=Icons.ERROR)
                    console.print()
                    get_input(f"{Icons.BACK} Nhấn Enter để quay lại")
                    return
                
                # Hiển thị cấu hình
                summary = self.runner_service.get_automation_summary(selected_accounts, live_cookies)
                print_info(f"⚙️ Cấu hình:", icon=Icons.SETTINGS)
                print_info(f"  • Chuyển nick sau: {summary['estimated']['jobs_per_account']} job")
                print_info(f"  • Mục tiêu: {summary['estimated']['total_target']} job")
                print_info(f"  • Delay: {summary['estimated']['delay_range']}")
                print_info(f"  • Số tài khoản GoLike: {summary['accounts']['golike_count']}")
                print_info(f"  • Tổng Instagram accounts: {summary['accounts']['instagram_count']}")
                console.print()
                
                # ✅ Run automation through service
                try:
                    results = self.runner_service.run_automation(automation_data)
                    
                    console.print()
                    if results['success']:
                        print_success("✅ Hoàn thành!", icon=Icons.TROPHY)
                        
                        # Cập nhật stats
                        self.stats['completed_jobs'] += results['total_missions']
                        self.stats['total_earnings'] += results['total_earnings']
                        
                        # Hiển thị tổng kết
                        console.print()
                        print_info("=" * 60, icon=Icons.CHART)
                        print_success(f"TỔNG KẾT", icon=Icons.TROPHY)
                        print_info(f"Nhiệm vụ hoàn thành: {results['total_missions']}", icon=Icons.DONE)
                        print_info(f"Tổng thu nhập: {results['total_earnings']:,} VNĐ", icon=Icons.MONEY)
                        print_info("=" * 60, icon=Icons.CHART)
                        console.print()
                    else:
                        print_error(f"❌ {results['message']}", icon=Icons.ERROR)
                        if results['total_missions'] > 0:
                            print_info(f"Đã hoàn thành {results['total_missions']} nhiệm vụ trước khi dừng", icon=Icons.INFO)
                    
                except Exception as e:
                    print_error(f"Lỗi: {str(e)}", icon=Icons.ERROR)
                
                console.print()
                get_input(f"{Icons.NEXT} Nhấn Enter để tiếp tục")
            else:
                print_warning("Đã hủy!", icon=Icons.WARNING)
                time.sleep(1)
                
        except KeyboardInterrupt:
            print_warning("\nĐã hủy!", icon=Icons.WARNING)
            time.sleep(1)
    
    def show_report(self):
        """Option 3: Báo cáo"""
        print_header()
        console.print(create_info_panel(
            "Xem thống kê chi tiết và hiệu suất",
            title="DASHBOARD",
            style="info",
            icon=Icons.REPORT
        ))
        console.print()
        
        # Tính toán stats từ accounts thực tế
        total_ig = sum(len(acc.get('instagram_accounts', [])) for acc in self.accounts)
        total_coins = sum(acc.get('total_coin', 0) for acc in self.accounts)
        pending_coins = sum(acc.get('pending_coin', 0) for acc in self.accounts)
        
        stats_display = {
            "Tổng số tài khoản": self.stats['total_accounts'],
            "Tài khoản đang hoạt động": self.stats['active_accounts'],
            "Tổng Instagram accounts": total_ig,
            "Pending coins": f"{pending_coins:,}",
            "Total coins": f"{total_coins:,}",
        }
        
        console.print(create_stats_table(stats_display, title="THỐNG KÊ TỔNG QUAN", icon=Icons.CHART))
        console.print()
        
        # Hiển thị danh sách tài khoản nếu có
        if self.accounts:
            # Convert sang format phù hợp với create_account_table
            display_accounts = []
            for acc in self.accounts:
                display_accounts.append({
                    'username': acc.get('username_account', 'N/A'),
                    'active': acc.get('status') == 'ready',
                    'ig_count': len(acc.get('instagram_accounts', [])),
                    'earnings': acc.get('total_coin', 0)
                })
            
            console.print(create_account_table(display_accounts, "CHI TIẾT TÀI KHOẢN"))
            console.print()
        else:
            print_warning("Chưa có tài khoản nào! Vui lòng thêm tài khoản ở Option 1.", icon=Icons.WARNING)
            console.print()
        
        get_input(f"{Icons.BACK} Nhấn Enter để quay lại")
    
    def exit_app(self):
        """Option 0: Thoát"""
        print_header()
        console.print(create_info_panel(
            "Cảm ơn bạn đã sử dụng GoLike Tool!",
            title="TẠM BIỆT",
            style="primary",
            icon=Icons.WAVE
        ))
        console.print()
        
        # Hiển thị stats cuối cùng
        if self.stats['total_accounts'] > 0:
            final_stats = {
                "Tổng tài khoản đã thêm": self.stats['total_accounts'],
                "Nhiệm vụ đã hoàn thành": self.stats['completed_jobs'],
                "Tổng thu nhập": f"{self.stats['total_earnings']:,} VNĐ",
            }
            console.print(create_stats_table(final_stats, title="KẾT QUẢ PHIÊN LÀM VIỆC", icon=Icons.TROPHY))
            console.print()
        
        print_success("Hẹn gặp lại! ", icon=Icons.PARTY)
        self.running = False
        time.sleep(2)
    
    def handle_choice(self, choice):
        """Xử lý lựa chọn của user"""
        actions = {
            '1': self.add_account,
            '2': self.run_jobs,
            '3': self.show_report,
            '0': self.exit_app,
        }
        
        action = actions.get(choice)
        if action:
            action()
        else:
            print_error("Lựa chọn không hợp lệ!")
            time.sleep(1)
    
    def run(self):
        """Main loop"""
        try:
            while self.running:
                self.show_menu()
                choice = get_input("Nhập lựa chọn của bạn")
                self.handle_choice(choice)
        
        except KeyboardInterrupt:
            console.print()
            print_warning("\nĐã dừng chương trình!", icon=Icons.WARNING)
            time.sleep(1)
        
        except Exception as e:
            console.print()
            print_error(f"Lỗi: {str(e)}", icon=Icons.ERROR)
            time.sleep(2)


def main():
    """Entry point"""
    app = GoLikeApp()
    app.run()


if __name__ == "__main__":
    main()
