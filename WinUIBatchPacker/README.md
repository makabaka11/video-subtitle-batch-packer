# 视频字幕批量封装工具（WinUI 3 版）

这是独立的 C#/.NET WinUI 3 实现，不会替换原 Python 版本。

## 构建环境

- Visual Studio 2022/2026，安装“.NET 桌面开发”和 Windows App SDK/WinUI 工作负载；或安装官方 WinApp CLI。
- .NET 8 SDK。
- Windows App SDK `1.8.260317003`（项目已锁定版本）。

当前仓库父目录含中文。若旧版 XAML 编译器异常退出，可把 `WinUIBatchPacker` 目录复制到纯英文路径后再构建。

## 构建

```powershell
dotnet restore
dotnet build -c Release -p:Platform=x64
```

Windows App SDK 采用 self-contained 非打包部署，Release 输出目录可直接分发。

## GitHub Actions 自动构建

提交中只要包含 `WinUIBatchPacker/**` 下的改动，`.github/workflows/winui-build.yml`
就会在 `windows-latest` 上自动执行 .NET 8 自包含 x64 发布。构建成功后，在该次
Actions 运行页面下载 `WinUIBatchPacker-win-x64-<运行编号>` Artifact 即可。

工作流也支持 Pull Request 和 Actions 页面的手动运行。

> 本机当前只有 .NET 10 CLI、未安装 WinUI 工作负载。NuGet 还原成功，但旧版
> `XamlCompiler.exe` 在该环境中无诊断退出，因此尚未提交未经验证的二进制产物。
