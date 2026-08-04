# ps2exe

PowerShell to EXE compiler. Wraps PS1 scripts in native Windows executables using `csc.exe` (built into Windows).

## Features

- No external dependencies (uses .NET Framework's csc.exe)
- Custom icon support (.ico)
- Hidden window execution (no console flash)
- Small output (~4KB + encoded script size)

## Usage

### Convert a command
```powershell
python ps2exe.py "whoami" -o test.exe
```

### Convert a PS1 file
```powershell
python ps2exe.py -f payload.ps1 -o payload.exe
```

### With custom icon
```powershell
python ps2exe.py -f script.ps1 -o app.exe --icon myicon.ico
```

### Console app (shows output)
```powershell
python ps2exe.py "Get-Process" -o procs.exe --wait
```

### Encode only (no compile)
```powershell
python ps2exe.py "whoami" --encode-only
# Output: base64 encoded command for -EncodedCommand
```

## Options

| Flag | Description |
|------|-------------|
| `-f`, `--file` | Read PowerShell from .ps1 file |
| `-o`, `--output` | Output exe name (default: payload.exe) |
| `--icon` | Path to .ico file |
| `--wait` | Wait for command, show output (console app) |
| `--encode-only` | Just print base64 encoded command |

## How it works

1. Reads PowerShell command/script
2. Encodes to Base64 (UTF-16LE - required by PowerShell)
3. Generates C# wrapper that calls `powershell.exe -EncodedCommand`
4. Compiles with `csc.exe` (ships with Windows)

## PowerShell flags used

```
-NoP        No profile (faster startup)
-NonI       Non-interactive
-W Hidden   Hidden window
-Exec Bypass   Skip execution policy
-EncodedCommand   Base64 encoded script
```

## Icon

`zip.ico` included. Place any `.ico` in the same directory and reference with `--icon`.

## Requirements

- Python 3.x
- Windows with .NET Framework (csc.exe)
