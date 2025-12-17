+++
date = '2025-12-01T14:23:59-06:00'
draft = false
title = 'Photo Organizer and Deduplicator'
tags = ['synology', 'dsm', 'photo-management', 'automation', 'python', 'package']
image = 'images/icon_256.png'
+++

# Synology DSM 7 Package
{{< img src="/images/icon_256.png" alt="Photo Organizer Icon" style="width: 256px; height: 256px; max-width: 256px;" >}}

## Table of Contents

1. [Overview](#overview)
2. [Package Details](#package-details)
3. [GitHub Repository](#github-repository)
4. [Download](#download)
5. [File Processing Logic](#file-processing-logic)
6. [Duplicate Handling](#duplicate-handling)
7. [Statistics Tracking](#statistics-tracking)
8. [Logging](#logging)
9. [Synology Integration](#synology-integration)
10. [License](#license)
11. [Support](#support)

## Overview

Photo Organizer and Deduplicator is a Synology NAS package that automatically organizes and manages your photo collection. The application continuously monitors a designated folder and automatically sorts photos by their capture date, detects duplicates, and organizes your entire photo library with minimal user intervention.

### Key Features

- **Automatic Folder Monitoring**: Continuously watches a user-defined source directory and processes new files as they are added
- **Intelligent Date Detection**: Extracts date from EXIF metadata (with nested EXIF support), video metadata, or file timestamps
- **Automatic Organization**: Sorts photos into year/month-based folders (`YYYY/MM_Mmm/`) with consistent `yyyymmdd_hhmmss.ext` naming
- **Duplicate Detection**: Uses MD5 hash comparison to identify exact duplicates, with configurable handling (delete or move to Duplicates folder)
- **File Renaming**: Automatically renames files to consistent chronological format when date information is available

### Recent Highlights

> **🔴 Critical Fixes in Latest Versions:**
> 
> - **v1.0.1-00019**: Fixed critical statistics tracking bug - statistics now update immediately after file moves, ensuring 100% accuracy even if logging fails
> - **v1.0.1-00018**: Fixed EXIF date extraction priority - photos now organized by actual capture date (nested ExifIFD tags) instead of file modification date
> 
> **✨ Major Improvements:**
> 
> - **Persistent Statistics**: JSON-based statistics tracking that persists across restarts (`Photo_Organizer_Statistics.json`)
> - **Enhanced Date Detection**: Added CreateDate tag support and fixed priority order to use actual photo capture dates
> - **Improved Logging**: Enhanced log entries with destination format information for better traceability

## Package Details

### Package Information
- **Package Name**: PhotoOrganizer
- **Version**: 1.0.1-00029
- **Display Name**: Photo Organizer and Deduplicator
- **Architecture**: noarch (works on all Synology NAS models)
- **Minimum DSM Version**: 7.0-40000
- **Maintainer**: MORCE.codes
- **Type**: Third-party package

### Technical Requirements
- **Python**: 3.7 or higher
- **Dependencies**:
  - [Pillow](https://python-pillow.org/) - For reading EXIF data and image processing
  - [watchdog](https://python-watchdog.readthedocs.io/) - For folder monitoring
  - [imagehash](https://github.com/JohannesBuchner/imagehash) - Optional dependency (currently not used in duplicate detection)
  - [mutagen](https://mutagen.readthedocs.io/) - Optional dependency for video metadata extraction (MP4/MOV files)
  - hashlib - Built-in Python library for MD5 hash calculation

### Installation
1. Download the `.spk` file (see download link below)
2. Open Synology Package Center
3. Click "Manual Install" and select the downloaded `.spk` file
4. Follow the installation wizard
5. Configure the source and destination directories during setup

### Usage
Once installed, the service runs automatically in the background:
1. Place photos in the configured source directory (default: `Photos/Photo Organizer`)
2. The service automatically processes existing photos
3. New photos added to the folder are automatically organized
4. Photos are sorted into year-based folders with consistent naming
5. Duplicates are detected and handled according to the configured settings

## GitHub Repository

[View on GitHub](https://github.com/52454D434F/DSM-Projects)

The project source code, build scripts, and documentation are available on GitHub. Contributions, bug reports, and feature requests are welcome!

## Download

### Latest Version:
[Download PhotoOrganizer-1.0.1-00029.spk](https://github.com/52454D434F/DSM-Photo-Organizer/blob/main/result_spk/PhotoOrganizer-1.0.1-00029/PhotoOrganizer-1.0.1-00029.spk)

**Recent Updates:**

- **v1.0.1-00029** (2025-12-XX)
  - **Temporary File Detection**: Added automatic detection and skipping of temporary files created during Synology/SMB transfers (pattern: `.<filename>.<random6chars>`)
  - **File Stability Checking**: Enhanced file processing to wait for files to be fully written before processing, preventing errors during active transfers
  - **Improved Transfer Handling**: Better reliability when processing files during active SMB/Synology file transfers

- **v1.0.1-00026** (2025-12-XX)
  - **Improved Indexer Reliability**: Enhanced error handling for Synology indexer operations with proper timeout management (5-second timeout)
  - **Better Error Isolation**: Indexer failures no longer affect file operations - improved separation of concerns
  - **Logging Refactoring**: Refactored logging in `update_synology_indexer` and related functions for improved reliability

- **v1.0.1-00019** (2025-12-05) - **CRITICAL FIX**
  - **Fixed Critical Statistics Tracking Bug**: Statistics are now updated immediately after file move operations complete, ensuring all file moves are accurately counted even if logging or Synology indexer operations fail
  - Statistics update order changed: statistics update immediately after `shutil.move()` succeeds, before any logging or indexer operations
  - Ensures data integrity: if a file is moved, it's always counted in statistics
  - Applied to all file move operations (normal organization, unknown file types, file replacements)

- **v1.0.1-00018** (2025-12-04) - **CRITICAL FIX**
  - **Fixed EXIF Date Extraction Priority Order**: Now correctly prioritizes nested ExifIFD tags over top-level tags
  - **New Priority Order** (highest to lowest):
    1. Nested ExifIFD DateTimeOriginal (tag 0x9003) - **HIGHEST PRIORITY**
    2. Nested ExifIFD DateTimeDigitized (tag 0x9004)
    3. Nested ExifIFD CreateDate
    4. Top-level DateTimeOriginal
    5. Top-level DateTimeDigitized
    6. Top-level CreateDate
    7. Top-level DateTime (tag 0x0132) - **LOWEST PRIORITY**
  - **Added CreateDate EXIF Tag Support**: Added support for extracting CreateDate tag from EXIF metadata (both top-level and nested ExifIFD)
  - **Enhanced Log Entries**: All log entries now include destination file format information for better traceability
  - **Impact**: Photos are now organized by their actual capture date, not when they were last modified

- **v1.0.1-00017** (2025-12-03)
  - **Persistent Statistics Tracking System**: Implemented JSON-based statistics file (`Photo_Organizer_Statistics.json`) that persists across restarts
  - **Statistics Adjustment Logic**: Automatically adjusts statistics when files move between destination and duplicates folders
  - **Improved Log File Naming**: 
    - `Photo_Organizer.log` → `Photo_Organizer_Activities.log`
    - `System.log` → `Photo_Organizer_Application.log`
    - `statistics.json` → `Photo_Organizer_Statistics.json`
  - **Fixed Mutagen Dependency Detection**: Properly detects mutagen when installed in virtual environment
  - **Fixed Video Metadata Extraction**: Fixed MOV file metadata extraction (removed dependency on non-existent QuickTime module)

## File Processing Logic

The Photo Organizer uses a file system watcher to monitor the source directory and processes each file through the following workflow:

### Processing Workflow

1. **File Detection**: The system waits 0.5 seconds after detecting a new file to ensure it's fully written (important for large files being copied)

2. **File Type Detection**: Determines if the file is an image or video based on file extension

3. **Date Extraction** (in priority order):
   - **Images**: 
     - **Priority 1**: Nested ExifIFD `DateTimeOriginal` (tag 0x9003) - **HIGHEST PRIORITY** - Most accurate capture date
     - **Priority 2**: Nested ExifIFD `DateTimeDigitized` (tag 0x9004)
     - **Priority 3**: Nested ExifIFD `CreateDate` *(Added in v1.0.1-00018)*
     - **Priority 4**: Top-level `DateTimeOriginal`
     - **Priority 5**: Top-level `DateTimeDigitized`
     - **Priority 6**: Top-level `CreateDate` *(Added in v1.0.1-00018)*
     - **Priority 7**: Top-level `DateTime` (tag 0x0132) - **LOWEST PRIORITY** - File modification date
     - Uses sophisticated multi-level EXIF parsing to handle different camera formats
     - > **🔴 Critical Fix (v1.0.1-00018)**: Nested ExifIFD tags are now correctly prioritized over top-level tags. This ensures **actual photo capture date is used instead of file modification date**. Previously, the script incorrectly checked top-level DateTime (file modification date) before nested DateTimeOriginal (actual capture date).
   - **Videos**: Attempts to read creation date from video metadata (MP4/MOV using mutagen library)
   - **Fallback**: Uses the older of file creation or modification timestamp (newer might have modifications)

4. **Destination Path Generation**:
   - If date found: Creates path `YYYY/MM_Mmm/` (e.g., `2024/08_Aug/`)
   - Filename format: `yyyymmdd_hhmmss.ext` (without subseconds for destination folder)
   - If no date found: Moves to `NoDateFound/` folder with original filename

5. **Duplicate Check**: Before moving, checks if a file with the same name already exists at the destination:
   - **Size Comparison**: First compares file sizes (fast optimization)
   - **MD5 Hash Check**: If sizes match, compares MD5 hashes
   - **Exact Duplicate**: If hashes match, handles according to `DELETE_DUPLICATES` setting
   - **Different Content**: If hashes differ, compares modification times and keeps older file

6. **File Movement**: Moves the file to the appropriate destination folder:
   - Files are renamed to consistent `yyyymmdd_hhmmss.ext` format when date is available
   - Original filenames preserved for files without date information
   - Duplicates are handled according to the configured strategy

### Date Extraction Methods

The application uses multiple methods to extract date information in priority order:

1. **EXIF Metadata (Images)**: 
   - **Nested ExifIFD tags (highest priority)**: Reads `DateTimeOriginal`, `DateTimeDigitized`, and `CreateDate` from nested ExifIFD structure (tag 0x8769)
   - **Top-level tags (fallback)**: Reads `DateTimeOriginal`, `DateTimeDigitized`, `CreateDate`, and `DateTime` from top-level EXIF tags
   - **Priority order ensures actual photo capture date is used**: Nested ExifIFD tags contain the most accurate capture metadata and are checked first
   - Supports both modern and legacy Pillow methods for maximum camera compatibility
   - > **🔴 Critical Fix (v1.0.1-00018)**: Fixed incorrect priority order that was using file modification date before actual capture date. Now correctly prioritizes nested ExifIFD tags (actual capture date) over top-level tags (file modification date). Added support for `CreateDate` tag in both nested and top-level EXIF structures.
2. **Video Metadata**: Reads creation date from MP4/MOV metadata using mutagen library, supporting ISO 8601 format.
3. **File Timestamps**: Uses the older of creation or modification time, preserving sub-second precision when available.

## Duplicate Handling

The application uses MD5 hash comparison for duplicate detection, with file size comparison first for performance optimization.

### Handling Strategies

- **Exact Duplicates (Same MD5 Hash)**: 
  - If `DELETE_DUPLICATES = true` (default): Duplicate is deleted immediately
  - If `DELETE_DUPLICATES = false`: Duplicate is moved to `Duplicates/` folder with subseconds/sequential naming

- **Different Content (Same Filename, Different Hash)**:
  - Keeps the older file in destination folder
  - Moves newer file to `Duplicates/` folder
  - Before moving to Duplicates, checks if an identical file already exists there (to prevent accumulation)
  - If duplicate found in Duplicates folder, deletes current file instead of moving it

### Filename Formats

- **Destination Folder**: `yyyymmdd_hhmmss.ext` (no subseconds)
- **Duplicates Folder**: `yyyymmdd_hhmmss.ssss.ext` (with subseconds when available) or `yyyymmdd_hhmmss.0001.ext` (sequential numbering)

Before moving a file to the Duplicates folder, the system checks if an identical file (same MD5 hash) already exists there. If found, the current file is deleted instead of creating another duplicate, ensuring efficient storage usage.

## Statistics Tracking

The application maintains statistics about file operations, tracking files/bytes moved to destination folders, moved to Duplicates, and deleted (duplicates). Statistics are stored persistently in `Photo_Organizer_Statistics.json`, automatically loaded on startup, and adjusted when files move between destination and Duplicates folders.

### Statistics Accuracy

> **🔴 Critical Fix (v1.0.1-00019)**: Statistics are now updated **immediately after file move operations complete**, ensuring all files are accurately counted even if logging or indexer operations fail. This guarantees data integrity: **if a file is moved, it's always counted in statistics**.
> 
> **What Changed:**
> - Statistics update moved to execute immediately after `shutil.move()` succeeds
> - Logging and indexer updates are wrapped in separate try-except blocks
> - Non-critical operation failures (logging, indexer) no longer prevent statistics updates
> - Applied to all file move operations: normal organization, unknown file types, and file replacements

### Statistics Data

The `Photo_Organizer_Statistics.json` file tracks:
- `files_moved_to_destination`: Total number of files moved to organized folders
- `bytes_moved_to_destination`: Total bytes moved to organized folders
- `files_moved_to_duplicates`: Total number of files moved to Duplicates folder
- `bytes_moved_to_duplicates`: Total bytes moved to Duplicates folder
- `files_deleted`: Total number of duplicate files deleted
- `bytes_deleted`: Total bytes deleted (duplicates)
- `last_updated`: Timestamp of last statistics update

### Statistics Persistence

- Statistics are automatically saved periodically (every 10 operations or 30 seconds timeout, whichever comes first)
- Statistics persist across application restarts
- Statistics are adjusted when files move between destination and Duplicates folders
- File locking support ensures thread-safe statistics updates on Unix/Linux systems

Statistics are automatically logged when:
- Service stops (final statistics before shutdown)
- Service is idle for 1 minute (logged before counter reset)

Logged format: `Info, System, YYYY/MM/DD HH:MM:SS, PhotoOrganizer, Statistics (reason): X.XX GB moved, X.XX MB deleted`

## Logging

The application uses multiple logging methods for reliability: system logger (accessible via DSM Log Center), Synology-specific logging, and package log files stored in the destination directory.

### Log Files

1. **`Photo_Organizer_Activities.log`** - Detailed file operation log
   - Tracks all file operations, moves, deletions, and duplicate handling
   - Format: `Log, Time, IP address, User, Event, File/Folder, File size, File name, Additional Info`

2. **`Photo_Organizer_Application.log`** - System and application events log
   - Records service start/stop, dependency checks, and system-level events
   - Format: `Level, Log, Time, User, Event` (Info, Warning, Error)

3. **`Photo_Organizer_Statistics.json`** - Persistent statistics file (see Statistics Tracking section)

### Logged Events

**File Operations**: File detected, file moved (with rename info), duplicate deleted, moved to duplicates (with reason), file moved/renamed, errors

**System Events**: Service started/stopped, dependency checks, statistics (see Statistics Tracking section)

### Viewing Logs

- **Via File Station or SSH**: Log files located in destination directory (default: `/volume1/photo/`)
  ```bash
  tail -n 50 /volume1/photo/Photo_Organizer_Activities.log
  tail -n 50 /volume1/photo/Photo_Organizer_Application.log
  ```

- **Via DSM Log Center**: Filter by tag `PhotoOrganizer` (Control Panel → Log Center → System Logs)

### Log Format Details

#### File Operation Log Format
Each entry in `Photo_Organizer_Activities.log` contains (in order):
- **Time**: Timestamp in `YYYY-MM-DD HH:MM:SS` format
- **IP address**: Local IP address of the NAS at the time of the operation
- **User**: System user running the service
- **File name**: Base filename (without folder path)
- **File size**: Human-readable file size (e.g., "2.45 MB")
- **Event**: Operation performed (e.g., "File moved", "Duplicate Deleted", "Moved to Duplicates", etc.)
- **Additional Info**: Contextual operation details (e.g., "Renamed to ...", "Moved from destination to duplicates - Different content", etc.)
- **File/Folder**: Full file system path affected by the operation (final path after move or deletion)

> **Updated in v1.0.1-00017:**  
> - Improved event descriptions for moved/deleted files, including statistics adjustments.
> - Some operations may log both old and new destination paths when moving between destination and duplicates folders.
> - Moved files from destination to duplicates folder will decrease destination stats and increase duplicates stats (see `Photo_Organizer_Statistics.json`).

#### System/Application Log Format
Each entry in `Photo_Organizer_Application.log` contains:
- **Level**: Log level (e.g., Info, Warning, Error)
- **Log**: Fixed value "System"
- **Time**: Timestamp in `YYYY/MM/DD HH:MM:SS` format
- **User**: System user running the service
- **Event**: Description of system or application event (e.g., "Service Started", "Service Stopped", dependencies checked, statistics saved, errors, etc.)

- Application log now focuses on service events, startup/shutdown, and critical errors.
- Log file path and naming updated for clarity in this version.

## Synology Integration

The Photo Organizer is specifically designed to integrate seamlessly with Synology DiskStation Manager (DSM), providing native NAS functionality.

### Synology Detection

The application automatically detects if it's running on a Synology NAS by checking:
- Presence of `/etc/synoinfo.conf`
- DSM version file at `/etc.defaults/VERSION`
- Standard Synology volume path `/volume1`

### Photo Indexer Integration

The application automatically updates Synology's photo indexer (`synoindex`) after file operations: removes deleted files from index (`synoindex -D`), updates index when files are moved (removes old path, adds new path), and silently handles cases where indexer is unavailable. This ensures Photo Station stays synchronized with file organization.

### Configuration

- **Paths**: Uses volume-based paths (default: `/volume1/photo/`), configurable during installation and stored in `config.ini`
- **Config File Locations**: `/var/packages/PhotoOrganizer/config.ini`, `/var/packages/PhotoOrganizer/var/config.ini`, or `/volume1/@appstore/PhotoOrganizer/var/config.ini` (searched in order)
- **Service Management**: Installs as `.spk` package through Package Center, can be started/stopped via Package Center interface

## License

Copyright (c) 2025 MORCE.codes

This package provides automatic photo organization functionality for Synology NAS. The Photo Organizer and Deduplicator application is provided as-is for organizing photos based on EXIF metadata.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/52454D434F/DSM-Projects/issues)

---

**Note**: This package is designed specifically for Synology DiskStation Manager (DSM) and requires a Synology NAS running DSM 7.0 or later.
