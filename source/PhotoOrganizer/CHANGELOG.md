# Changelog

All notable changes to the Photo Organizer and Deduplicator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1-00018] - 2025-01-XX

### Added
- **CreateDate EXIF Tag Support**
  - Added support for extracting CreateDate tag from EXIF metadata
  - CreateDate is checked in priority order after DateTimeOriginal and DateTimeDigitized
  - Supports both top-level and nested ExifIFD CreateDate tags
  - Some cameras and software use CreateDate as an alternative date tag

- **Enhanced Log Entries with Destination Format**
  - All log entries now include destination file format information
  - "Duplicate Deleted" entries show destination format: `yyyy/mm_MMM/yyyymmdd_hhmmss.ext`
  - "File moved" entries show destination path format
  - "Moved to Duplicates" entries show where duplicate was found
  - Improves traceability and debugging of file operations

### Changed
- **Date Extraction Priority Order (CRITICAL FIX)**
  - **Fixed incorrect priority order** - now correctly prioritizes nested ExifIFD tags over top-level tags
  - New priority order (highest to lowest):
    1. Nested ExifIFD DateTimeOriginal (tag 0x9003) - **HIGHEST PRIORITY**
    2. Nested ExifIFD DateTimeDigitized (tag 0x9004)
    3. Nested ExifIFD CreateDate
    4. Top-level DateTimeOriginal
    5. Top-level DateTimeDigitized
    6. Top-level CreateDate
    7. Top-level DateTime (tag 0x0132) - **LOWEST PRIORITY**
  - Previously, the script incorrectly checked top-level DateTime (file modification date) before nested DateTimeOriginal (actual photo capture date)
  - This fix ensures the actual photo capture date is used instead of file modification date
  - **Impact**: Photos will now be organized by their actual capture date, not when they were last modified

### Fixed
- **Date Extraction Logic**
  - Fixed bug where top-level DateTime (file modification date) was checked before nested DateTimeOriginal (photo capture date)
  - Now correctly extracts the actual photo capture date from nested EXIF data
  - Tag 306 (0x0132) is correctly identified as "DateTime" (file modification), not "DateTimeOriginal"
  - Nested ExifIFD DateTimeOriginal (tag 0x9003) is now properly prioritized

- **Log Entry Consistency**
  - Fixed all log entries to properly include destination format information
  - Fixed typo: "Different content then file" → "Different content than file"
  - All `dest_format` variables are now properly defined before use in log messages

### Technical Details
- Date extraction now follows EXIF standard priority: nested ExifIFD tags contain the most accurate capture metadata
- Most modern cameras store DateTimeOriginal in nested ExifIFD structure, not top-level tags
- The fix ensures compatibility with both legacy and modern camera EXIF formats

---

## [1.0.1-00017] - 2025-12-03

### Added
- **Persistent Statistics Tracking System**
  - Implemented JSON-based statistics file (`Photo_Organizer_Statistics.json`) to track file operations
  - Statistics persist across application restarts
  - Tracks the following metrics:
    - Total number of files moved to destination
    - Total bytes moved to destination
    - Total number of files moved to duplicates folder
    - Total bytes moved to duplicates folder
    - Total number of files deleted (duplicates)
    - Total bytes deleted (duplicates)
  - Statistics are automatically loaded on startup
  - Statistics are saved periodically (every 10 operations or 30 seconds timeout, whichever comes first)
  - File locking support for thread-safe statistics updates on Unix/Linux systems

- **Statistics Adjustment Logic**
  - When files are moved from destination folder to duplicates folder, statistics are automatically adjusted:
    - Subtracts from destination statistics
    - Adds to duplicates statistics
  - Ensures accurate tracking when files are reorganized

### Changed
- **Log File Naming**
  - `Photo_Organizer.log` → `Photo_Organizer_Activities.log` (file operation activities)
  - `System.log` → `Photo_Organizer_Application.log` (system/application events)
  - `statistics.json` → `Photo_Organizer_Statistics.json` (statistics tracking)

- **Statistics Save Timing**
  - Statistics now save after every 10 operations OR after 30 seconds timeout (whichever comes first)
  - Improves data persistence and reduces risk of data loss on unexpected shutdowns

- **Application Log Cleanup**
  - Removed detailed statistics breakdown from `Photo_Organizer_Application.log`
  - Statistics are still saved to `Photo_Organizer_Statistics.json` but no longer clutter the application log
  - Application log now focuses on system events and service status

### Fixed
- Statistics now accurately reflect files moved between folders
- When files move from destination to duplicates, destination statistics are properly decremented
- **Mutagen dependency detection**: Fixed false warning about mutagen not being installed
  - Updated dependency check to import mutagen directly instead of relying on module-level flag
  - Properly detects mutagen when installed in virtual environment
- **Video metadata extraction**: Fixed MOV file metadata extraction
  - Removed dependency on non-existent `mutagen.quicktime` module (not available in mutagen 1.47.0+)
  - MOV files now use MP4 module since they share the same container format
  - Video metadata extraction works correctly for both MP4 and MOV files

### Technical Details
- Statistics are stored in JSON format for human readability and easy backup
- Statistics file location: `{DEST_DIR}/Photo_Organizer_Statistics.json`
- Statistics are saved with file locking on Unix/Linux systems for thread safety
- Backward compatible with existing `bytes_moved` and `bytes_deleted` legacy variables

---

## Previous Versions

For changes in previous versions, please refer to the git history or project documentation.

