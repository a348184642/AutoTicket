import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading
import os
from datetime import datetime
import AutoTicket

GUI_CONFIG_FILE = "./gui_config.json"

class AutoTicketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("多账号杭工e家抢券工具 (最终版)")
        self.root.geometry("850x700")
        
        self.running = False
        self.task_thread = None

        # 1. 顶部：账号配置
        top_frame = tk.LabelFrame(root, text="第一步：账号配置", padx=10, pady=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(top_frame, text="账号文件:").grid(row=0, column=0, sticky=tk.W)
        self.path_entry = tk.Entry(top_frame, width=60)
        self.path_entry.grid(row=0, column=1, padx=5)
        tk.Button(top_frame, text="浏览", command=self.browse_file).grid(row=0, column=2)
        tk.Button(top_frame, text="加载/刷新账号", command=self.load_accounts, bg="#e0e0e0").grid(row=0, column=3, padx=5)

        self.account_list = tk.Listbox(top_frame, width=80, height=4)
        self.account_list.grid(row=1, column=0, columnspan=4, pady=5, sticky=tk.W)

        # 2. 中部：参数配置
        param_frame = tk.LabelFrame(root, text="第二步：参数设置", padx=10, pady=10)
        param_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text="抢券时间:").pack(side=tk.LEFT)
        self.run_time_entry = tk.Entry(row1, width=25)
        self.run_time_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="  兑换ID:").pack(side=tk.LEFT)
        self.exchange_id_entry = tk.Entry(row1, width=5)
        self.exchange_id_entry.pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(param_frame)
        row2.pack(fill=tk.X, pady=5)
        tk.Label(row2, text="运行次数:").pack(side=tk.LEFT)
        self.run_count_entry = tk.Entry(row2, width=8)
        self.run_count_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="  请求间隔(秒):").pack(side=tk.LEFT)
        self.time_sleep_entry = tk.Entry(row2, width=8)
        self.time_sleep_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="  最大并发:").pack(side=tk.LEFT)
        self.max_workers_entry = tk.Entry(row2, width=5)
        self.max_workers_entry.pack(side=tk.LEFT, padx=5)

        row3 = tk.Frame(param_frame)
        row3.pack(fill=tk.X, pady=5)
        tk.Label(row3, text="快捷设置:").pack(side=tk.LEFT)
        tk.Button(row3, text="今天17:00", command=lambda: self.set_quick_time(17, 0)).pack(side=tk.LEFT, padx=5)
        tk.Button(row3, text="今天11:30", command=lambda: self.set_quick_time(11, 30)).pack(side=tk.LEFT, padx=5)
        tk.Button(row3, text="1分钟后(测试)", command=self.set_test_time).pack(side=tk.LEFT, padx=5)

        # 3. 底部：按钮 & 日志
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.daily_btn = tk.Button(btn_frame, text="执行每日任务", command=self.run_daily_task, 
                                   bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=18, height=2)
        self.daily_btn.pack(side=tk.LEFT, padx=10)
        
        self.exchange_btn = tk.Button(btn_frame, text="执行抢券任务", command=self.run_exchange_task, 
                                     bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=18, height=2)
        self.exchange_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="停止", command=self.stop_task, 
                                  bg="#f44336", fg="white", width=10, height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        log_frame = tk.LabelFrame(root, text="运行日志", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, state=tk.DISABLED)
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 初始化
        self.load_gui_config()
        self.path_entry.insert(0, "./accounts.json")

    def set_quick_time(self, hour, minute):
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time < now:
            from datetime import timedelta
            target_time += timedelta(days=1)
        self.run_time_entry.delete(0, tk.END)
        self.run_time_entry.insert(0, target_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.save_gui_config()

    def set_test_time(self):
        from datetime import timedelta
        test_time = datetime.now() + timedelta(minutes=1)
        self.run_time_entry.delete(0, tk.END)
        self.run_time_entry.insert(0, test_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.save_gui_config()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON文件", "*.json")])
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def load_accounts(self):
        file_path = self.path_entry.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("提示", "请先选择有效的账号文件！")
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                accounts = json.load(f)
            
            self.account_list.delete(0, tk.END)
            for idx, account in enumerate(accounts):
                display_name = account.get('login_name', '未知账号')[:10]
                self.account_list.insert(tk.END, f"账号{idx+1}: {display_name}")
            
            self.log(f"✅ 成功加载 {len(accounts)} 个账号")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")
            self.log(f"❌ 加载账号失败: {e}")

    def save_gui_config(self):
        try:
            config = {
                "run_time": self.run_time_entry.get(),
                "exchange_id": self.exchange_id_entry.get(),
                "run_count": self.run_count_entry.get(),
                "time_sleep": self.time_sleep_entry.get(),
                "max_workers": self.max_workers_entry.get(),
                "account_file": self.path_entry.get()
            }
            with open(GUI_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except:
            pass

    def _apply_and_save_config(self):
        try:
            run_time_str = self.run_time_entry.get()
            exchange_id = self.exchange_id_entry.get()
            run_count = int(self.run_count_entry.get())
            time_sleep = float(self.time_sleep_entry.get())
            max_workers = int(self.max_workers_entry.get())

            from datetime import datetime
            run_time = datetime.strptime(run_time_str, "%Y-%m-%d %H:%M:%S")

            AutoTicket.RUN_TIME = run_time
            AutoTicket.EXCHANGE_ID_PLAINTEXT = exchange_id
            AutoTicket.RUN_COUNT = run_count
            AutoTicket.TIME_SLEEP = time_sleep
            AutoTicket.MAX_WORKERS = max_workers
            AutoTicket.config_file = self.path_entry.get()

            self.save_gui_config()
            self.log("✅ 参数已应用")
            return True

        except ValueError as e:
            messagebox.showerror("参数错误", f"请检查格式：{e}")
            return False
        except Exception as e:
            messagebox.showerror("错误", f"应用参数失败：{e}")
            return False

    def load_gui_config(self):
        if os.path.exists(GUI_CONFIG_FILE):
            try:
                with open(GUI_CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                self.run_time_entry.insert(0, config.get("run_time", ""))
                self.exchange_id_entry.insert(0, config.get("exchange_id", "10"))
                self.run_count_entry.insert(0, str(config.get("run_count", 100)))
                self.time_sleep_entry.insert(0, str(config.get("time_sleep", 0.08)))
                self.max_workers_entry.insert(0, str(config.get("max_workers", 5)))
                
                if "account_file" in config:
                    self.path_entry.delete(0, tk.END)
                    self.path_entry.insert(0, config["account_file"])
            except:
                self.set_default_params()
        else:
            self.set_default_params()

    def set_default_params(self):
        self.exchange_id_entry.insert(0, "10")
        self.run_count_entry.insert(0, "100")
        self.time_sleep_entry.insert(0, "0.08")
        self.max_workers_entry.insert(0, "5")
        self.set_quick_time(17, 0)

    def _run_task(self, task_func):
        try:
            if not self._apply_and_save_config():
                return

            self.running = True
            self._update_buttons_state(False)
            
            original_print = __builtins__.print
            def gui_print(*args, **kwargs):
                msg = ' '.join(str(arg) for arg in args)
                self.log(msg)
                original_print(*args, **kwargs)
            __builtins__.print = gui_print

            task_func()

        except Exception as e:
            self.log(f"❌ 任务出错: {str(e)}")
            messagebox.showerror("错误", f"任务执行出错：{e}")
        finally:
            __builtins__.print = original_print
            if self.running:
                self.running = False
                self._update_buttons_state(True)
                self.log("🏁 任务结束")

    def run_daily_task(self):
        if self.running:
            messagebox.showinfo("提示", "任务正在运行中！")
            return
        self.log("🚀 准备执行每日任务...")
        self.task_thread = threading.Thread(target=self._run_task, args=(self._daily_task_wrapper,))
        self.task_thread.daemon = True
        self.task_thread.start()

    def _daily_task_wrapper(self):
        AutoTicket.config_file = self.path_entry.get()
        AutoTicket.run_multi_account_daily_task()

    def run_exchange_task(self):
        if self.running:
            messagebox.showinfo("提示", "任务正在运行中！")
            return
        self.log("🚀 准备执行抢券任务...")
        self.task_thread = threading.Thread(target=self._run_task, args=(AutoTicket.run_multi_account_exchange,))
        self.task_thread.daemon = True
        self.task_thread.start()

    def stop_task(self):
        if not self.running:
            self.log("没有正在运行的任务")
            return
            
        self.log("⏹️ 正在发送停止信号...")
        AutoTicket.STOP_FLAG = True
        
        # 立即解锁界面
        self.running = False
        self._update_buttons_state(True)
        self.log("⏹️ 停止信号已发送，界面已解锁")

    def _update_buttons_state(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.daily_btn.config(state=state)
        self.exchange_btn.config(state=state)
        self.stop_btn.config(state=tk.DISABLED if enabled else tk.NORMAL)
        for entry in [self.run_time_entry, self.exchange_id_entry, self.run_count_entry, 
                      self.time_sleep_entry, self.max_workers_entry, self.path_entry]:
            entry.config(state=state)

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {msg}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoTicketGUI(root)
    root.mainloop()
