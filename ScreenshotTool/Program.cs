using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        var virtualBounds = SystemInformation.VirtualScreen;

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

        using var outBmp = new Bitmap(capture.Width, capture.Height, PixelFormat.Format24bppRgb);
        using (var g2 = Graphics.FromImage(outBmp))
        {
            g2.DrawImageUnscaled(capture, 0, 0);
        }

        var path = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
            $"screenshot_{DateTime.Now:yyyyMMdd_HHmmss}.bmp"
        );

        var bmpCodec = ImageCodecInfo.GetImageEncoders()
            .First(c => c.FormatID == ImageFormat.Bmp.Guid);

        outBmp.Save(path, bmpCodec, null);

        Clipboard.SetImage(outBmp);
        Console.WriteLine($"Saved: {path}");
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

        using (var path = new GraphicsPath(FillMode.Alternate))
        {
            path.AddRectangle(ClientRectangle);
            path.AddRectangle(rect);

            using var region = new Region(path);
            e.Graphics.FillRegion(overlayBrush, region);
        }

        using (var pen = new Pen(Color.DeepSkyBlue, 2))
        {
            e.Graphics.DrawRectangle(pen, rect);
        }

        var label = $"{rect.Width} × {rect.Height}";
        var size = e.Graphics.MeasureString(label, Font);
        var labelRect = new RectangleF(rect.X, rect.Y - size.Height - 6, size.Width + 10, size.Height + 6);
        if (labelRect.Y < 0) labelRect.Y = rect.Y + 6;

        using (var bg = new SolidBrush(Color.FromArgb(170, Color.Black)))
            e.Graphics.FillRectangle(bg, labelRect);
        using (var fg = new SolidBrush(Color.White))
            e.Graphics.DrawString(label, Font, fg, labelRect.X + 5, labelRect.Y + 3);

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
