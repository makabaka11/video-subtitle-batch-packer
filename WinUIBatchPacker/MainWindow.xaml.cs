using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace WinUIBatchPacker;

public sealed partial class MainWindow : Window
{
    private bool _refreshing;

    public MainWindow()
    {
        InitializeComponent();
        VideoList.HeaderText = "视频文件";
        SubtitleList.HeaderText = "字幕组";
        VideoList.SelectionChangedByCheck += ListCheckChanged;
        SubtitleList.SelectionChangedByCheck += ListCheckChanged;
        VideoList.Reordered += ListReordered;
        SubtitleList.Reordered += ListReordered;
        AppWindow.Resize(new Windows.Graphics.SizeInt32(1720, 900));
    }

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
        MatchInfo.Severity = matched ? InfoBarSeverity.Success : InfoBarSeverity.Warning;
        MatchInfo.Message = matched ? $"当前将按序号处理 {videos} 对" : $"已选视频 {videos} 个，字幕组 {subtitles} 个；数量必须相等";
    }
    private async void StartPack_Click(object sender, RoutedEventArgs e)
    {
        var videos = VideoList.SelectedRows(); var subtitles = SubtitleList.SelectedRows();
        if (videos.Count == 0 || videos.Count != subtitles.Count) { AppendLog("错误：两侧已选数量必须相等且不能为零。"); return; }
        var replace = ReplaceCheck.IsChecked == true; var output = OutputFolderBox.Text.Trim();
        if (!replace && output.Length == 0) { AppendLog("错误：请选择输出文件夹。"); return; }
        if (!replace) Directory.CreateDirectory(output);
        var encoding = (EncodingBox.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "UTF-8";
        var language = (LanguageBox.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "简体中文";
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
