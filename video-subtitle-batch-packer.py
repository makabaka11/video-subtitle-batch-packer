import os
import re
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading

class VideoSubtitlePacker:
    def __init__(self, root):
        self.root = root
        self.root.title("视频字幕批量封装工具")
        self.root.geometry("800x600")

        # 初始化变量
        self.ffmpeg_path = tk.StringVar()
        self.video_folder = tk.StringVar()
        self.subtitle_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.encoding = tk.StringVar(value="UTF-8")
        # 字幕语言变量，默认简中
        self.subtitle_language = tk.StringVar(value="简中")
        # 默认字幕选项
        self.set_default_subtitle = tk.BooleanVar(value=False)

        # 构建GUI
        self._build_gui()

    def _build_gui(self):
        # 1. FFmpeg路径配置
        ffmpeg_frame = ttk.LabelFrame(self.root, text="FFmpeg 配置(已配置环境变量可留空)")
        ffmpeg_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(ffmpeg_frame, text="FFmpeg路径：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_path, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ffmpeg_frame, text="浏览", command=self._select_ffmpeg).grid(row=0, column=2, padx=5, pady=5)

        # 2. 文件夹配置
        folder_frame = ttk.LabelFrame(self.root, text="文件夹配置")
        folder_frame.pack(fill="x", padx=10, pady=5)

        # 视频文件夹
        ttk.Label(folder_frame, text="原视频文件夹：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(folder_frame, textvariable=self.video_folder, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="浏览", command=self._select_video_folder).grid(row=0, column=2, padx=5, pady=5)

        # 字幕文件夹
        ttk.Label(folder_frame, text="字幕文件夹：").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(folder_frame, textvariable=self.subtitle_folder, width=60).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="浏览", command=self._select_subtitle_folder).grid(row=1, column=2, padx=5, pady=5)

        # 输出文件夹
        ttk.Label(folder_frame, text="输出文件夹：").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=60).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="浏览", command=self._select_output_folder).grid(row=2, column=2, padx=5, pady=5)

        # 3. 可选配置
        option_frame = ttk.LabelFrame(self.root, text="可选配置")
        option_frame.pack(fill="x", padx=10, pady=5)

        # 编码格式
        ttk.Label(option_frame, text="编码格式：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        encoding_options = ["UTF-8", "gbk", "cp936", "gb2312"]
        ttk.Combobox(option_frame, textvariable=self.encoding, values=encoding_options, state="readonly").grid(row=0, column=1, padx=5, pady=5)

        # 字幕语言选择
        ttk.Label(option_frame, text="字幕轨道语言：").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        lang_options = ["简中", "繁中", "英文"]
        ttk.Combobox(option_frame, textvariable=self.subtitle_language, values=lang_options, state="readonly").grid(row=0, column=3, padx=5, pady=5)

        # 是否设为默认字幕
        ttk.Checkbutton(option_frame, text="是否设为默认字幕", variable=self.set_default_subtitle).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # 4. 操作按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="开始批量封装", command=self._start_pack_thread).grid(row=0, column=0, padx=5, pady=5)

        # 5. 日志窗口
        log_frame = ttk.LabelFrame(self.root, text="执行日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, width=90, height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    # 文件夹选择方法
    def _select_ffmpeg(self):
        path = filedialog.askopenfilename(title="选择ffmpeg.exe", filetypes=[("可执行文件", "*.exe")])
        if path:
            self.ffmpeg_path.set(path)

    def _select_video_folder(self):
        path = filedialog.askdirectory(title="选择视频文件夹")
        if path:
            self.video_folder.set(path)

    def _select_subtitle_folder(self):
        path = filedialog.askdirectory(title="选择字幕文件夹")
        if path:
            self.subtitle_folder.set(path)

    def _select_output_folder(self):
        path = filedialog.askdirectory(title="选择输出文件夹")
        if path:
            self.output_folder.set(path)

    # 日志输出
    def _log(self, msg):
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    # 解析集数规则
    def _parse_episode_rules(self, file_list):
        # 支持列表中同时存在 #01# 和 [OVA]/[12]/[SP1] 等格式，返回可用规则列表
        rules = []
        if not file_list:
            return rules

        for fname in file_list:
            base = os.path.basename(fname)

            hash_m = re.search(r"#(\d+)#", base)
            if hash_m:
                prefix = base[:hash_m.start()]
                suffix = base[hash_m.end():]
                if not any(r["type"] == "hash" and r["prefix"] == prefix and r["suffix"] == suffix for r in rules):
                    rules.append({
                        "type": "hash",
                        "prefix": prefix,
                        "suffix": suffix,
                        "episode_pattern": r"#?(\d+)#?",
                    })

            bracket_m = re.search(r"\[(\d+|[A-Za-z]+\d*)\]", base)
            if bracket_m:
                prefix = base[:bracket_m.start()]
                suffix = base[bracket_m.end():]
                if not any(r["type"] == "bracket" and r["prefix"] == prefix and r["suffix"] == suffix for r in rules):
                    rules.append({
                        "type": "bracket",
                        "prefix": prefix,
                        "suffix": suffix,
                        "episode_pattern": r"\[(\d+|[A-Za-z]+\d*)\]",
                    })
        return rules

    # 提取文件集数
    def _extract_episode(self, filename, rules):
        for rule in rules:
            pattern = re.escape(rule["prefix"]) + rule["episode_pattern"] + re.escape(rule["suffix"])
            match = re.match(pattern, filename)
            if match:
                return match.group(1)
        return None

    def _episode_sort_key(self, ep):
        # 数字优先按数值排序，其次按字母排序，保证 OVA/ SP 系列在后
        if ep.isdigit():
            return (0, int(ep))
        return (1, ep.lower())

    def _ffprobe_path(self):
        # 如果已指定 ffmpeg.exe，则尝试使用同目录下的 ffprobe.exe，否则退回系统可执行名
        ffmpeg_exe = self.ffmpeg_path.get()
        if ffmpeg_exe and ffmpeg_exe.lower().endswith("ffmpeg.exe"):
            return os.path.join(os.path.dirname(ffmpeg_exe), "ffprobe.exe")
        return "ffprobe"

    def _count_subtitle_streams(self, video_path):
        ffprobe_exe = self._ffprobe_path()
        try:
            result = subprocess.run(
                [ffprobe_exe, "-v", "error", "-select_streams", "s", "-show_entries", "stream=index", "-of", "csv=p=0", video_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                timeout=10,
            )
            if result.returncode != 0:
                return 0
            # 每行一个字幕流索引
            lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
            return len(lines)
        except Exception:
            return 0

    # 构建FFmpeg命令
    def _build_ffmpeg_cmd(self, video_path, subtitle_path, output_path, existing_subs_count):
        # 基础命令
        ffmpeg_exe = self.ffmpeg_path.get() or "ffmpeg"
        cmd = [
            ffmpeg_exe,
            "-i", video_path,
            "-i", subtitle_path,
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "copy",
            # 保留原视频全部流，再追加外部字幕第一轨
            "-map", "0",
            "-map", "1:s:0",
        ]

        # 添加字幕轨道语言元数据
        lang_map = {
            "简中": "chi-sim",
            "繁中": "chi-tra",
            "英文": "eng"
        }
        lang_code = lang_map.get(self.subtitle_language.get(), "chi-sim")
        # 只给新增的外部字幕轨道设置语言，不覆盖原视频已有字幕语言
        cmd.extend([f"-metadata:s:s:{existing_subs_count}", f"language={lang_code}"])

        # 设置默认字幕
        if self.set_default_subtitle.get():
            # 先清除所有字幕轨的默认标记，再设置新字幕为默认
            # 这确保只有新添加的字幕是默认字幕，避免多个默认字幕造成播放器行为不一致
            cmd.extend(["-disposition:s", "-default"])
            cmd.extend([f"-disposition:s:{existing_subs_count}", "default"])

        # 编码格式
        cmd.extend(["-sub_charenc", self.encoding.get()])

        # 输出路径（覆盖已有文件）
        cmd.extend(["-y", output_path])

        return cmd

    # 批量封装核心逻辑
    def _batch_pack(self):
        # 校验配置
        if not self.video_folder.get() or not self.subtitle_folder.get() or not self.output_folder.get():
            self._log("错误：视频/字幕/输出文件夹不能为空！")
            return

        # 获取视频和字幕文件列表
        video_files = [f for f in os.listdir(self.video_folder.get()) if f.lower().endswith(("mkv", "mp4"))]
        subtitle_files = [f for f in os.listdir(self.subtitle_folder.get()) if f.lower().endswith(("ass", "srt"))]
        if not video_files or not subtitle_files:
            self._log("错误：视频文件夹或字幕文件夹中无有效文件！")
            return

        # 单文件场景：跳过集数解析，直接封装
        if len(video_files) == 1 and len(subtitle_files) == 1:
            video_path = os.path.join(self.video_folder.get(), video_files[0])
            subtitle_path = os.path.join(self.subtitle_folder.get(), subtitle_files[0])
            output_filename = os.path.basename(video_path)
            output_path = os.path.join(self.output_folder.get(), output_filename)
            existing_subs = self._count_subtitle_streams(video_path)

            self._log("检测到单个视频与单个字幕，直接封装...")
            try:
                cmd = self._build_ffmpeg_cmd(video_path, subtitle_path, output_path, existing_subs)
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding=self.encoding.get(),
                    timeout=300
                )
                if result.returncode != 0:
                    self._log(f"封装失败：{result.stderr}")
                else:
                    self._log(f"封装成功：{output_path}")
            except Exception as e:
                self._log(f"封装异常：{str(e)}")
            return

        # 解析集数规则
        video_rules = self._parse_episode_rules(video_files)
        subtitle_rules = self._parse_episode_rules(subtitle_files)
        if not video_rules or not subtitle_rules:
            self._log("错误：未找到可识别的集数标记（如 #01# 或 [OVA]/[12]/[SP1]）！")
            return

        # 构建文件-集数映射
        video_ep_map = {}
        for f in video_files:
            ep = self._extract_episode(f, video_rules)
            if ep:
                video_ep_map[ep] = os.path.join(self.video_folder.get(), f)

        subtitle_ep_map = {}
        for f in subtitle_files:
            ep = self._extract_episode(f, subtitle_rules)
            if ep:
                subtitle_ep_map[ep] = os.path.join(self.subtitle_folder.get(), f)

        # 按集数匹配并执行封装
        common_eps = sorted(set(video_ep_map.keys()) & set(subtitle_ep_map.keys()), key=self._episode_sort_key)
        if not common_eps:
            self._log("错误：未找到匹配集数的视频和字幕！")
            return

        self._log(f"找到 {len(common_eps)} 个匹配集数，开始批量封装...")
        for ep in common_eps:
            video_path = video_ep_map[ep]
            subtitle_path = subtitle_ep_map[ep]
            existing_subs = self._count_subtitle_streams(video_path)
            # 构建输出文件名（移除#标记，方括号形式保持原名）
            video_name = re.sub(r"#(\d+)#", r"\1", os.path.basename(video_path))
            output_path = os.path.join(self.output_folder.get(), video_name)

            self._log(f"开始封装 第{ep}集：{video_name}")
            try:
                # 执行FFmpeg命令
                cmd = self._build_ffmpeg_cmd(video_path, subtitle_path, output_path, existing_subs)
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding=self.encoding.get(),
                    timeout=300
                )
                if result.returncode != 0:
                    self._log(f"第{ep}集封装失败：{result.stderr}")
                else:
                    self._log(f"第{ep}集封装成功：{output_path}")
            except Exception as e:
                self._log(f"第{ep}集封装异常：{str(e)}")

        self._log("所有任务执行完毕！")

    # 启动线程执行封装（避免GUI卡死）
    def _start_pack_thread(self):
        thread = threading.Thread(target=self._batch_pack)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSubtitlePacker(root)
    root.mainloop()