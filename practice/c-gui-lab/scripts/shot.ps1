# Bring the window (found by title keyword, ASCII only) to front and capture its rect.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/shot.ps1 -Contains "GTK4 Style" -Out build/screenshots/gtk.png
param(
  [Parameter(Mandatory = $true)][string]$Contains,
  [Parameter(Mandatory = $true)][string]$Out
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class Win32Shot {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)]
  public static extern int GetWindowText(IntPtr hWnd, StringBuilder sb, int max);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left, Top, Right, Bottom; }

  public static IntPtr FindByTitle(string keyword) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, l) => {
      if (!IsWindowVisible(h)) return true;
      var sb = new StringBuilder(256);
      GetWindowText(h, sb, 256);
      if (sb.ToString().Contains(keyword)) { found = h; return false; }
      return true;
    }, IntPtr.Zero);
    return found;
  }
}
"@

$h = [Win32Shot]::FindByTitle($Contains)
if ($h -eq [IntPtr]::Zero) {
  Write-Output "WINDOW-NOT-FOUND: $Contains"
  exit 1
}
[Win32Shot]::SetProcessDPIAware() | Out-Null
[Win32Shot]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 900

$r = New-Object Win32Shot+RECT
[Win32Shot]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Right - $r.Left
$hgt = $r.Bottom - $r.Top
if ($w -le 0 -or $hgt -le 0) {
  Write-Output "BAD-RECT"
  exit 1
}
$bmp = New-Object System.Drawing.Bitmap($w, $hgt)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size($w, $hgt)))
$bmp.Save($Out)
Write-Output "SHOT-OK ${w}x${hgt} -> $Out"
