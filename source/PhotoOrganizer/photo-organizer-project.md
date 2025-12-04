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
2. [Purpose](#purpose)
3. [Key Features](#key-features)
4. [Package Details](#package-details)
5. [GitHub Repository](#github-repository)
6. [Download](#download)
7. [How It Works](#how-it-works)
8. [File Processing Logic](#file-processing-logic)
9. [Duplicate Handling](#duplicate-handling)
10. [Statistics Tracking](#statistics-tracking)
11. [Logging](#logging)
12. [Synology Integration](#synology-integration)
13. [License](#license)
14. [Support](#support)

## Overview

Photo Organizer and Deduplicator is a Synology NAS package that automatically organizes and manages your photo collection. This intelligent application continuously monitors a designated folder and automatically sorts photos by their capture date, detects duplicates, and organizes your entire photo library with minimal user intervention.

## Purpose

The Photo Organizer script is designed to solve common photo management challenges:

- **Automatic Organization**: Automatically sorts photos into year-based folders based on when they were taken
- **Duplicate Detection**: Identifies and handles both exact duplicates and visually similar images
- **Continuous Monitoring**: Watches a source folder and processes new photos as they arrive
- **Smart File Naming**: Renames files to a consistent `yyyymmdd_hhmmss.*` format for easy organization
- **EXIF Metadata Support**: Uses photo metadata when available, with intelligent fallbacks

## Key Features

### Automatic Folder Monitoring
The application continuously watches a user-defined source directory (`Photos/PhotosToProcess` by default) and automatically processes new files as they are added.

### Intelligent Date Detection
- **Primary Method**: Extracts date from EXIF metadata (`DateTimeOriginal`) when available
  - Checks top-level EXIF tags first
  - Searches nested EXIF data (ExifIFD) for cameras that store metadata in nested structures
  - Falls back to `DateTimeDigitized` if `DateTimeOriginal` is unavailable
  - Handles various EXIF storage formats for maximum compatibility
- **Fallback Method**: Uses file creation or modification date if EXIF data is missing
- **Smart Organization**: Files are organized into year-based subfolders (e.g., `Photos/2024/`)

### Duplicate Detection
- **Exact Duplicates**: Uses MD5 hash comparison to identify identical files
- **Smart Handling**: 
  - Exact duplicates can be deleted or moved to `Duplicates` folder based on configuration
  - When files have same destination name but different content, keeps the older file and moves newer to Duplicates
  - Prevents duplicate accumulation by checking Duplicates folder before moving files there
  - Files in Duplicates folder use subseconds format (`yyyymmdd_hhmmss.ssss.ext`) for unique identification

### File Renaming
Files with date information are automatically renamed to `yyyymmdd_hhmmss.*` format, making it easy to find and organize photos chronologically.

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
1. Place photos in the configured source directory (default: `Photos/PhotosToProcess`)
2. The service automatically processes existing photos
3. New photos added to the folder are automatically organized
4. Photos are sorted into year-based folders with consistent naming
5. Duplicates are detected and handled according to the configured settings

## GitHub Repository

[View on GitHub](https://github.com/52454D434F/DSM-Projects)

The project source code, build scripts, and documentation are available on GitHub. Contributions, bug reports, and feature requests are welcome!

## Download

### Latest Version: 1.0.1-00016
[Download PhotoOrganizer-1.0.x-xxxxx.spk](https://github.com/52454D434F/DSM-Projects/blob/e7c6452f16fba1a8fed28b4e3d414815bd007c90/result_spk/PhotoOrganizer-1.0.1-00016/PhotoOrganizer-1.0.1-00016.spk)

## How It Works

1. **Monitoring**: The service uses a file system watcher to detect new files in the source directory
2. **Processing**: When a new photo is detected:
   - EXIF metadata is extracted to determine the capture date
   - If EXIF data is unavailable, file timestamps are used
   - The photo is renamed to `yyyymmdd_hhmmss.ext` format (if date is available)
   - The photo is checked against existing files at the destination for duplicates
3. **Duplicate Detection**: 
   - File sizes are compared first (fast optimization)
   - If sizes match, MD5 hashes are compared to identify exact duplicates
   - If hashes differ but filenames match, modification times are compared
4. **Organization**: Photos are moved to appropriate year-based folders (`YYYY/MM_Mmm/`) with consistent naming
5. **Duplicate Handling**: 
   - Exact duplicates are deleted or moved to `Duplicates/` folder based on configuration
   - When files have different content but same name, the older file is kept in destination, newer file moved to Duplicates
   - Before moving to Duplicates, checks if an identical file already exists there to prevent duplicate accumulation

## File Processing Logic

The Photo Organizer uses a sophisticated multi-step process to handle each file that appears in the source directory.

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
   - **Fallback**: Uses the older of file creation or modification timestamp

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

#### EXIF Metadata (Images)
The application uses a sophisticated multi-level approach to extract date information from EXIF metadata:

1. **Top-Level Tags**: First attempts to read `DateTimeOriginal` (tag 306) from top-level EXIF tags
2. **Nested EXIF Data (ExifIFD)**: If not found at top level, checks nested EXIF data:
   - Accesses ExifIFD (tag 34665 / 0x8769) using Pillow's `get_ifd()` method (Pillow 8.0+)
   - Reads `DateTimeOriginal` (tag 0x9003 / 36867) from within the ExifIFD
   - Falls back to `DateTimeDigitized` (tag 0x9004) if `DateTimeOriginal` is unavailable
   - Alternative access methods for compatibility with different EXIF structures
3. **Legacy Support**: Supports both modern `getexif()` and legacy `_getexif()` Pillow methods for compatibility
4. **Format**: EXIF date format is `YYYY:MM:DD HH:MM:SS` (no milliseconds in EXIF standard)
5. **Sub-Second Precision**: Preserves sub-second precision from file timestamps when EXIF is unavailable

This multi-level approach ensures maximum compatibility with different camera models and image processing software, as many modern cameras store date information in nested EXIF structures (ExifIFD) rather than top-level tags. The application automatically handles both storage methods, ensuring accurate date extraction regardless of how the camera or software stores the metadata.

#### Video Metadata
- For MP4/M4V files: Reads creation date from MP4 metadata tags (`©day` or `\xa9day`)
- For MOV files: Reads creation date from QuickTime metadata
- Supports ISO 8601 format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
- Falls back to file timestamps if metadata unavailable

#### File Timestamps
- Uses the older of creation time or modification time
- Preserves sub-second precision (microseconds) when available
- Works for both images and videos when metadata is missing
- Provides reliable fallback for files without embedded metadata

## Duplicate Handling

The application implements intelligent duplicate detection and handling to prevent storage waste and maintain a clean photo library.

### Duplicate Detection Process

1. **Fast Size Check**: First compares file sizes - if different, files are not duplicates (performance optimization)

2. **MD5 Hash Comparison**: If sizes match, calculates MD5 hash of both files
   - MD5 hash provides cryptographic-level duplicate detection
   - Only performed when file sizes match (optimization)
   - Ensures 100% accuracy in identifying identical files

3. **Content Comparison**: If hashes match, files are identical duplicates

### Duplicate Handling Strategies

#### Exact Duplicates (Same MD5 Hash)

When a file with the same destination filename and identical content (same MD5 hash) is detected:

**If `DELETE_DUPLICATES = true`** (default):
- The duplicate file is deleted immediately
- Statistics track bytes deleted
- Synology indexer is updated to remove the file from index
- No storage space wasted on duplicates

**If `DELETE_DUPLICATES = false`**:
- Duplicate is moved to `Duplicates/` folder
- Filename format: `yyyymmdd_hhmmss.ssss.ext` (with subseconds if available)
- If subseconds not available: `yyyymmdd_hhmmss.0001.ext`, `yyyymmdd_hhmmss.0002.ext`, etc.
- Statistics track bytes moved
- Preserves all files for manual review

#### Different Content (Same Filename, Different Hash)

When files have the same destination filename but different content (different MD5 hash):

1. **Modification Time Comparison**: Compares file modification times to determine which file is older
2. **Keep Older File**: The older (earlier modified) file stays in the destination folder
3. **Move Newer File**: The newer (later modified) file is moved to `Duplicates/` folder
4. **Pre-Duplicate Check**: Before moving to Duplicates folder, checks if an identical file (same MD5 hash) already exists in Duplicates folder
   - **If duplicate found in Duplicates**: Deletes the current file instead of creating another duplicate
   - **If no duplicate found**: Moves the file with unique subseconds/sequential naming
5. **Source Replacement**: If the destination file was moved to Duplicates (because it was newer), the source file replaces it in the destination folder

### Filename Formats

#### Destination Folder
- Format: `yyyymmdd_hhmmss.ext`
- Example: `20250214_134757.jpg`
- No subseconds included (clean, consistent naming)
- Used for existence checks and organization
- Files are renamed to this format when moved to date-based folders

#### Duplicates Folder
- **With subseconds**: `yyyymmdd_hhmmss.ssss.ext` (e.g., `20250214_134757.3519.jpg`)
  - Uses actual subseconds from file timestamp when available
  - Provides unique identification based on capture time precision
  - Format: 4-digit subsecond value (milliseconds from microseconds)
- **Without subseconds**: `yyyymmdd_hhmmss.0001.ext`, `yyyymmdd_hhmmss.0002.ext`, etc.
  - Sequential numbering ensures unique filenames
  - Starts from 0001 and increments as needed
  - Used when subseconds are not available from file metadata
- **Fallback naming**: If filename doesn't match date pattern, uses original name with sequential suffix: `originalname.0001.ext`

### Duplicate Detection in Duplicates Folder

Before moving a file to the Duplicates folder, the system performs an additional duplicate check:

1. **MD5 Hash Calculation**: Calculates MD5 hash of the file to be moved
2. **Folder Scan**: Scans all files in the Duplicates folder
3. **Hash Comparison**: Compares hashes to find exact matches
4. **Duplicate Found**: If an identical file (same MD5 hash) already exists in Duplicates folder:
   - Deletes the current file instead of moving it
   - Logs as "Duplicate Deleted" with reference to existing duplicate
   - Updates statistics (bytes deleted)
   - Updates Synology indexer
5. **No Duplicate Found**: If no match is found:
   - Moves the file with unique subseconds/sequential naming
   - Ensures Duplicates folder only contains unique files

This prevents accumulation of multiple identical duplicates in the Duplicates folder, ensuring efficient storage usage even when `DELETE_DUPLICATES = false`.

## Statistics Tracking

The application maintains comprehensive statistics about file operations to help users understand the service's activity.

### Tracked Metrics

- **Bytes Moved**: Total size of files successfully organized and moved to destination folders
- **Bytes Deleted**: Total size of duplicate files removed from the system

### Statistics Logging

Statistics are automatically logged in the system log when:

1. **Service Stops**: When the service is stopped (graceful shutdown or signal)
   - Final statistics are always logged before shutdown
   - Prevents loss of statistics data

2. **Idle Timeout**: After 1 minute (60 seconds) of no file activity
   - Statistics are logged with reason "timeout" before resetting counters
   - Counters reset to zero after logging
   - Prevents statistics from growing indefinitely
   - Provides periodic activity summaries

3. **Manual Reset**: Statistics can be reset programmatically

### Statistics Format

Logged entries appear in `System.log` with format:
```
Info, System, 2025/01/15 14:30:22, PhotoOrganizer, Statistics (service stopped): 2.45 GB moved, 150.30 MB deleted
```

The format includes:
- Log level: `Info`
- Log type: `System`
- Timestamp: `YYYY/MM/DD HH:MM:SS`
- User: System user running the service
- Event: Description with formatted byte counts

### Statistics Reset Behavior

- Statistics reset automatically after 1 minute of idle time
- Reset prevents counters from accumulating over long periods
- Each reset logs the accumulated statistics before clearing
- Service stop always logs final statistics (even if recently reset)
- Prevents duplicate logging on exit through flag management

### Performance Considerations

- Statistics are tracked in memory (global variables)
- Minimal performance impact on file operations
- Logging is asynchronous and doesn't block file processing
- Byte counters use efficient integer arithmetic

## Logging

Photo Organizer includes comprehensive logging capabilities to track all operations, system events, and file activities. The logging system uses multiple methods to ensure reliability and compatibility with Synology DSM.

### Log Files

The application maintains two primary log files in the destination directory:

1. **`Photo_Organizer.log`** - Detailed file operation log
   - Tracks all file operations (moves, deletes, duplicates)
   - Records file detection events
   - Includes file size, timestamps, IP addresses, and user information
   - Format: `Log, Time, IP address, User, Event, File/Folder, File size, File name, Additional Info`

2. **`System.log`** - System events log
   - Records service start/stop events
   - Logs dependency checks and system status
   - Tracks statistics (bytes moved/deleted)
   - Format: `Level, Log, Time, User, Event`
   - Log levels: Info, Warning, Error

### Logging Methods

The application uses multiple logging methods for maximum reliability:

1. **System Logger** (`logger` command)
   - Integrates with Synology's system logging infrastructure
   - Messages are accessible through DSM's Log Center
   - Tag: `PhotoOrganizer`
   - Priority: `user.info`

2. **Synology Logging** (`synologset1`)
   - Synology-specific logging method
   - Provides additional integration with DSM logging system
   - Used as a fallback if standard logger is unavailable

3. **Package Log Files**
   - Plain text log files stored in the destination directory
   - Always accessible to the package user
   - Provides detailed operation history
   - Can be viewed with any text editor or log viewer

### Logged Events

The following events are logged:

#### File Operations
- **File Detected**: New file detected in source directory
- **File Moved**: File successfully moved to destination (includes "Renamed to" info when applicable)
- **Duplicate Deleted**: Exact duplicate removed (either from source or from Duplicates folder)
- **Moved to Duplicates**: Duplicate file moved to Duplicates folder (includes reason: "Exact duplicate", "Newer file", or "Older file")
- **File Moved/Renamed**: External file move/rename detected by watchdog
- **Error**: Any error during file processing

#### System Events
- **Service Started**: Application initialization
- **Service Stopped**: Application shutdown
- **Dependency Check**: Verification of required Python packages
- **Statistics**: Summary of bytes moved and deleted (logged on service stop or idle timeout)

### Log File Locations

On Synology NAS, log files are stored in:
- Default location: `/volume1/photo/Photo_Organizer.log` and `/volume1/photo/System.log`
- Alternative: Configured destination directory

### Viewing Logs

#### Via File Station or SSH
```bash
# View recent file operations
tail -n 50 /volume1/photo/Photo_Organizer.log

# View system events
tail -n 50 /volume1/photo/System.log

# View all logs
cat /volume1/photo/Photo_Organizer.log
```

#### Via DSM Log Center
System-level events logged via `logger` and `synologset1` are accessible through:
- **DSM Control Panel** → **Log Center** → **System Logs**
- Filter by tag: `PhotoOrganizer`

### Log Statistics

The application tracks and logs statistics including:
- Total bytes moved (files organized)
- Total bytes deleted (duplicates removed)
- Statistics are logged when:
  - Service stops
  - Service is idle for extended periods
  - Manual statistics reset occurs

### Log Format Details

#### File Operation Log Format
Each entry in `Photo_Organizer.log` contains (in order):
- **Time**: Timestamp in `YYYY-MM-DD HH:MM:SS` format
- **IP address**: Local IP address of the NAS
- **User**: System user running the service
- **File name**: Base filename
- **File size**: Human-readable file size (e.g., "2.45 MB")
- **Event**: Type of operation (File moved, Duplicate Deleted, etc.)
- **Additional Info**: Contextual information about the operation (e.g., "Renamed to", "Different content - Older file", etc.)
- **File/Folder**: Full system path to the file (destination path if file was moved)

#### System Log Format
Each entry in `System.log` contains:
- **Level**: Log level (Info, Warning, Error)
- **Log**: Always "System"
- **Time**: Timestamp in `YYYY/MM/DD HH:MM:SS` format
- **User**: System user
- **Event**: Description of the system event

### Troubleshooting with Logs

Logs are essential for troubleshooting issues:
1. Check `System.log` for dependency errors or service start/stop issues
2. Review `Photo_Organizer.log` for file processing errors
3. Look for "Error" entries to identify specific problems
4. Verify file paths and permissions from logged file operations

For detailed debugging instructions, see the [DEBUGGING.md](source/PhotoOrganizer/DEBUGGING.md) file in the project repository.

## Synology Integration

The Photo Organizer is specifically designed to integrate seamlessly with Synology DiskStation Manager (DSM), providing native NAS functionality.

### Synology Detection

The application automatically detects if it's running on a Synology NAS by checking:
- Presence of `/etc/synoinfo.conf`
- DSM version file at `/etc.defaults/VERSION`
- Standard Synology volume path `/volume1`

### Photo Indexer Integration

The application automatically updates Synology's built-in photo indexer (`synoindex`) after file operations:

#### Indexer Update Process

1. **File Deletion**: Removes deleted files from the index
   - Command: `synoindex -D <file_path>`
   - Ensures deleted duplicates don't appear in Photo Station
   - Keeps index synchronized with actual file system

2. **File Movement**: Updates index when files are moved
   - Removes old path: `synoindex -D <old_path>`
   - Adds new path: `synoindex -A <new_path>`
   - Keeps Photo Station synchronized with file organization
   - Ensures photos appear in correct location in Photo Station

3. **Error Handling**: Silently handles cases where `synoindex` is unavailable
   - No errors thrown if indexer command fails
   - Service continues operating normally
   - Timeout protection (5 seconds) prevents hanging
   - Graceful degradation on non-Synology systems

### Path Configuration

The application uses volume-based paths for consistency:
- Default paths: `/volume1/photo/` (configurable during installation)
- Logs show volume-based paths for clarity and consistency
- Compatible with Synology's file system structure
- Paths are configurable via the installation wizard and stored in `config.ini`

### Synology-Specific Features

- **Package Installation**: Designed as a Synology `.spk` package
  - Installs through Package Center
  - Follows Synology package structure and conventions
  - Includes proper service management scripts

- **Service Management**: Integrates with DSM's package service system
  - Can be started/stopped via Package Center
  - Respects Synology's service lifecycle
  - Proper signal handling for graceful shutdown

- **Log Integration**: Logs appear in DSM Log Center
  - Uses Synology's logging infrastructure
  - Accessible through DSM web interface
  - Filterable by tag and priority

- **User Permissions**: Respects Synology user and permission system
  - Runs with appropriate package user permissions
  - Respects folder access controls
  - Integrates with DSM security model

- **Volume Support**: Works with multiple Synology volumes
  - Supports `/volume1`, `/volume2`, etc.
  - Handles volume-specific paths correctly
  - Adapts to different storage configurations

### Configuration on Synology

Configuration files are stored in Synology package directories:
- Primary: `/var/packages/PhotoOrganizer/config.ini`
- Alternative: `/var/packages/PhotoOrganizer/var/config.ini`
- Fallback: `/volume1/@appstore/PhotoOrganizer/var/config.ini`

The application automatically searches these locations in order and uses the first available configuration file.

### Benefits of Synology Integration

- **Seamless Operation**: Works like native Synology applications
  - No special configuration required
  - Follows DSM conventions and standards
  - Integrates with existing workflows

- **Photo Station Compatibility**: Organized photos appear correctly in Photo Station
  - Indexer updates ensure proper recognition
  - Maintains metadata and organization
  - Supports Photo Station's browsing features

- **System Logging**: Integrates with DSM's centralized logging
  - All events visible in Log Center
  - Consistent with other Synology services
  - Easy troubleshooting and monitoring

- **Service Management**: Can be started/stopped via Package Center
  - Standard Synology package interface
  - Status monitoring through Package Center
  - Automatic startup on boot (if configured)

- **Resource Management**: Respects Synology's resource limits and scheduling
  - Works within DSM's resource constraints
  - Compatible with other services
  - Efficient resource utilization

## License

Copyright (c) 2025 MORCE.codes

This package provides automatic photo organization functionality for Synology NAS. The Photo Organizer and Deduplicator application is provided as-is for organizing photos based on EXIF metadata.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/52454D434F/DSM-Projects/issues)

---

**Note**: This package is designed specifically for Synology DiskStation Manager (DSM) and requires a Synology NAS running DSM 7.0 or later.
