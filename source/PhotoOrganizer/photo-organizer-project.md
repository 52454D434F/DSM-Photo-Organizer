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

## Package Details

### Package Information
- **Package Name**: PhotoOrganizer
- **Version**: 1.0.1-0016
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
[Download PhotoOrganizer-1.0.1-00016.spk](https://github.com/52454D434F/DSM-Projects/blob/e7c6452f16fba1a8fed28b4e3d414815bd007c90/result_spk/PhotoOrganizer-1.0.1-00016/PhotoOrganizer-1.0.1-00016.spk)

## File Processing Logic

The Photo Organizer uses a file system watcher to monitor the source directory and processes each file through the following workflow:

### Processing Workflow

1. **File Detection**: The system waits 0.5 seconds after detecting a new file to ensure it's fully written (important for large files being copied)

2. **File Type Detection**: Determines if the file is an image or video based on file extension

3. **Date Extraction** (in priority order):
   - **Images**: 
     - Attempts to read EXIF `DateTimeOriginal` from top-level tags
     - If not found, searches nested EXIF data (ExifIFD) for `DateTimeOriginal`
     - Falls back to `DateTimeDigitized` if `DateTimeOriginal` is unavailable
     - Uses sophisticated multi-level EXIF parsing to handle different camera formats
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

1. **EXIF Metadata (Images)**: Reads `DateTimeOriginal` from top-level tags, then nested EXIF data (ExifIFD), with fallback to `DateTimeDigitized`. Supports both modern and legacy Pillow methods for maximum camera compatibility.
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

**Note:** Log file names were changed in v1.0.1-00017 for clarity.

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

> **Updated in v1.0.1-00017:**  
> - Statistics dump on shutdown removed from application log to reduce clutter; see `Photo_Organizer_Statistics.json` for details.
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
