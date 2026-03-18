import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QMessageBox, QSplitter)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, Qt
import AutoTicket
import threading
import json
import os
from datetime import datetime, timedelta

# 工作线程：处理单个账号抢券任务
class Worker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, account_no, login_name, ses_id, exchange_id, run_time_str, run_count, time_sleep):
        super().__init__()
        self.account_no = account_no
        self.login_name = login_name
        self.user_id = login_name
        self.ses_id = ses_id
        self.exchange_id = exchange_id
        self.run_time_str = run_time_str
        self.run_count = int(run_count)
        self.time_sleep = float(time_sleep)
        self.running = True
        self.timer = None

    def run(self):
        try:
            AutoTicket.set_log_callback(lambda msg: self.log_signal.emit(f"[账号{self.account_no}] {msg}"))
            AutoTicket.LOGIN_NAME_PLAINTEXT = self.login_name
            AutoTicket.USER_ID_PLAINTEXT = self.login_name
            AutoTicket.SES_ID = self.ses_id
            AutoTicket.EXCHANGE_ID_PLAINTEXT = self.exchange_id
            
            run_time = datetime.strptime(self.run_time_str, "%Y-%m-%d %H:%M:%S")
            AutoTicket.RUN_TIME = run_time
            AutoTicket.RUN_COUNT = self.run_count
            AutoTicket.timeSleep = self.time_sleep

            self.log_signal.emit(f"程序已启动，将在 {run_time} 执行兑换任务，共执行 {self.run_count} 次。")
            self.task_thread = threading.Thread(target=self.run_task)
            self.task_thread.start()
            
        except Exception as e:
            self.log_signal.emit(f"发生错误: {str(e)}")
            self.finished_signal.emit()

    def run_task(self):
        try:
            AutoTicket.set_log_callback(lambda msg: self.log_signal.emit(f"[账号{self.account_no}] {msg}"))
            AutoTicket.wait_until_target()
            if self.running:
                AutoTicket.job()
        except Exception as e:
            self.log_signal.emit(f"任务执行出错: {str(e)}")
        finally:
            AutoTicket.set_log_callback(None)
            self.finished_signal.emit()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.cancel()
        self.quit()
        self.wait()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker1 = None
        self.worker2 = None
        self.init_ui()
        self.config_file = "./config.json"
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('多账号自动抢券工具')
        self.setGeometry(100, 100, 800, 600)

        # 账号1配置
        config_group1 = QGroupBox("账号1配置")
        config_layout1 = QFormLayout()
        self.login_name1_edit = QLineEdit(AutoTicket.LOGIN_NAME_PLAINTEXT)
        self.ses_id1_edit = QLineEdit(AutoTicket.SES_ID)
        self.exchange_id1_edit = QLineEdit(AutoTicket.EXCHANGE_ID_PLAINTEXT)
        self.run_time1_edit = QLineEdit(self.get_next_run_time())
        self.run_count1_edit = QLineEdit(str(AutoTicket.RUN_COUNT))
        self.time_sleep1_edit = QLineEdit(str(AutoTicket.timeSleep))
        config_layout1.addRow(QLabel("LOGIN_NAME/USER_ID:"), self.login_name1_edit)
        config_layout1.addRow(QLabel("SES_ID:"), self.ses_id1_edit)
        config_layout1.addRow(QLabel("EXCHANGE_ID:#9=2块,10=4块,11=6块"), self.exchange_id1_edit)
        config_layout1.addRow(QLabel("抢票时间"), self.run_time1_edit)
        config_layout1.addRow(QLabel("运行次数:"), self.run_count1_edit)
        config_layout1.addRow(QLabel("运行间隔:"), self.time_sleep1_edit)
        config_group1.setLayout(config_layout1)

        # 账号2配置
        config_group2 = QGroupBox("账号2配置")
        config_layout2 = QFormLayout()
        self.login_name2_edit = QLineEdit(AutoTicket.LOGIN_NAME_PLAINTEXT)
        self.ses_id2_edit = QLineEdit(AutoTicket.SES_ID)
        self.exchange_id2_edit = QLineEdit(AutoTicket.EXCHANGE_ID_PLAINTEXT)
        self.run_time2_edit = QLineEdit(self.get_next_run_time())
        self.run_count2_edit = QLineEdit(str(AutoTicket.RUN_COUNT))
        self.time_sleep2_edit = QLineEdit(str(AutoTicket.timeSleep))
        config_layout2.addRow(QLabel("LOGIN_NAME/USER_ID:"), self.login_name2_edit)
        config_layout2.addRow(QLabel("SES_ID:"), self.ses_id2_edit)
        config_layout2.addRow(QLabel("EXCHANGE_ID:#9=2块,10=4块,11=6块"), self.exchange_id2_edit)
        config_layout2.addRow(QLabel("抢票时间"), self.run_time2_edit)
        config_layout2.addRow(QLabel("运行次数:"), self.run_count2_edit)
        config_layout2.addRow(QLabel("运行间隔:"), self.time_sleep2_edit)
        config_group2.setLayout(config_layout2)

        # 布局
        config_splitter = QSplitter(Qt.Horizontal)
        config_splitter.addWidget(config_group1)
        config_splitter.addWidget(config_group2)
        config_splitter.setSizes([400, 400])

        # 功能按钮（已移除GitHub按钮）
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动双账号抢券")
        self.stop_button = QPushButton("停止所有任务")
        self.daily_task_button = QPushButton("执行双账号每日任务")
        self.set_1130_button = QPushButton("一键设置11:30抢票")
        self.set_1700_button = QPushButton("一键设置17:00抢票")
        
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.daily_task_button)
        button_layout.addWidget(self.set_1130_button)
        button_layout.addWidget(self.set_1700_button)

        # 日志区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(config_splitter)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("运行日志:"))
        main_layout.addWidget(self.log_display)
        self.setLayout(main_layout)

        # 信号绑定
        self.start_button.clicked.connect(self.start_double_program)
        self.stop_button.clicked.connect(self.stop_all_program)
        self.daily_task_button.clicked.connect(self.execute_double_daily_task)
        self.set_1130_button.clicked.connect(lambda: self.set_fixed_time("11:30"))
        self.set_1700_button.clicked.connect(lambda: self.set_fixed_time("17:00"))

        # 配置自动保存
        self.login_name1_edit.textChanged.connect(self.save_config)
        self.ses_id1_edit.textChanged.connect(self.save_config)
        self.exchange_id1_edit.textChanged.connect(self.save_config)
        self.run_count1_edit.textChanged.connect(self.save_config)
        self.time_sleep1_edit.textChanged.connect(self.save_config)
        self.login_name2_edit.textChanged.connect(self.save_config)
        self.ses_id2_edit.textChanged.connect(self.save_config)
        self.exchange_id2_edit.textChanged.connect(self.save_config)
        self.run_count2_edit.textChanged.connect(self.save_config)
        self.time_sleep2_edit.textChanged.connect(self.save_config)

    def get_fixed_time_str(self, hour_minute):
        today = datetime.now().date()
        target_time = datetime.combine(today, datetime.strptime(hour_minute, "%H:%M").time())
        if target_time < datetime.now():
            target_time += timedelta(days=1)
        return target_time.strftime("%Y-%m-%d %H:%M:%S")

    def set_fixed_time(self, hour_minute):
        fixed_time = self.get_fixed_time_str(hour_minute)
        self.run_time1_edit.setText(fixed_time)
        self.run_time2_edit.setText(fixed_time)
        self.update_log(f"已一键设置两个账号抢票时间为：{fixed_time}")

    def start_double_program(self):
        # 账号1参数
        login_name1 = self.login_name1_edit.text()
        ses_id1 = self.ses_id1_edit.text()
        exchange_id1 = self.exchange_id1_edit.text()
        run_time1_str = self.run_time1_edit.text()
        run_count1 = self.run_count1_edit.text()
        time_sleep1 = self.time_sleep1_edit.text()
        # 账号2参数
        login_name2 = self.login_name2_edit.text()
        ses_id2 = self.ses_id2_edit.text()
        exchange_id2 = self.exchange_id2_edit.text()
        run_time2_str = self.run_time2_edit.text()
        run_count2 = self.run_count2_edit.text()
        time_sleep2 = self.time_sleep2_edit.text()
        
        all_fields = [login_name1, ses_id1, exchange_id1, run_time1_str, run_count1, time_sleep1,
                      login_name2, ses_id2, exchange_id2, run_time2_str, run_count2, time_sleep2]
        if not all(all_fields):
            QMessageBox.warning(self, "输入错误", "所有字段都必须填写！")
            return
        try:
            int(run_count1)
            float(time_sleep1)
            datetime.strptime(run_time1_str, "%Y-%m-%d %H:%M:%S")
            int(run_count2)
            float(time_sleep2)
            datetime.strptime(run_time2_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            QMessageBox.warning(self, "输入错误", "运行次数/间隔必须是数字，时间格式错误！")
            return
        
        # 启动双任务
        self.worker1 = Worker(1, login_name1, ses_id1, exchange_id1, run_time1_str, run_count1, time_sleep1)
        self.worker1.log_signal.connect(self.update_log)
        self.worker1.finished_signal.connect(lambda: self.worker_finished(1))
        self.worker1.start()

        self.worker2 = Worker(2, login_name2, ses_id2, exchange_id2, run_time2_str, run_count2, time_sleep2)
        self.worker2.log_signal.connect(self.update_log)
        self.worker2.finished_signal.connect(lambda: self.worker_finished(2))
        self.worker2.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_log("双账号任务启动中...")
        
    def stop_all_program(self):
        if self.worker1:
            self.worker1.stop()
            self.worker1 = None
        if self.worker2:
            self.worker2.stop()
            self.worker2 = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_log("所有任务已停止")
        
    def worker_finished(self, account_no):
        self.update_log(f"账号{account_no}任务执行完成")
        if (self.worker1 is None or not self.worker1.isRunning()) and \
           (self.worker2 is None or not self.worker2.isRunning()):
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def execute_double_daily_task(self):
        login_name1 = self.login_name1_edit.text()
        ses_id1 = self.ses_id1_edit.text()
        exchange_id1 = self.exchange_id1_edit.text()
        login_name2 = self.login_name2_edit.text()
        ses_id2 = self.ses_id2_edit.text()
        exchange_id2 = self.exchange_id2_edit.text()
        
        if not all([login_name1, ses_id1, login_name2, ses_id2]):
            QMessageBox.warning(self, "输入错误", "LOGIN_NAME和SES_ID不能为空！")
            return
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.daily_task_button.setEnabled(False)
        
        self.daily_task_thread = threading.Thread(target=self.run_double_daily_task, 
                                                  args=(login_name1, ses_id1, exchange_id1,
                                                        login_name2, ses_id2, exchange_id2))
        self.daily_task_thread.start()
        
    def run_double_daily_task(self, login1, ses1, exch1, login2, ses2, exch2):
        try:
            self.update_log("开始执行账号1每日任务...")
            AutoTicket.LOGIN_NAME_PLAINTEXT = login1
            AutoTicket.USER_ID_PLAINTEXT = login1
            AutoTicket.SES_ID = ses1
            AutoTicket.EXCHANGE_ID_PLAINTEXT = exch1
            AutoTicket.set_log_callback(lambda msg: self.update_log(f"[账号1] {msg}"))
            AutoTicket.daily_task_workflow()

            self.update_log("开始执行账号2每日任务...")
            AutoTicket.LOGIN_NAME_PLAINTEXT = login2
            AutoTicket.USER_ID_PLAINTEXT = login2
            AutoTicket.SES_ID = ses2
            AutoTicket.EXCHANGE_ID_PLAINTEXT = exch2
            AutoTicket.set_log_callback(lambda msg: self.update_log(f"[账号2] {msg}"))
            AutoTicket.daily_task_workflow()

        except Exception as e:
            self.update_log(f"每日任务出错: {str(e)}")
        finally:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.daily_task_button.setEnabled(True)
            self.update_log("双账号每日任务执行完成")
            AutoTicket.set_log_callback(None)
        
    def update_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_display.append(f"[{timestamp}] {message}")
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

    def save_config(self):
        config = {
            "account1": {
                "login_name": self.login_name1_edit.text(),
                "ses_id": self.ses_id1_edit.text(),
                "exchange_id": self.exchange_id1_edit.text(),
                "run_count": self.run_count1_edit.text(),
                "time_sleep": self.time_sleep1_edit.text()
            },
            "account2": {
                "login_name": self.login_name2_edit.text(),
                "ses_id": self.ses_id2_edit.text(),
                "exchange_id": self.exchange_id2_edit.text(),
                "run_count": self.run_count2_edit.text(),
                "time_sleep": self.time_sleep2_edit.text()
            }
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    config = json.load(f)
                if "account1" in config:
                    acc1 = config["account1"]
                    self.login_name1_edit.setText(acc1.get("login_name", ""))
                    self.ses_id1_edit.setText(acc1.get("ses_id", ""))
                    self.exchange_id1_edit.setText(acc1.get("exchange_id", ""))
                    self.run_count1_edit.setText(acc1.get("run_count", str(AutoTicket.RUN_COUNT)))
                    self.time_sleep1_edit.setText(acc1.get("time_sleep", str(AutoTicket.timeSleep)))
                if "account2" in config:
                    acc2 = config["account2"]
                    self.login_name2_edit.setText(acc2.get("login_name", ""))
                    self.ses_id2_edit.setText(acc2.get("ses_id", ""))
                    self.exchange_id2_edit.setText(acc2.get("exchange_id", ""))
                    self.run_count2_edit.setText(acc2.get("run_count", str(AutoTicket.RUN_COUNT)))
                    self.time_sleep2_edit.setText(acc2.get("time_sleep", str(AutoTicket.timeSleep)))
            except Exception as e:
                self.update_log(f"加载配置失败: {str(e)}")

    def get_next_run_time(self):
        now = datetime.now()
        today = now.date()
        time_11_30 = datetime.combine(today, datetime.strptime("11:30", "%H:%M").time())
        time_17_00 = datetime.combine(today, datetime.strptime("17:00", "%H:%M").time())
        if now < time_11_30:
            next_time = time_11_30
        elif now < time_17_00:
            next_time = time_17_00
        else:
            next_time = datetime.combine(today + timedelta(days=1), datetime.strptime("11:30", "%H:%M").time())
        return next_time.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
