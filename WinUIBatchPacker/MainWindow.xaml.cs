using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace WinUIBatchPacker;

public sealed partial class MainWindow : Window
{
    private bool _refreshing;
    private readonly TextBox FfmpegBox = new();
    private readonly TextBox VideoFolderBox = new();
    private readonly TextBox SubtitleFolderBox = new();
    private readonly TextBox InputFolderBox = new();
    private readonly TextBox OutputFolderBox = new();
    private readonly CheckBox SameFolderCheck = new() { Content = "视频和字幕位于同一个文件夹" };
    private readonly CheckBox ReplaceCheck = new() { Content = "封装成功后安全替换原视频" };
    private readonly CheckBox DefaultSubtitleCheck = new() { Content = "将新增的第一条字幕设为默认轨道" };
    private readonly Grid SeparateFoldersPanel = new();
    private readonly Grid InputFolderPanel = new();
    private readonly Grid OutputFolderPanel = new();
    private readonly ComboBox EncodingBox = new();
    private readonly ComboBox LanguageBox = new();
    private readonly ProgressBar Progress = new() { Minimum = 0, Maximum = 1, Height = 4 };
    private readonly TextBox LogBox = new() { Height = 190, AcceptsReturn = true, IsReadOnly = true, TextWrapping = TextWrapping.Wrap, FontFamily = new Microsoft.UI.Xaml.Media.FontFamily("Consolas") };
    private readonly TextBlock MatchInfo = new() { Text = "请选择输入路径", TextWrapping = TextWrapping.Wrap };
    private readonly MediaListView VideoList = new();
    private readonly MediaListView SubtitleList = new();

    public MainWindow()
    {
        InitializeComponent();
        BuildInterface();
        VideoList.HeaderText = "视频文件";
        SubtitleList.HeaderText = "字幕组";
        VideoList.SelectionChangedByCheck += ListCheckChanged;
        SubtitleList.SelectionChangedByCheck += ListCheckChanged;
        VideoList.Reordered += ListReordered;
        SubtitleList.Reordered += ListReordered;
        AppWindow.Resize(new Windows.Graphics.SizeInt32(1720, 900));
    }

    private void BuildInterface()
    {
        SameFolderCheck.Checked += FolderModeChanged; SameFolderCheck.Unchecked += FolderModeChanged;
        ReplaceCheck.Checked += ReplaceModeChanged; ReplaceCheck.Unchecked += ReplaceModeChanged;
        VideoFolderBox.TextChanged += FolderTextChanged; SubtitleFolderBox.TextChanged += FolderTextChanged; InputFolderBox.TextChanged += FolderTextChanged;
        EncodingBox.Items.Add("UTF-8"); EncodingBox.Items.Add("gbk"); EncodingBox.Items.Add("cp936"); EncodingBox.Items.Add("gb2312"); EncodingBox.Items.Add("big5"); EncodingBox.SelectedIndex = 0;
        LanguageBox.Items.Add("简体中文"); LanguageBox.Items.Add("繁体中文"); LanguageBox.Items.Add("英语"); LanguageBox.SelectedIndex = 0;

        var root = new Grid { Padding = new Thickness(20), ColumnSpacing = 16, Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 244, 246, 249)) };
        root.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(620) }); root.ColumnDefinitions.Add(new ColumnDefinition());
        var left = new StackPanel { Spacing = 14, Margin = new Thickness(0, 0, 6, 0) };
        left.Children.Add(new TextBlock { Text = "视频字幕批量封装", FontSize = 30, FontWeight = Windows.UI.Text.FontWeights.SemiBold });

        var ff = new StackPanel { Spacing = 10 }; ff.Children.Add(Heading("FFmpeg")); ff.Children.Add(new TextBlock { Text = "已加入系统 PATH 时可以留空", Opacity = .62 });
        FfmpegBox.PlaceholderText = "ffmpeg.exe 路径"; ff.Children.Add(PathRow(FfmpegBox, "选择文件", PickFfmpeg_Click)); left.Children.Add(Card(ff));

        var folders = new StackPanel { Spacing = 12 }; folders.Children.Add(Heading("文件位置")); folders.Children.Add(SameFolderCheck);
        ConfigureFolderGrid(SeparateFoldersPanel, true); AddFolderRow(SeparateFoldersPanel, VideoFolderBox, "视频文件夹", PickVideoFolder_Click, 0); AddFolderRow(SeparateFoldersPanel, SubtitleFolderBox, "字幕文件夹", PickSubtitleFolder_Click, 1); folders.Children.Add(SeparateFoldersPanel);
        ConfigureFolderGrid(InputFolderPanel, false); AddFolderRow(InputFolderPanel, InputFolderBox, "输入文件夹", PickInputFolder_Click, 0); InputFolderPanel.Visibility = Visibility.Collapsed; folders.Children.Add(InputFolderPanel);
        folders.Children.Add(ReplaceCheck); ConfigureFolderGrid(OutputFolderPanel, false); AddFolderRow(OutputFolderPanel, OutputFolderBox, "输出文件夹", PickOutputFolder_Click, 0); folders.Children.Add(OutputFolderPanel); left.Children.Add(Card(folders));

        var subs = new StackPanel { Spacing = 12 }; subs.Children.Add(Heading("字幕选项"));
        var combos = new Grid { ColumnSpacing = 12 }; combos.ColumnDefinitions.Add(new ColumnDefinition()); combos.ColumnDefinitions.Add(new ColumnDefinition()); EncodingBox.Header = "文件编码"; LanguageBox.Header = "未知后缀语言"; Grid.SetColumn(LanguageBox, 1); combos.Children.Add(EncodingBox); combos.Children.Add(LanguageBox); subs.Children.Add(combos); subs.Children.Add(DefaultSubtitleCheck); left.Children.Add(Card(subs));

        var logs = new StackPanel { Spacing = 10 }; var logHead = new Grid(); logHead.ColumnDefinitions.Add(new ColumnDefinition()); logHead.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto }); logHead.Children.Add(Heading("执行日志")); var clear = Button("清空", ClearLog_Click); Grid.SetColumn(clear, 1); logHead.Children.Add(clear); logs.Children.Add(logHead); logs.Children.Add(Progress); logs.Children.Add(LogBox); var start = Button("开始批量封装", StartPack_Click); start.HorizontalAlignment = HorizontalAlignment.Stretch; logs.Children.Add(start); left.Children.Add(Card(logs));
        var scroll = new ScrollViewer { Content = left, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled }; root.Children.Add(scroll);

        var right = new Grid { RowSpacing = 12 }; right.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); right.RowDefinitions.Add(new RowDefinition()); right.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); Grid.SetColumn(right, 1);
        right.Children.Add(new TextBlock { Text = "匹配方案", FontSize = 24, FontWeight = Windows.UI.Text.FontWeights.SemiBold });
        var lists = new Grid { ColumnSpacing = 12 }; lists.ColumnDefinitions.Add(new ColumnDefinition()); lists.ColumnDefinitions.Add(new ColumnDefinition()); Grid.SetRow(lists, 1); Grid.SetColumn(SubtitleList, 1); lists.Children.Add(VideoList); lists.Children.Add(SubtitleList); right.Children.Add(lists);
        var info = new Border { Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 232, 241, 251)), BorderBrush = new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 184, 214, 242)), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(8), Padding = new Thickness(12), Child = MatchInfo }; Grid.SetRow(info, 2); right.Children.Add(info); root.Children.Add(right); Content = root;
    }

    private static TextBlock Heading(string text) => new() { Text = text, FontSize = 18, FontWeight = Windows.UI.Text.FontWeights.SemiBold };
    private static Border Card(UIElement child) => new() { Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Colors.White), BorderBrush = new Microsoft.UI.Xaml.Media.SolidColorBrush(Windows.UI.Color.FromArgb(255, 225, 229, 234)), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(12), Padding = new Thickness(18), Child = child };
    private static Button Button(string text, RoutedEventHandler click) { var b = new Button { Content = text }; b.Click += click; return b; }
    private static Grid PathRow(TextBox box, string label, RoutedEventHandler click) { var g = new Grid { ColumnSpacing = 8 }; g.ColumnDefinitions.Add(new ColumnDefinition()); g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto }); var b = Button(label, click); Grid.SetColumn(b, 1); g.Children.Add(box); g.Children.Add(b); return g; }
    private static void ConfigureFolderGrid(Grid grid, bool twoRows) { grid.ColumnSpacing = 8; grid.RowSpacing = 10; grid.ColumnDefinitions.Add(new ColumnDefinition()); grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto }); grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); if (twoRows) grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); }
    private static void AddFolderRow(Grid grid, TextBox box, string header, RoutedEventHandler click, int row) { box.Header = header; var b = Button("浏览", click); b.Margin = new Thickness(0, 25, 0, 0); Grid.SetRow(box, row); Grid.SetRow(b, row); Grid.SetColumn(b, 1); grid.Children.Add(box); grid.Children.Add(b); }

    private IntPtr Hwnd => WindowNative.GetWindowHandle(this);
    private async Task<string?> PickFolder()
    {
        var picker = new FolderPicker(); picker.FileTypeFilter.Add("*"); InitializeWithWindow.Initialize(picker, Hwnd);
        return (await picker.PickSingleFolderAsync())?.Path;
    }
    private async void PickVideoFolder_Click(object s, RoutedEventArgs e) { var p = await PickFolder(); if (p != null) VideoFolderBox.Text = p; }
    private async void PickSubtitleFolder_Click(object s, RoutedEventArgs e) { var p = await PickFolder(); if (p != null) SubtitleFolderBox.Text = p; }
    private async void PickInputFolder_Click(object s, RoutedEventArgs e) { var p = await PickFolder(); if (p != null) InputFolderBox.Text = p; }
    private async void PickOutputFolder_Click(object s, RoutedEventArgs e) { var p = await PickFolder(); if (p != null) OutputFolderBox.Text = p; }
    private async void PickFfmpeg_Click(object s, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker(); picker.FileTypeFilter.Add(".exe"); InitializeWithWindow.Initialize(picker, Hwnd);
        var file = await picker.PickSingleFileAsync(); if (file != null) FfmpegBox.Text = file.Path;
    }
    private void FolderModeChanged(object s, RoutedEventArgs e)
    {
        var same = SameFolderCheck.IsChecked == true;
        SeparateFoldersPanel.Visibility = same ? Visibility.Collapsed : Visibility.Visible;
        InputFolderPanel.Visibility = same ? Visibility.Visible : Visibility.Collapsed;
        RefreshLists();
    }
    private void ReplaceModeChanged(object s, RoutedEventArgs e) => OutputFolderPanel.Visibility = ReplaceCheck.IsChecked == true ? Visibility.Collapsed : Visibility.Visible;
    private void FolderTextChanged(object s, TextChangedEventArgs e) => RefreshLists();
    private void RefreshLists()
    {
        if (_refreshing || VideoList == null) return; _refreshing = true;
        try
        {
            var same = SameFolderCheck.IsChecked == true;
            var videoFolder = same ? InputFolderBox.Text.Trim() : VideoFolderBox.Text.Trim();
            var subtitleFolder = same ? InputFolderBox.Text.Trim() : SubtitleFolderBox.Text.Trim();
            VideoList.SetItems(MediaService.LoadVideos(videoFolder)); SubtitleList.SetItems(MediaService.LoadSubtitleGroups(subtitleFolder)); UpdateMatchInfo();
        }
        catch (Exception ex) { AppendLog($"扫描失败：{ex.Message}"); }
        finally { _refreshing = false; }
    }
    private void ListCheckChanged(object? s, EventArgs e) => UpdateMatchInfo();
    private void ListReordered(object? s, EventArgs e) => UpdateMatchInfo();
    private void UpdateMatchInfo()
    {
        var videos = VideoList.SelectedRows().Count; var subtitles = SubtitleList.SelectedRows().Count; var matched = videos > 0 && videos == subtitles;
        MatchInfo.Text = matched ? $"✓ 当前将按序号处理 {videos} 对" : $"已选视频 {videos} 个，字幕组 {subtitles} 个；数量必须相等";
    }
    private async void StartPack_Click(object sender, RoutedEventArgs e)
    {
        var videos = VideoList.SelectedRows(); var subtitles = SubtitleList.SelectedRows();
        if (videos.Count == 0 || videos.Count != subtitles.Count) { AppendLog("错误：两侧已选数量必须相等且不能为零。"); return; }
        var replace = ReplaceCheck.IsChecked == true; var output = OutputFolderBox.Text.Trim();
        if (!replace && output.Length == 0) { AppendLog("错误：请选择输出文件夹。"); return; }
        if (!replace) Directory.CreateDirectory(output);
        var encoding = EncodingBox.SelectedItem?.ToString() ?? "UTF-8";
        var language = LanguageBox.SelectedItem?.ToString() ?? "简体中文";
        var options = new PackOptions(FfmpegBox.Text.Trim(), encoding, language, DefaultSubtitleCheck.IsChecked == true, replace, output);
        Progress.Maximum = videos.Count; Progress.Value = 0; AppendLog($"开始处理 {videos.Count} 对。");
        for (var i = 0; i < videos.Count; i++)
        {
            var video = videos[i].Paths[0]; var subs = MediaService.Deduplicate(subtitles[i].Paths);
            var target = replace ? Path.Combine(Path.GetDirectoryName(video)!, $".__muxing_{Guid.NewGuid():N}{Path.GetExtension(video)}") : Path.Combine(output, Path.GetFileName(video));
            if (!replace && Path.GetFullPath(target).Equals(Path.GetFullPath(video), StringComparison.OrdinalIgnoreCase)) { AppendLog($"#{i + 1} 跳过：输出与原视频路径相同。"); continue; }
            AppendLog($"#{i + 1} {Path.GetFileName(video)}：加入 {subs.Count} 条字幕");
            try
            {
                var result = await MediaService.Pack(video, subs, target, options);
                if (result.Code != 0) { AppendLog($"#{i + 1} 失败：{result.Output[^Math.Min(2000, result.Output.Length)..]}"); if (replace && File.Exists(target)) File.Delete(target); }
                else { if (replace) File.Move(target, video, true); AppendLog($"#{i + 1} 完成"); }
            }
            catch (Exception ex) { AppendLog($"#{i + 1} 异常：{ex.Message}"); if (replace && File.Exists(target)) File.Delete(target); }
            Progress.Value = i + 1;
        }
        AppendLog("全部任务执行完毕。");
    }
    private void AppendLog(string text) => LogBox.Text += $"[{DateTime.Now:HH:mm:ss}] {text}\r\n";
    private void ClearLog_Click(object sender, RoutedEventArgs e) => LogBox.Text = "";
}
