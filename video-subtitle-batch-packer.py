import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import subprocess
import re
from datetime import datetime

class VideoSubtitlePacker:
    def __init__(self, root):
        self.root = root
        self.root.title("视频字幕批量封装工具")
        self.root.geometry("800x780")
        self.root.resizable(False, False)

        # 核心变量
        self.ffmpeg_path_var = tk.StringVar()
        self.video_folder_var = tk.StringVar()
        self.subtitle_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.default_sub_var = tk.IntVar()
        self.encoding_var = tk.StringVar(value="utf-8")  # 默认UTF-8
        self.task_queue = []
        self.is_running = False
        
        # 动态规则变量
        self.video_prefix = ""
        self.video_suffix = ""
        self.sub_prefix = ""
        self.sub_suffix = ""

        # 组件顺序
        self.create_tips_frame()
        self.create_ffmpeg_path_frame()
        self.create_path_frame()
        self.create_default_sub_checkbox()
        self.create_encoding_frame()
        self.create_button_frame()
        self.create_log_window()

    def create_tips_frame(self):
        """用户提示框"""
        tips_frame = ttk.Frame(self.root, padding="10")
        tips_frame.pack(fill="x", expand=False)

        # 核心提示
        main_tips = ttk.Label(
            tips_frame,
            text="📌 仅需标记每个文件夹的第一个文件！用#包裹集数（例：#01#）",
            foreground="red",
            font=("微软雅黑", 9, "bold")
        )
        main_tips.grid(row=0, column=0, padx=5, pady=3, sticky="w")

        # 示例
        example_tips = ttk.Label(
            tips_frame,
            text="示例：[CLANNAD][#01#][1080P].mkv → 输出[CLANNAD][01][1080P].mkv",
            font=("微软雅黑", 8)
        )
        example_tips.grid(row=1, column=0, padx=5, pady=2, sticky="w")

    def create_ffmpeg_path_frame(self):
        ffmpeg_frame = ttk.Frame(self.root, padding="10")
        ffmpeg_frame.pack(fill="x", expand=False)

        # 主标签
        ttk.Label(ffmpeg_frame, text="FFmpeg.exe路径：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # 输入框
        ffmpeg_entry = ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_path_var, width=50)
        ffmpeg_entry.grid(row=0, column=1, padx=5, pady=5)
        # 浏览按钮
        ttk.Button(ffmpeg_frame, text="浏览", command=self.select_ffmpeg_exe).grid(row=0, column=2, padx=5, pady=5)
        
        # 新增：PATH提示（蓝色字体，醒目）
        path_tips = ttk.Label(
            ffmpeg_frame,
            text="💡 若已将FFmpeg添加到PATH可留空！",
            foreground="blue",
            font=("微软雅黑", 8)
        )
        path_tips.grid(row=1, column=0, columnspan=3, padx=5, pady=2, sticky="w")

    def create_path_frame(self):
        """视频/字幕/输出文件夹选择"""
        path_frame = ttk.Frame(self.root, padding="10")
        path_frame.pack(fill="x", expand=False)

        # 原视频文件夹
        ttk.Label(path_frame, text="原视频文件夹：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        video_entry = ttk.Entry(path_frame, textvariable=self.video_folder_var, width=50)
        video_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(path_frame, text="浏览", command=self.select_video_folder).grid(row=0, column=2, padx=5, pady=5)

        # 字幕文件夹
        ttk.Label(path_frame, text="字幕文件夹：").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        sub_entry = ttk.Entry(path_frame, textvariable=self.subtitle_folder_var, width=50)
        sub_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(path_frame, text="浏览", command=self.select_subtitle_folder).grid(row=1, column=2, padx=5, pady=5)

        # 输出文件夹
        ttk.Label(path_frame, text="输出文件夹：").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        output_entry = ttk.Entry(path_frame, textvariable=self.output_folder_var, width=50)
        output_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(path_frame, text="浏览", command=self.select_output_folder).grid(row=2, column=2, padx=5, pady=5)

    def create_default_sub_checkbox(self):
        check_frame = ttk.Frame(self.root, padding="10")
        check_frame.pack(fill="x", expand=False)

        self.default_sub_check = ttk.Checkbutton(
            check_frame,
            text="是否设为默认字幕",
            variable=self.default_sub_var
        )
        self.default_sub_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    def create_encoding_frame(self):
        """编码选择（默认UTF-8）"""
        encoding_frame = ttk.Frame(self.root, padding="10")
        encoding_frame.pack(fill="x", expand=False)

        ttk.Label(encoding_frame, text="输出编码格式：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        encoding_options = ["gbk", "utf-8", "gb2312", "cp936", "utf-16"]
        self.encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=encoding_options,
            state="readonly",
            width=15
        )
        self.encoding_combo.grid(row=0, column=1, padx=5, pady=5)
        self.encoding_combo.current(1)  # 默认UTF-8

    def create_button_frame(self):
        """功能按钮"""
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill="x", expand=False)

        self.start_btn = ttk.Button(
            btn_frame,
            text="开始批量封装",
            command=self.init_task_queue
        )
        self.start_btn.grid(row=0, column=0, padx=10, pady=5)

        ttk.Button(
            btn_frame,
            text="清空日志",
            command=self.clear_log
        ).grid(row=0, column=1, padx=10, pady=5)

    def create_log_window(self):
        """日志窗口"""
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill="both", expand=True)

        ttk.Label(log_frame, text="执行日志：").pack(anchor="w", padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            bg="black",
            fg="white",
            font=("Consolas", 8),
            wrap=tk.WORD
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.bind("<Key>", lambda e: "break")  # 禁止编辑

    # 文件夹/文件选择方法
    def select_ffmpeg_exe(self):
        file_path = filedialog.askopenfilename(
            title="选择FFmpeg.exe",
            filetypes=[("EXE文件", "*.exe"), ("所有文件", "*.*")]
        )
        if file_path:
            self.ffmpeg_path_var.set(file_path)

    def select_video_folder(self):
        folder = filedialog.askdirectory(title="选择原视频文件夹")
        if folder:
            self.video_folder_var.set(folder)

    def select_subtitle_folder(self):
        folder = filedialog.askdirectory(title="选择字幕文件夹")
        if folder:
            self.subtitle_folder_var.set(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder_var.set(folder)

    # 新增：检查系统PATH中是否有FFmpeg
    def check_ffmpeg_in_path(self):
        """
        检查系统PATH是否包含ffmpeg
        :return: 存在返回"ffmpeg"，不存在返回None
        """
        try:
            # 执行ffmpeg -version，验证是否能调用
            result = subprocess.run(
                "ffmpeg -version",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                return "ffmpeg"  # 返回命令名，用于后续调用
            else:
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None

    def parse_first_file_rule(self, first_filename, file_type="video"):
        """解析第一个文件的#标记规则"""
        match = re.search(r'(.*)#(\d+)#(.*)', first_filename)
        if not match:
            self.write_log(f"错误：{file_type}第一个文件【{first_filename}】未找到#数字#格式的标记！")
            return False
        
        prefix = re.escape(match.group(1))
        postfix = re.escape(match.group(3))
        
        if file_type == "video":
            self.video_prefix = prefix
            self.video_suffix = postfix
            self.write_log(f"✅ 解析视频规则：前缀=[{match.group(1)}]，后缀=[{match.group(3)}]")
        else:
            self.sub_prefix = prefix
            self.sub_suffix = postfix
            self.write_log(f"✅ 解析字幕规则：前缀=[{match.group(1)}]，后缀=[{match.group(3)}]")
        
        return True

    def extract_file_number(self, filename, file_type="video"):
        """提取文件集数（兼容带#/不带#）"""
        prefix = self.video_prefix if file_type == "video" else self.sub_prefix
        suffix = self.video_suffix if file_type == "video" else self.sub_suffix
        
        pattern = f"{prefix}#?(\d+)#?{suffix}"
        match = re.search(pattern, filename)
        
        if match:
            return match.group(1)
        return None
    
    def clean_filename(self, filename):
        """移除文件名中的#标记"""
        cleaned_name = re.sub(r'#(\d+)#', r'\1', filename)
        cleaned_name = cleaned_name.replace("#", "")
        return cleaned_name

    def write_log(self, content):
        """写入日志"""
        current_time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_text.insert(tk.END, f"{current_time} {content}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def init_task_queue(self):
        """初始化任务队列（核心逻辑）"""
        if self.is_running:
            self.write_log("提示：当前已有任务在执行，请勿重复点击！")
            return

        # 路径验证
        ffmpeg_path = self.ffmpeg_path_var.get().strip()
        video_folder = self.video_folder_var.get().strip()
        subtitle_folder = self.subtitle_folder_var.get().strip()
        output_folder = self.output_folder_var.get().strip()
        selected_encoding = self.encoding_var.get()

        # 验证FFmpeg路径
        final_ffmpeg_path = None
        if not ffmpeg_path:  # 路径为空，检查PATH
            self.write_log("FFmpeg路径为空，尝试从系统PATH中查找...")
            final_ffmpeg_path = self.check_ffmpeg_in_path()
            if final_ffmpeg_path:
                self.write_log(f"✅ 成功找到PATH中的FFmpeg，将直接调用：{final_ffmpeg_path}")
            else:
                self.write_log("❌ 错误：PATH中未找到FFmpeg！请填写FFmpeg.exe路径或添加到系统PATH")
                return
        else:  # 路径不为空，验证有效性
            if os.path.exists(ffmpeg_path) and ffmpeg_path.endswith(".exe"):
                final_ffmpeg_path = ffmpeg_path
                self.write_log(f"✅ FFmpeg路径验证通过：{final_ffmpeg_path}")
            else:
                self.write_log(f"❌ 错误：无效的FFmpeg.exe路径！{ffmpeg_path}")
                return

        # 验证文件夹路径
        if not video_folder or not subtitle_folder or not output_folder:
            self.write_log("错误：请填写完整的三个文件夹路径！")
            return
        if not os.path.isdir(video_folder) or not os.path.isdir(subtitle_folder) or not os.path.isdir(output_folder):
            self.write_log("错误：部分文件夹路径不存在！")
            return

        # 处理视频文件
        video_ext = ('.mkv', '.mp4', '.MKV', '.MP4')
        video_files = [f for f in os.listdir(video_folder) if f.endswith(video_ext)]
        if not video_files:
            self.write_log("错误：视频文件夹未找到mkv/mp4文件！")
            return
        
        # 解析第一个视频文件的规则
        first_video = video_files[0]
        self.write_log(f"\n===== 解析第一个视频文件规则 =====")
        if not self.parse_first_file_rule(first_video, "video"):
            return
        
        # 批量提取所有视频的集数
        video_dict = {}
        self.write_log(f"\n===== 批量提取视频集数 =====")
        for file in video_files:
            file_path = os.path.join(video_folder, file)
            num = self.extract_file_number(file, "video")
            if num:
                video_dict[num] = file_path
                self.write_log(f"成功：{file} → 集数{num}")
            else:
                self.write_log(f"失败：{file} 未匹配到集数（格式与第一个文件不一致？）")

        if not video_dict:
            self.write_log("错误：未提取到任何视频的集数！")
            return

        # 处理字幕文件
        sub_ext = ('.ass', '.srt', '.ASS', '.SRT')
        sub_files = [f for f in os.listdir(subtitle_folder) if f.endswith(sub_ext)]
        if not sub_files:
            self.write_log("错误：字幕文件夹未找到ass/srt文件！")
            return
        
        # 解析第一个字幕文件的规则
        first_sub = sub_files[0]
        self.write_log(f"\n===== 解析第一个字幕文件规则 =====")
        if not self.parse_first_file_rule(first_sub, "sub"):
            return
        
        # 批量提取所有字幕的集数
        sub_dict = {}
        self.write_log(f"\n===== 批量提取字幕集数 =====")
        for file in sub_files:
            file_path = os.path.join(subtitle_folder, file)
            num = self.extract_file_number(file, "sub")
            if num:
                sub_dict[num] = file_path
                self.write_log(f"成功：{file} → 集数{num}")
            else:
                self.write_log(f"失败：{file} 未匹配到集数（格式与第一个文件不一致？）")

        if not sub_dict:
            self.write_log("错误：未提取到任何字幕的集数！")
            return

        # 匹配视频和字幕
        self.task_queue.clear()
        success_match = 0
        
        # 按集数数字正序排序
        sorted_nums = sorted(video_dict.keys(), key=lambda x: int(x))
        self.write_log(f"\n===== 匹配视频-字幕（正序） =====")
        # 在init_task_queue函数的“匹配视频和字幕”部分，替换输出文件名的生成逻辑
        for num in sorted_nums:
            if num in sub_dict:
                video_path = video_dict[num]
                sub_path = sub_dict[num]
                # 核心修改：处理MP4格式的输出
                original_filename = os.path.basename(video_path)
                # 1. 清理文件名中的#标记
                cleaned_filename = self.clean_filename(original_filename)
                # 2. 拆分文件名和后缀
                name_part, ext_part = os.path.splitext(cleaned_filename)
                # 3. 若原后缀是.mp4/.MP4，强制改为.mkv（兼容字幕）
                if ext_part.lower() == ".mp4":
                    final_output_filename = f"{name_part}.mkv"
                    self.write_log(f"提示：原视频是MP4格式，自动转为MKV容器（兼容字幕）→ {final_output_filename}")
                else:
                    final_output_filename = cleaned_filename
                # 4. 生成输出路径
                output_file = os.path.join(output_folder, final_output_filename)
                # 添加任务到队列
                self.task_queue.append((
                    num, video_path, sub_path, output_file,
                    final_ffmpeg_path, self.default_sub_var.get(), selected_encoding
                ))
                success_match += 1
                self.write_log(f"匹配成功：集数{num} → 原始名{original_filename} → 输出名{final_output_filename}")
            else:
                self.write_log(f"匹配失败：集数{num} 无对应字幕")

        if not self.task_queue:
            self.write_log("错误：未匹配到任何视频-字幕组合！")
            return

        # 开始执行任务
        self.write_log(f"\n===== 任务初始化完成 =====")
        self.write_log(f"共匹配{success_match}个任务，执行顺序：{','.join(sorted_nums)}")
        self.write_log(f"FFmpeg路径：{final_ffmpeg_path}")
        self.write_log(f"编码格式：{selected_encoding}")
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.execute_next_task()

    def execute_next_task(self):
        """执行下一个任务（正序）"""
        if not self.task_queue:
            self.write_log("\n===== 所有任务执行完毕 =====")
            self.is_running = False
            self.start_btn.config(state="normal")
            return

        # 取出队列第一个任务
        task = self.task_queue.pop(0)
        num, video_path, sub_path, output_file, ffmpeg_path, is_default, encoding = task
        
        self.write_log(f"\n===== 执行集数{num}（剩余{len(self.task_queue)}个） =====")
        self.write_log(f"视频：{video_path}")
        self.write_log(f"字幕：{sub_path}")
        self.write_log(f"输出：{output_file}")

        # 构建FFmpeg命令
        cmd = [
            f'"{ffmpeg_path}"', "-i", f'"{video_path}"', "-i", f'"{sub_path}"',
            "-map", "0", "-map", "1", "-c", "copy", "-y"
        ]
        # 设置默认字幕
        if is_default:
            cmd.insert(-2, "-disposition:s:1")
            cmd.insert(-2, "default")
        # 添加输出路径
        cmd.append(f'"{output_file}"')
        cmd_str = " ".join(cmd)
        self.write_log(f"执行命令：{cmd_str}")

        # 执行命令
        try:
            result = subprocess.run(
                cmd_str, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, encoding=encoding, timeout=None
            )
            if result.returncode == 0:
                self.write_log(f"✅ 集数{num}执行成功！")
            else:
                self.write_log(f"❌ 集数{num}执行失败（返回码{result.returncode}）")
                self.write_log(f"错误信息：{result.stdout.strip()}")
        except UnicodeDecodeError:
            self.write_log(f"❌ 集数{num}编码错误！请切换编码格式")
        except Exception as e:
            self.write_log(f"❌ 集数{num}异常：{str(e)}")

        # 执行下一个任务
        self.root.after(100, self.execute_next_task)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSubtitlePacker(root)
    root.mainloop()
