using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Linq;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main()
    {
        var bounds = SystemInformation.VirtualScreen;

        using var capture = new Bitmap(bounds.Width, bounds.Height, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(capture))
        {
            g.CopyFromScreen(bounds.Left, bounds.Top, 0, 0, bounds.Size);
        }

        using var outBmp = new Bitmap(capture.Width, capture.Height, PixelFormat.Format24bppRgb);
        using (var g2 = Graphics.FromImage(outBmp))
        {
            g2.DrawImageUnscaled(capture, 0, 0);
        }

        var path = System.IO.Path.Combine(
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
