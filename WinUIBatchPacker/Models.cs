using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace WinUIBatchPacker;

public sealed class MediaRow : INotifyPropertyChanged
{
    private bool _isSelected = true;
    private string _number = "";
    public required string DisplayName { get; init; }
    public required IReadOnlyList<string> Paths { get; init; }
    public string Episode { get; init; } = "";
    public bool IsSelected { get => _isSelected; set { if (_isSelected != value) { _isSelected = value; Changed(); } } }
    public string Number { get => _number; set { if (_number != value) { _number = value; Changed(); } } }
    public event PropertyChangedEventHandler? PropertyChanged;
    private void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
}

public sealed record PackOptions(string Ffmpeg, string Encoding, string FallbackLanguage,
    bool DefaultSubtitle, bool ReplaceOriginal, string OutputFolder);
