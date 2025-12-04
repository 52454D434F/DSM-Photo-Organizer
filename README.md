# Photo Organizer and Deduplicator

## Overview

Photo Organizer and Deduplicator is an intelligent file management system designed for Synology NAS that automatically organizes photos and videos by their capture date, detects duplicates, and maintains a clean, organized photo library with minimal user intervention. The system operates as a background service that continuously monitors a designated source folder and processes files as they arrive.

## Purpose

The Photo Organizer addresses common photo management challenges:

- **Automatic Organization**: Eliminates manual sorting by automatically organizing photos into year/month-based folder structures based on when they were taken
- **Duplicate Detection and Handling**: Identifies exact duplicates using cryptographic hashing and intelligently handles them based on user preferences
- **Continuous Monitoring**: Operates as a background service that processes files in real-time as they are added to the source directory
- **Smart File Naming**: Standardizes filenames to `yyyymmdd_hhmmss.*` format for chronological organization
- **EXIF Metadata Support**: Leverages embedded photo metadata when available, with intelligent fallbacks to file system timestamps
- **Synology Integration**: Seamlessly integrates with Synology DSM, including Photo Station indexer updates and system logging

## Technology Stack

### Core Technologies

- **Python 3.7+**: Core programming language
- **Pillow (PIL)**: Image processing and EXIF metadata extraction
  - Handles nested EXIF data structures (ExifIFD)
  - Supports both modern `getexif()` and legacy `_getexif()` methods
  - Cross-platform image format support
- **watchdog**: File system monitoring and event handling
  - Cross-platform file system event detection
  - Efficient polling and event-driven architecture
- **imagehash**: Perceptual hashing for similar image detection (optional)
  - Uses average hash (aHash) algorithm
  - Detects visually similar images even with minor differences
- **hashlib**: Built-in Python library for MD5 hash calculation
  - Cryptographic-level duplicate detection
  - Fast file comparison without full content reading

### Optional Dependencies

- **mutagen**: Video metadata extraction for MP4/MOV files
  - Reads creation dates from video file metadata
  - Falls back to file timestamps if unavailable

### Synology-Specific Technologies

- **synoindex**: Synology Photo Station indexer integration
  - Updates index when files are moved or deleted
  - Ensures Photo Station recognizes organized files
- **logger / synologset1**: System logging integration
  - Logs appear in DSM Log Center
  - Provides centralized logging infrastructure

## Architecture and Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    File System Watcher                      │
│              (watchdog Observer + Handler)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  File Processing Pipeline                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ File Type    │  │ Date         │  │ Duplicate    │       │
│  │ Detection    │→ │ Extraction   │→ │ Detection    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Destination  │  │ File         │  │ Synology     │       │
│  │ Path         │→ │ Movement     │→ │ Indexer      │       │
│  │ Generation   │  │              │  │ Update       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Logging and Statistics System                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ File         │  │ System       │  │ Statistics   │       │
│  │ Operation    │  │ Events       │  │ Tracking     │       │
│  │ Log          │  │ Log          │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Management

The system uses a hierarchical configuration approach:

1. **Runtime Configuration** (`config.ini`): Primary configuration source
   - Location priority:
     - `/var/packages/PhotoOrganizer/config.ini` (Synology primary)
     - `/var/packages/PhotoOrganizer/var/config.ini` (Synology alternative)
     - `/volume1/@appstore/PhotoOrganizer/var/config.ini` (Synology fallback)
     - `./config.ini` (local development)
   - Settings:
     - Source directory path
     - Destination root directory
     - Duplicate handling policy (delete vs. keep)

2. **Default Values**: Used when no configuration file exists
   - Synology: `/volume1/photo/Photo Organizer` → `/volume1/photo/`
   - Local: `Photos\Photo Organizer` → `Photos`

## Decision Flow

### Main Processing Flow

```
File Detected
    │
    ├─→ Skip if .Zone.Identifier (Windows security file)
    │
    ├─→ Wait 0.5 seconds (ensure file is fully written)
    │
    ├─→ Determine File Type
    │   │
    │   ├─→ Image File? (jpg, jpeg, png, gif, bmp, tiff, webp, heic, heif)
    │   │
    │   ├─→ Video File? (mp4, m4v, mov, avi, mkv, wmv, flv, webm)
    │   │
    │   └─→ Unknown Type → Move to "Unknown File Types/" folder
    │                       │
    │                       └─→ Check for duplicates in Unknown folder
    │                           └─→ Handle duplicate (delete or move to Duplicates)
    │
    ├─→ Extract Date Information
    │   │
    │   ├─→ For Images:
    │   │   ├─→ Try EXIF DateTimeOriginal (top-level tag 306)
    │   │   ├─→ If not found, try nested EXIF (ExifIFD tag 34665)
    │   │   │   └─→ Read DateTimeOriginal (tag 0x9003) from ExifIFD
    │   │   │   └─→ Fallback to DateTimeDigitized (tag 0x9004)
    │   │   └─→ Fallback to file creation/modification date
    │   │
    │   └─→ For Videos:
    │       ├─→ Try video metadata (mutagen library)
    │       │   ├─→ MP4/M4V: Read ©day or \xa9day tag
    │       │   └─→ MOV: Read \xa9day tag
    │       └─→ Fallback to file creation/modification date
    │
    ├─→ Generate Destination Path
    │   │
    │   ├─→ If date found:
    │   │   ├─→ Format: YYYY/MM_Mmm/ (e.g., 2024/08_Aug/)
    │   │   ├─→ Filename: yyyymmdd_hhmmss.ext (no subseconds)
    │   │   └─→ Create destination folder if needed
    │   │
    │   └─→ If no date found:
    │       ├─→ Destination: NoDateFound/
    │       └─→ Keep original filename
    │
    ├─→ Check if Destination File Exists
    │   │
    │   ├─→ If file exists:
    │   │   ├─→ Compare file sizes (optimization)
    │   │   │   └─→ If sizes differ → Different files
    │   │   │
    │   │   ├─→ If sizes match:
    │   │   │   ├─→ Calculate MD5 hash of both files
    │   │   │   │
    │   │   │   ├─→ If hashes match (exact duplicate):
    │   │   │   │   ├─→ If DELETE_DUPLICATES = true:
    │   │   │   │   │   ├─→ Delete source file
    │   │   │   │   │   ├─→ Log "Duplicate Deleted"
    │   │   │   │   │   ├─→ Update statistics (bytes_deleted)
    │   │   │   │   │   └─→ Update Synology indexer (remove)
    │   │   │   │   │
    │   │   │   │   └─→ If DELETE_DUPLICATES = false:
    │   │   │   │       ├─→ Move to Duplicates/ folder
    │   │   │   │       ├─→ Filename: yyyymmdd_hhmmss.ssss.ext (with subseconds)
    │   │   │   │       │   └─→ Or: yyyymmdd_hhmmss.0001.ext (if no subseconds)
    │   │   │   │       ├─→ Check for duplicate in Duplicates folder first
    │   │   │   │       │   └─→ If duplicate found in Duplicates → Delete instead
    │   │   │   │       ├─→ Log "Moved to Duplicates"
    │   │   │   │       ├─→ Update statistics (bytes_moved)
    │   │   │   │       └─→ Update Synology indexer (add new location)
    │   │   │   │
    │   │   │   └─→ If hashes differ (different content, same name):
    │   │   │       ├─→ Compare modification times
    │   │   │       ├─→ Keep older file in destination
    │   │   │       ├─→ Move newer file to Duplicates/
    │   │   │       │   └─→ Check for duplicate in Duplicates folder first
    │   │   │       │       └─→ If duplicate found → Delete instead
    │   │   │       └─→ Update Synology indexer
    │   │   │
    │   │   └─→ Return (file handled)
    │   │
    │   └─→ If file doesn't exist:
    │       └─→ Continue to file movement
    │
    └─→ Move File to Destination
        ├─→ Move file using shutil.move()
        ├─→ Log "File moved" event
        ├─→ Update statistics (bytes_moved)
        └─→ Update Synology indexer (add new location)
```

### EXIF Date Extraction Flow

```
get_exif_taken_date(image_path)
    │
    ├─→ Open image with PIL.Image.open()
    │
    ├─→ Get EXIF data
    │   ├─→ Try image.getexif() (Pillow 8.0+)
    │   └─→ Fallback to image._getexif() (legacy)
    │
    ├─→ Method 1: Check top-level tags
    │   └─→ Try tag 306 (DateTimeOriginal)
    │
    ├─→ Method 2: Check nested EXIF (ExifIFD)
    │   ├─→ Access ExifIFD using get_ifd(0x8769)
    │   ├─→ Read tag 0x9003 (DateTimeOriginal) from ExifIFD
    │   └─→ Fallback to tag 0x9004 (DateTimeDigitized)
    │
    ├─→ Method 3: Alternative ExifIFD access
    │   └─→ Try direct tag 34665 access
    │
    ├─→ Method 4: Iterate through all tags
    │   └─→ Search for DateTimeOriginal, DateTime, or DateTimeDigitized
    │
    └─→ Parse date string
        ├─→ Format: 'YYYY:MM:DD HH:MM:SS'
        └─→ Return datetime object
```

### Duplicate Detection Flow

```
check_duplicate_md5_in_folder(file_path, folder_path)
    │
    ├─→ Calculate MD5 hash of source file
    │   └─→ Read file in chunks (64KB) for efficiency
    │
    ├─→ Iterate through all files in folder
    │   ├─→ Calculate MD5 hash of each file
    │   └─→ Compare hashes
    │
    └─→ Return path to duplicate if found, None otherwise
```

## Technical Implementation Details

### File System Monitoring

The system uses the `watchdog` library to monitor the source directory:

- **Observer Pattern**: Uses `watchdog.observers.Observer` to watch for file system events
- **Event Handler**: Custom `PhotoHandler` class extends `FileSystemEventHandler`
- **Event Types Handled**:
  - `on_created`: New file detected
  - `on_moved`: File moved/renamed (external operations)
- **Periodic Check**: Additional 10-second interval check for unprocessed files (mitigates WSL/path issues)

### Date Extraction Implementation

#### EXIF Metadata (Images)

The system implements a multi-level EXIF extraction strategy:

1. **Top-Level Tags**: First checks standard EXIF tag 306 (DateTimeOriginal)
2. **Nested EXIF (ExifIFD)**: Many modern cameras store metadata in nested structures
   - Accesses ExifIFD using Pillow's `get_ifd(0x8769)` method
   - Reads DateTimeOriginal (tag 0x9003) from within ExifIFD
   - Falls back to DateTimeDigitized (tag 0x9004) if DateTimeOriginal unavailable
3. **Legacy Support**: Handles both `getexif()` (Pillow 8.0+) and `_getexif()` (older versions)
4. **Format Parsing**: Handles standard EXIF format `YYYY:MM:DD HH:MM:SS`

#### Video Metadata

- **MP4/M4V**: Reads `©day` or `\xa9day` tags using mutagen library
- **MOV**: Reads `\xa9day` tag from QuickTime metadata
- **Format Support**: ISO 8601 formats (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`)

#### File Timestamps

- Uses the older of creation time or modification time
- Preserves sub-second precision (microseconds) when available
- Provides reliable fallback for files without embedded metadata

### Duplicate Detection Algorithm

#### Exact Duplicate Detection (MD5 Hash)

1. **Size Comparison** (optimization): First compares file sizes
   - If sizes differ → Files are different (skip hash calculation)
   - If sizes match → Proceed to hash comparison
2. **MD5 Hash Calculation**: 
   - Reads file in 64KB chunks for memory efficiency
   - Calculates cryptographic MD5 hash
   - Compares hashes of both files
3. **Result**: 
   - Identical hash → Exact duplicate
   - Different hash → Different files (even with same name)

#### Duplicate Handling in Duplicates Folder

Before moving a file to the Duplicates folder:
1. Calculate MD5 hash of file to be moved
2. Scan all files in Duplicates folder
3. Compare hashes to find exact matches
4. If duplicate found: Delete the file instead of moving it
5. Prevents accumulation of multiple identical duplicates

### Filename Formatting

#### Destination Folder Format
- **Format**: `yyyymmdd_hhmmss.ext`
- **Example**: `20250214_134757.jpg`
- **No subseconds**: Clean, consistent naming for organized files
- **Used for**: Existence checks and file organization

#### Duplicates Folder Format
- **With subseconds**: `yyyymmdd_hhmmss.ssss.ext` (e.g., `20250214_134757.3519.jpg`)
  - Uses actual subseconds from file timestamp when available
  - Provides unique identification based on capture time precision
- **Without subseconds**: `yyyymmdd_hhmmss.0001.ext`, `yyyymmdd_hhmmss.0002.ext`, etc.
  - Sequential numbering ensures unique filenames
  - Starts from 0001 and increments as needed

### Logging System

#### Log Files

1. **Photo_Organizer.log**: Detailed file operation log
   - Format: `Log, Time, IP address, User, Event, File/Folder, File size, File name, Additional Info`
   - Tracks: File moves, deletes, duplicates, errors
   - Location: Destination directory

2. **System.log**: System events log
   - Format: `Level, Log, Time, User, Event`
   - Tracks: Service start/stop, dependency checks, statistics
   - Log levels: Info, Warning, Error
   - Location: Destination directory

#### Logging Methods

1. **System Logger** (`logger` command): Integrates with Synology Log Center
2. **Synology Logging** (`synologset1`): Additional DSM integration
3. **Package Log Files**: Plain text files for detailed operation history

### Statistics Tracking

The system maintains in-memory statistics:

- **Bytes Moved**: Total size of files successfully organized
- **Bytes Deleted**: Total size of duplicate files removed

Statistics are logged when:
1. **Service Stops**: Final statistics logged before shutdown
2. **Idle Timeout**: After 60 seconds of no file activity, statistics logged and counters reset

### Synology Integration

#### Photo Indexer Integration

- **File Deletion**: `synoindex -D <file_path>` removes deleted files from index
- **File Movement**: 
  - `synoindex -D <old_path>` removes old location
  - `synoindex -A <new_path>` adds new location
- **Error Handling**: Silently handles cases where `synoindex` is unavailable
- **Timeout Protection**: 5-second timeout prevents hanging

#### Path Conversion

- Converts user-visible paths to system paths for logging
- Example: `/volume1/photo/Photo Organizer/file.jpg` → `/var/services/photo/Photo Organizer/file.jpg`
- Enables compatibility with Synology's Log Center

## Requirements

- **Python**: 3.7 or higher
- **Required Dependencies**:
  - [Pillow](https://python-pillow.org/) - Image processing and EXIF extraction
  - [watchdog](https://python-watchdog.readthedocs.io/) - File system monitoring
  - [imagehash](https://github.com/JohannesBuchner/imagehash) - Perceptual hashing (optional, for similar image detection)
- **Optional Dependencies**:
  - [mutagen](https://mutagen.readthedocs.io/) - Video metadata extraction (optional)

## Installation

### For Synology NAS

1. Download the `.spk` package file
2. Open Synology Package Center
3. Click "Manual Install" and select the downloaded `.spk` file
4. Follow the installation wizard
5. Configure source and destination directories during setup

### For Local Development

1. Install Python 3.7+ from [python.org](https://www.python.org/downloads/)
2. Install required packages:
   ```bash
   pip install Pillow watchdog imagehash mutagen
   ```
3. Create `config.ini` file:
   ```ini
   [paths]
   source_dir = Photos/Photo Organizer
   destination_root = Photos

   [duplicates]
   delete = true
   ```
4. Run the script:
   ```bash
   python Photo_Organizer.py
   ```

## Usage

Once installed and running, the service operates automatically:

1. Place photos in the configured source directory (default: `Photos/Photo Organizer`)
2. The service automatically processes existing photos
3. New photos added to the folder are automatically organized
4. Photos are sorted into year/month-based folders with consistent naming
5. Duplicates are detected and handled according to configuration

## Features

- **Automatic folder monitoring**: Continuously watches for new files using watchdog
- **Multi-level EXIF extraction**: Handles both top-level and nested EXIF data structures
- **Smart date fallback**: Uses file timestamps when metadata unavailable
- **Intelligent file renaming**: Standardizes to `yyyymmdd_hhmmss.*` format
- **Cryptographic duplicate detection**: MD5 hash comparison for exact duplicates
- **Optimized performance**: Size comparison before hash calculation
- **Year/month organization**: Files organized into `YYYY/MM_Mmm/` structure
- **Synology integration**: Photo Station indexer updates and system logging
- **Comprehensive logging**: Detailed operation logs and system event tracking
- **Statistics tracking**: Monitors bytes moved and deleted

## Notes

- Files are processed from the configured source directory
- Files with dates are renamed and organized by year/month
- Files without date information are moved to `NoDateFound/` with original filename
- Unknown file types are moved to `Unknown File Types/` folder
- **Duplicate handling**:
  - Exact duplicates (same MD5 hash) are deleted or moved to `Duplicates/` based on configuration
  - Files with same name but different content: older file kept, newer moved to `Duplicates/`
  - Duplicates folder checks prevent accumulation of identical files
- Destination folders are created automatically as needed
- The service includes periodic checks to handle files that may be missed by the file watcher

## License

Copyright (c) 2025 MORCE.codes

This package provides automatic photo organization functionality for Synology NAS. The Photo Organizer and Deduplicator application is provided as-is for organizing photos based on EXIF metadata.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/52454D434F/Photo-Organizer)
