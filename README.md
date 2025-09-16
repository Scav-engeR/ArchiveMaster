# ArchiveMaster 🗃️  
### Unified Multi-Archive Merger for ZIP, RAR, and TAR Files

### [ArchiveMaster Screenshot] <img width="1919" height="824" alt="image" src="https://github.com/user-attachments/assets/b14405b5-7df1-42e9-a306-ab0e9d621d2b" />

---

## 🔧 Overview

**ArchiveMaster** is a cross-platform desktop application and CLI tool that combines multiple archive files (ZIP, RAR, TAR, TGZ, TBZ2, etc.) into a single unified archive — preserving directory structure, metadata, and file integrity.

Whether you’re managing software releases, backup sets, or fragmented downloads, ArchiveMaster eliminates the need to manually extract and re-compress archives. It supports **multi-volume RAR** files automatically and offers both **graphical and command-line interfaces**.

> ✅ **No more manual extraction → re-zipping workflows!**

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| **Multi-format Support** | ZIP, RAR, TAR, TAR.GZ, TAR.BZ2, TGZ, TBZ2 |
| **Auto-Detect Multi-Volume RAR** | Only need to select `.part1.rar` — all other volumes found automatically |
| **Compression Control** | Choose output format (ZIP/TAR) + compression level (1–9) and type (Deflate/Gzip/Bzip2) |
| **GUI & CLI Modes** | Intuitive GUI for users + powerful CLI for automation |
| **Progress Tracking** | Real-time progress bar, file count, and elapsed time |
| **Log System** | Full operation log with timestamps — exportable to file |
| **Cancel & Resume Safe** | Graceful cancellation during processing |
| **Unicode Filename Support** | Handles non-ASCII filenames across platforms |
| **Cross-Platform** | Works on Windows, macOS, Linux |

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- `unrar` (for RAR support on Linux/macOS)

#### On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install unrar python3-pip

On macOS:

brew install unrar
On Windows:
Download and install WinRAR — it includes unrar.exe which is auto-detected.

Install Dependencies

pip install rarfile
💡 rarfile uses unrar under the hood — ensure it's in your system PATH.

🖥️ Usage
Option 1: Graphical Interface (Recommended for most users)

python3 archivemaster.py
Then:

- Click “Add Files” and select your archives.
- Select output format: ZIP, TAR, TAR.GZ, or TAR.BZ2
- Adjust compression level (1–9)
- Click “Merge Archives”
- Choose output location → Done!
⚠️ For multi-volume RAR archives, only select the first file (filename.part1.rar). All others are auto-detected.

Option 2: Command Line Interface (CLI)

python3 archivemaster.py input1.zip input2.rar input3.tar -o combined.zip --verbose
CLI Options:

usage: archivemaster.py [-h] [-o OUTPUT] [-f FORMAT] [-c COMPRESSION] [-l LEVEL] [--verbose] inputs [inputs ...]

ArchiveMaster - Combine multiple archive files

positional arguments:
  inputs                Input archive files (.zip, .rar, .tar, etc.)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output archive file path (required)
  -f FORMAT, --format FORMAT
                        Output format (zip, tar, tar.gz, tar.bz2) default: zip
  -c COMPRESSION, --compression COMPRESSION
                        Compression type (deflate, gzip, bzip2) default: deflate
  -l LEVEL, --level LEVEL
                        Compression level (1-9) default: 6
  --verbose             Enable verbose logging
Example:

# Merge multiple archives into a high-compression TAR.GZ
python3 archivemaster.py data.zip logs.rar backup.tar -o final_backup.tar.gz -f tar.gz -c gzip -l 9 --verbose

# Merge RAR volume set (only specify part1!)
python3 archivemaster.py project.part1.rar -o project_complete.zip

🛠 Technical Notes
Built with Python 3.8+ and tkinter (no external GUI frameworks).
Uses native libraries: zipfile, tarfile, rarfile.
No external binaries required beyond unrar (for RAR extraction).
Thread-safe with progress reporting.
Memory-efficient: extracts to temporary directory only; no full archive loading into RAM.

🧪 Development & Testing
Run Tests (Manual)

# Create test archives
mkdir test_archive && cd test_archive
touch file1.txt file2.txt
zip test1.zip file1.txt
zip test2.zip file2.txt
rar a test3.rar file1.txt file2.txt

# Merge them
cd ..
python3 archivemaster.py test_archive/test1.zip test_archive/test2.zip test_archive/test3.rar -o merged.zip
Build Executable (Windows/macOS/Linux)
Install PyInstaller:


pip install pyinstaller
Build standalone binary:


pyinstaller --onefile --windowed --name ArchiveMaster archivemaster.py
Output will be in dist/ArchiveMaster

🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request for:

New format support (e.g., 7z, ISO)
Dark mode UI
Batch processing from folders
Drag-and-drop file input
Dockerized version

Star this repo if you find it useful! ⭐
