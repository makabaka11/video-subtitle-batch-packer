using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace WinUIBatchPacker;

public sealed class MediaRow : INotifyPropertyChanged
{
    private bool _isSelected = true;
    private string _number = "";
    // WinUI's generated XAML type metadata constructs models through a default
    // constructor and property setters, so these cannot be required/init-only.
    public string DisplayName { get; set; } = "";
    public IReadOnlyList<string> Paths { get; set; } = Array.Empty<string>();
    public string Episode { get; set; } = "";
    public bool IsSelected { get => _isSelected; set { if (_isSelected != value) { _isSelected = value; Changed(); } } }
    public string Number { get => _number; set { if (_number != value) { _number = value; Changed(); } } }
    public event PropertyChangedEventHandler? PropertyChanged;
    private void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
}

public sealed record PackOptions(string Ffmpeg, string Encoding, string FallbackLanguage,
    bool DefaultSubtitle, bool ReplaceOriginal, string OutputFolder);
