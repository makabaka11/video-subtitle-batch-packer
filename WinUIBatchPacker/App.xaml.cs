using Microsoft.UI.Xaml;

namespace WinUIBatchPacker;

public partial class App : Application
{
    private Window? _window;
    private static readonly string StartupLog = Path.Combine(Path.GetTempPath(), "WinUIBatchPacker-startup.log");
    public App()
    {
        UnhandledException += (_, e) => File.WriteAllText(StartupLog, $"{DateTime.Now:O}\r\n{e.Exception}");
        InitializeComponent();
    }
    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        try { _window = new MainWindow(); _window.Activate(); }
        catch (Exception ex) { File.WriteAllText(StartupLog, $"{DateTime.Now:O}\r\n{ex}"); throw; }
    }
}
