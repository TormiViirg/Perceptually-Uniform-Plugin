using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows.Forms;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {

        DpiAwareness.EnablePerMonitorV2BestEffort();

        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        var virtualBounds = Win32Screen.GetVirtualScreenBoundsPx();

        Rectangle region;
        if (args.Any(a => a.Equals("--snip", StringComparison.OrdinalIgnoreCase)))
        {
            var snip = SnipForm.GetSelection(virtualBounds);
            if (snip is null) return;
            region = snip.Value;
        }
        else
        {
            region = virtualBounds;
        }

        using var capture = new Bitmap(region.Width, region.Height, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(capture))
        {
            g.CopyFromScreen(region.Left, region.Top, 0, 0, region.Size, CopyPixelOperation.SourceCopy);
        }

        var outputDir = OutputDirectory.GetOutputDirectory(args);
        Directory.CreateDirectory(outputDir);

        // BMP is uncompressed by default (BI_RGB). This avoids any lossy artifacts.
        var path = Path.Combine(outputDir, $"screenshot_{DateTime.Now:yyyyMMdd_HHmmss}.bmp");
        capture.Save(path, ImageFormat.Bmp);

        // Put it on the clipboard (Windows stores a bitmap/DIB; no JPEG-style loss).
        Clipboard.SetImage(capture);

        Console.WriteLine($"Saved: {path}");
    }
}

internal static class OutputDirectory
{
    private static string ConfigPath()
        => Path.Combine(AppContext.BaseDirectory, "screenshottool.config");

    private static string BuiltInDefault()
        => Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);

    private static string ConfiguredDefault()
    {
        var cfg = ConfigPath();
        if (File.Exists(cfg))
        {
            var text = File.ReadAllText(cfg).Trim();
            if (!string.IsNullOrWhiteSpace(text))
                return text;
        }
        return BuiltInDefault();
    }

    private static void SetConfiguredDefault(string path)
    {
        Directory.CreateDirectory(path);
        File.WriteAllText(ConfigPath(), path);
    }

    public static string GetOutputDirectory(string[] args)
    {
        var setIdx = Array.FindIndex(args, a => a.Equals("--set-default", StringComparison.OrdinalIgnoreCase));
        if (setIdx >= 0 && setIdx + 1 < args.Length && !string.IsNullOrWhiteSpace(args[setIdx + 1]))
        {
            var newDefault = Path.GetFullPath(args[setIdx + 1]);
            SetConfiguredDefault(newDefault);
            return newDefault;
        }

        var outIdx = Array.FindIndex(args, a =>
            a.Equals("--out", StringComparison.OrdinalIgnoreCase) ||
            a.Equals("--dir", StringComparison.OrdinalIgnoreCase));

        if (outIdx >= 0 && outIdx + 1 < args.Length && !string.IsNullOrWhiteSpace(args[outIdx + 1]))
            return Path.GetFullPath(args[outIdx + 1]);

        return ConfiguredDefault();
    }
}

internal sealed class SnipForm : Form
{
    private readonly Rectangle _virtualBounds;
    private Bitmap? _background;
    private Point? _start;
    private Point _current;

    public Rectangle SelectedRectangle { get; private set; }

    private SnipForm(Rectangle virtualBounds)
    {
        _virtualBounds = virtualBounds;

        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.Manual;
        Bounds = virtualBounds;
        TopMost = true;
        ShowInTaskbar = false;
        DoubleBuffered = true;
        Cursor = Cursors.Cross;
        KeyPreview = true;
    }

    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);

        _background = new Bitmap(_virtualBounds.Width, _virtualBounds.Height, PixelFormat.Format32bppArgb);
        using var g = Graphics.FromImage(_background);
        g.CopyFromScreen(_virtualBounds.Left, _virtualBounds.Top, 0, 0, _virtualBounds.Size, CopyPixelOperation.SourceCopy);

        Invalidate();
    }

    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (e.KeyCode == Keys.Escape)
        {
            DialogResult = DialogResult.Cancel;
            Close();
            return;
        }
        base.OnKeyDown(e);
    }

    protected override void OnMouseDown(MouseEventArgs e)
    {
        if (e.Button != MouseButtons.Left) return;
        _start = e.Location;
        _current = e.Location;
        Invalidate();
        base.OnMouseDown(e);
    }

    protected override void OnMouseMove(MouseEventArgs e)
    {
        if (_start is null) return;
        _current = e.Location;
        Invalidate();
        base.OnMouseMove(e);
    }

    protected override void OnMouseUp(MouseEventArgs e)
    {
        if (e.Button != MouseButtons.Left || _start is null) return;

        _current = e.Location;
        var rectClient = NormalizeRect(_start.Value, _current);

        if (rectClient.Width < 2 || rectClient.Height < 2)
        {
            DialogResult = DialogResult.Cancel;
            Close();
            return;
        }

        var topLeft = PointToScreen(rectClient.Location);
        SelectedRectangle = new Rectangle(topLeft, rectClient.Size);

        DialogResult = DialogResult.OK;
        Close();

        base.OnMouseUp(e);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        if (_background != null)
            e.Graphics.DrawImageUnscaled(_background, 0, 0);

        using var overlayBrush = new SolidBrush(Color.FromArgb(120, Color.Black));

        if (_start is null)
        {
            e.Graphics.FillRectangle(overlayBrush, ClientRectangle);
            base.OnPaint(e);
            return;
        }

        var rect = NormalizeRect(_start.Value, _current);

        using (var path = new System.Drawing.Drawing2D.GraphicsPath(System.Drawing.Drawing2D.FillMode.Alternate))
        {
            path.AddRectangle(ClientRectangle);
            path.AddRectangle(rect);

            using var region = new Region(path);
            e.Graphics.FillRegion(overlayBrush, region);
        }

        using (var pen = new Pen(Color.DeepSkyBlue, 2))
            e.Graphics.DrawRectangle(pen, rect);

        base.OnPaint(e);
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) _background?.Dispose();
        base.Dispose(disposing);
    }

    private static Rectangle NormalizeRect(Point a, Point b)
    {
        var x1 = Math.Min(a.X, b.X);
        var y1 = Math.Min(a.Y, b.Y);
        var x2 = Math.Max(a.X, b.X);
        var y2 = Math.Max(a.Y, b.Y);
        return Rectangle.FromLTRB(x1, y1, x2, y2);
    }

    public static Rectangle? GetSelection(Rectangle virtualBounds)
    {
        using var f = new SnipForm(virtualBounds);
        return f.ShowDialog() == DialogResult.OK ? f.SelectedRectangle : (Rectangle?)null;
    }
}

internal static class DpiAwareness
{
    private static readonly IntPtr DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = new IntPtr(-4);

    [DllImport("user32.dll")]
    private static extern bool SetProcessDpiAwarenessContext(IntPtr value);

    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();

    public static void EnablePerMonitorV2BestEffort()
    {
        try
        {
            SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        }
        catch (EntryPointNotFoundException)
        {
            try { SetProcessDPIAware(); } catch { /* ignore */ }
        }
        catch
        {
            // Non-fatal; continue.
        }
    }
}

internal static class Win32Screen
{
    private const int SM_XVIRTUALSCREEN = 76;
    private const int SM_YVIRTUALSCREEN = 77;
    private const int SM_CXVIRTUALSCREEN = 78;
    private const int SM_CYVIRTUALSCREEN = 79;

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int nIndex);

    public static Rectangle GetVirtualScreenBoundsPx()
    {
        var x = GetSystemMetrics(SM_XVIRTUALSCREEN);
        var y = GetSystemMetrics(SM_YVIRTUALSCREEN);
        var w = GetSystemMetrics(SM_CXVIRTUALSCREEN);
        var h = GetSystemMetrics(SM_CYVIRTUALSCREEN);
        return new Rectangle(x, y, w, h);
    }
}
