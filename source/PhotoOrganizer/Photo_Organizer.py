import os
import shutil
import time
import hashlib
import socket
import getpass
import sys
import subprocess
import signal
import atexit
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# File locking support (Unix/Linux only)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Optional dependency: mutagen for video metadata extraction
try:
    import mutagen
    from mutagen.mp4 import MP4
    # Note: QuickTime module doesn't exist in mutagen 1.47.0+
    # MOV files are handled by MP4 module since they share the same container format
    MUTAGEN_AVAILABLE = True
except ImportError:
    mutagen = None
    MP4 = None
    MUTAGEN_AVAILABLE = False

def get_package_version():
    """Get package version from VERSION file."""
    try:
        # Try to find VERSION file relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(script_dir, 'VERSION')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    # Fallback version
    return "1.0.1-00001"

PACKAGE_VERSION = get_package_version()

def is_synology_nas():
    """Check if the script is running on a Synology NAS."""
    # Check for Synology-specific paths
    if os.path.exists('/etc/synoinfo.conf'):
        return True
    # Check for DSM version file
    if os.path.exists('/etc.defaults/VERSION'):
        try:
            with open('/etc.defaults/VERSION', 'r') as f:
                content = f.read()
                if 'productversion' in content.lower() or 'dsm' in content.lower():
                    return True
        except Exception:
            pass
    # Check for /volume1 which is standard on Synology
    if os.path.exists('/volume1'):
        return True
    return False

import configparser

# Source and destination directories
# Use Synology path if running on NAS, otherwise use Windows path.
# Defaults can be overridden by a runtime config file written by postinst.
if is_synology_nas():
    DEFAULT_SOURCE_DIR = "/volume1/photo/Photo Organizer"
    DEFAULT_DEST_DIR = "/volume1/photo/"
else:
    DEFAULT_SOURCE_DIR = r"Photos\Photo Organizer"
    DEFAULT_DEST_DIR = r"Photos"

# todo: should come from the install wizard
SOURCE_DIR = DEFAULT_SOURCE_DIR
DEST_DIR = DEFAULT_DEST_DIR
DELETE_DUPLICATES = True

def load_runtime_config():
    """Load runtime configuration (paths, duplicate policy) if available."""
    global SOURCE_DIR, DEST_DIR, DELETE_DUPLICATES

    config_paths = []
    if is_synology_nas():
        # Primary location: /var/packages/PhotoOrganizer (PACKAGE_VAR_DIR in postinst)
        config_paths = [
            "/var/packages/PhotoOrganizer/config.ini",
            "/var/packages/PhotoOrganizer/var/config.ini",
            "/volume1/@appstore/PhotoOrganizer/var/config.ini",
        ]
    else:
        # For local testing on Windows/Linux, allow a config.ini next to the script
        config_paths = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")]

    parser = configparser.ConfigParser()

    for path in config_paths:
        if not os.path.exists(path):
            continue
        try:
            parser.read(path, encoding="utf-8")

            if parser.has_section("paths"):
                source_dir = parser.get("paths", "source_dir", fallback=SOURCE_DIR)
                dest_root = parser.get("paths", "destination_root", fallback=DEST_DIR)

                if source_dir:
                    SOURCE_DIR = source_dir
                if dest_root:
                    DEST_DIR = dest_root

            if parser.has_section("duplicates"):
                delete_str = parser.get("duplicates", "delete", fallback="true").strip().lower()
                DELETE_DUPLICATES = delete_str in ("1", "true", "yes", "y")

            break  # Successfully loaded a config, no need to try other paths
        except Exception as e:
            print(f"Warning: Error reading config file {path}: {e}")
    
    # Initialize statistics file path and load statistics after DEST_DIR is set
    initialize_statistics_file()
    load_statistics()

# Ensure DEST_DIR exists
if not os.path.exists(DEST_DIR):
    try:
        os.makedirs(DEST_DIR, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create destination directory {DEST_DIR}: {e}")

def initialize_statistics_file():
    """Initialize the statistics file path after DEST_DIR is set."""
    global STATS_FILE
    STATS_FILE = os.path.join(DEST_DIR, "Photo_Organizer_Statistics.json")
    STATS_FILE = os.path.abspath(STATS_FILE)

def load_statistics():
    """Load statistics from JSON file."""
    global stats
    if STATS_FILE is None:
        initialize_statistics_file()
    
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                # Use file locking on Unix/Linux if available
                if HAS_FCNTL:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    except (IOError, OSError):
                        pass  # Locking failed, continue without lock
                
                loaded_stats = json.load(f)
                
                if HAS_FCNTL:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except (IOError, OSError):
                        pass
                
                # Merge with defaults (in case new fields were added)
                for key in stats:
                    if key in loaded_stats:
                        if key == "last_updated":
                            stats[key] = loaded_stats[key]
                        else:
                            # Ensure numeric values
                            try:
                                stats[key] = int(loaded_stats[key])
                            except (ValueError, TypeError):
                                stats[key] = 0
        except Exception as e:
            log_system_event("Warning", f"Error loading statistics: {e}")

def save_statistics(force=False):
    """Save statistics to JSON file with file locking.
    
    Args:
        force: If True, save immediately regardless of counter
    """
    global stats, _stats_save_counter
    if STATS_FILE is None:
        initialize_statistics_file()
    
    stats["last_updated"] = datetime.now().isoformat()
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        
        # Write with file locking
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            if HAS_FCNTL:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                except (IOError, OSError):
                    pass  # Locking failed, continue without lock
            
            json.dump(stats, f, indent=2)
            
            if HAS_FCNTL:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass
        
        # Reset counter if forced save
        if force:
            _stats_save_counter = 0
    except Exception as e:
        log_system_event("Error", f"Error saving statistics: {e}")

def save_statistics_if_needed(force=False):
    """Save statistics periodically (every 10 operations or 30 seconds timeout) or when forced."""
    global _stats_save_counter, _stats_last_save_time
    
    _stats_save_counter += 1
    current_time = time.time()
    
    # Initialize last save time if not set
    if _stats_last_save_time is None:
        _stats_last_save_time = current_time
    
    # Save every 10 operations, after 30 seconds timeout, or when forced
    time_since_last_save = current_time - _stats_last_save_time
    if force or _stats_save_counter >= 10 or time_since_last_save >= 30:
        save_statistics()
        _stats_save_counter = 0
        _stats_last_save_time = current_time

# Log file path - stored in DEST_DIR
LOG_FILE = os.path.join(DEST_DIR, "Photo_Organizer_Activities.log")
LOG_FILE = os.path.abspath(LOG_FILE)
LOG_FILE_INITIALIZED = False

# System log file path - stored in DEST_DIR
SYSTEM_LOG_FILE = os.path.join(DEST_DIR, "Photo_Organizer_Application.log")
SYSTEM_LOG_FILE = os.path.abspath(SYSTEM_LOG_FILE)
SYSTEM_LOG_INITIALIZED = False

# Statistics file path - stored in DEST_DIR (will be set after config loads)
STATS_FILE = None

# Statistics tracking - detailed counters
stats = {
    "files_moved_to_destination": 0,
    "bytes_moved_to_destination": 0,
    "files_moved_to_duplicates": 0,
    "bytes_moved_to_duplicates": 0,
    "files_deleted": 0,
    "bytes_deleted": 0,
    "last_updated": None
}

# Counter for batch saving (save every 10 operations)
_stats_save_counter = 0
_stats_last_save_time = None

# Legacy variables for backward compatibility with existing log_statistics function
bytes_moved = 0
bytes_deleted = 0
last_file_detected_time = None
last_statistics_log_time = None
statistics_reset_time = None
statistics_already_logged = False  # Flag to prevent duplicate logging on exit

def test_dependencies():
    """Test if all required dependencies are installed."""
    print("=" * 60)
    print("Checking dependencies...")
    print("=" * 60)
    
    log_system_event("Info", "Dependency check started")
    
    missing_deps = []
    warnings = []
    installed_deps = []
    
    # Test Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 7:
        version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        print(f"✓ Python {version_str} (required: 3.7+)")
        installed_deps.append(f"Python {version_str}")
    else:
        print(f"✗ Python {python_version.major}.{python_version.minor} (requires 3.7+)")
        missing_deps.append("Python 3.7+")
        log_system_event("Error", f"Dependency check failed: Python {python_version.major}.{python_version.minor} (requires 3.7+)")
    
    # Test built-in modules
    builtin_modules = ['os', 'shutil', 'time', 'hashlib', 'socket', 'getpass', 'datetime']
    for module in builtin_modules:
        try:
            __import__(module)
            print(f"✓ {module} (built-in)")
        except ImportError:
            print(f"✗ {module} (built-in, should always be available)")
            missing_deps.append(module)
            log_system_event("Error", f"Dependency check failed: {module} module not available")
    
    # Test Pillow
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        version = Image.__version__
        print(f"✓ Pillow (version: {version})")
        installed_deps.append(f"Pillow {version}")
    except ImportError:
        print("✗ Pillow is NOT installed")
        print("  Install with: pip install Pillow")
        missing_deps.append("Pillow")
        log_system_event("Error", "Dependency check failed: Pillow is not installed")
    
    # Test watchdog
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        print("✓ watchdog")
        installed_deps.append("watchdog")
    except ImportError:
        print("✗ watchdog is NOT installed")
        print("  Install with: pip install watchdog")
        missing_deps.append("watchdog")
        log_system_event("Error", "Dependency check failed: watchdog is not installed")
    
    # Test imagehash (optional)
    try:
        import imagehash
        print("✓ imagehash (optional)")
        installed_deps.append("imagehash")
    except ImportError:
        print("⚠ imagehash is NOT installed (optional)")
        print("  Install with: pip install imagehash")
        warnings.append("imagehash (optional)")
        log_system_event("Warning", "Dependency check: imagehash (optional) is not installed")
    
    # Test mutagen (optional, for video file metadata)
    # Try importing mutagen directly to check if it's available
    try:
        import mutagen
        from mutagen.mp4 import MP4
        # Note: QuickTime module doesn't exist in mutagen 1.47.0+, MOV files use MP4
        print("✓ mutagen (optional, for video metadata)")
        installed_deps.append("mutagen")
    except ImportError:
        print("⚠ mutagen is NOT installed (optional, for video metadata)")
        print("  Install with: pip install mutagen")
        print("  Or install all dependencies: pip install -r requirements.txt")
        print("  Note: Video files will use file creation/modification date if mutagen is not installed")
        warnings.append("mutagen (optional)")
        log_system_event("Warning", "Dependency check: mutagen (optional) is not installed - video files will use file date")
    
    print("=" * 60)
    
    if missing_deps:
        print("✗ Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print()
        print("Install missing packages with:")
        print("  pip install -r requirements.txt")
        print("  Or individually: pip install Pillow watchdog imagehash mutagen")
        print()
        log_system_event("Error", f"Dependency check completed: Missing required dependencies - {', '.join(missing_deps)}")
        return False
    else:
        if warnings:
            print("✓ All required dependencies are installed")
            print(f"⚠ Optional: {', '.join(warnings)}")
            log_system_event("Info", f"Dependency check completed: All required dependencies installed. Optional: {', '.join(warnings)}")
        else:
            print("✓ All dependencies are installed")
            log_system_event("Info", f"Dependency check completed: All dependencies installed - {', '.join(installed_deps)}")
        print()
        return True

# Cache IP address to avoid repeated socket connections
_cached_ip = None

def get_local_ip():
    """Get local IP address (cached)."""
    global _cached_ip
    if _cached_ip is not None:
        return _cached_ip
    
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            _cached_ip = s.getsockname()[0]
            return _cached_ip
    except Exception:
        _cached_ip = "127.0.0.1"
        return _cached_ip

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def initialize_log_file():
    """Initialize the log file with header if it doesn't exist."""
    global LOG_FILE_INITIALIZED
    if not LOG_FILE_INITIALIZED and not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("# Time, IP address, User, File name, File size, Event, Additional Info, File/Folder\n")
            LOG_FILE_INITIALIZED = True
        except Exception as e:
            print(f"Error initializing log file: {e}")

def initialize_system_log():
    """Initialize the system log file with header if it doesn't exist."""
    global SYSTEM_LOG_INITIALIZED
    if not SYSTEM_LOG_INITIALIZED and not os.path.exists(SYSTEM_LOG_FILE):
        try:
            with open(SYSTEM_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("# Level, Log, Time, User, Event\n")
            SYSTEM_LOG_INITIALIZED = True
        except Exception as e:
            print(f"Error initializing system log file: {e}")

def format_bytes(bytes_value):
    """Format bytes into human-readable format (KB, MB, GB, etc.) with up to 2 decimal places."""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    # Format with up to 2 decimal places
    if unit_index == 0:  # Bytes - no decimals
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"

def log_statistics(reason="service stopped", force=False):
    """Log statistics to system log when script stops or idle.
    
    Args:
        reason: Reason for logging statistics (e.g., "service stopped", "idle timeout")
        force: If True, log even if already logged (for idle timeout resets)
    """
    global bytes_moved, bytes_deleted, last_statistics_log_time, statistics_already_logged
    
    # Prevent duplicate logging on exit (unless forced, e.g., for idle timeout)
    if not force and statistics_already_logged and reason == "service stopped":
        return
    
    # Save statistics before logging (force save)
    save_statistics(force=True)
    
    # Statistics are saved to Photo_Organizer_Statistics.json
    # No longer logging detailed statistics to application log
    
    last_statistics_log_time = time.time()
    
    # Mark as logged if this is an exit-related log
    if reason == "service stopped":
        statistics_already_logged = True

def log_system_event(level, event_message):
    """Log system events (start, stop, dependencies check, etc.).
    
    Args:
        level: Log level (Info, Warning, Error)
        event_message: Description of the event
    """
    global SYSTEM_LOG_INITIALIZED
    
    # Initialize system log if needed
    initialize_system_log()
    
    # Get current time in format: 2025/11/22 01:30:54
    current_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    
    # Get user
    try:
        user = getpass.getuser()
    except Exception:
        user = os.getenv('USER', os.getenv('USERNAME', 'system'))
    
    # Write to system log file
    try:
        with open(SYSTEM_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{level}, System, {current_time}, {user}, {event_message}\n")
    except Exception as e:
        print(f"Error writing to system log file: {e}")

def log_file_event(event_type, file_path, dest_path=None, file_size=None, additional_info=""):
    """Log file event to Photo_Organizer_Activities.log.
    
    Columns: Time, IP address, User, File name, File size, Event, Additional Info, File/Folder
    Saves to log file and prints to console.
    """
    global LOG_FILE_INITIALIZED
    
    # Initialize log file if needed
    initialize_log_file()
    
    # Get current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get user
    try:
        user = getpass.getuser()
    except Exception:
        user = os.getenv('USER', os.getenv('USERNAME', 'system'))
    
    # Get IP address
    ip_address = get_local_ip()
    
    # Get file size if not provided
    if file_size is None:
        try:
            file_size = os.path.getsize(file_path)
        except Exception:
            file_size = 0
    
    # Format file size
    size_str = format_file_size(file_size)
    
    # Get file name
    file_name = os.path.basename(file_path)
    
    # Determine file/folder path (destination if provided, otherwise source)
    file_folder = dest_path if dest_path else file_path
    
    # Write to log file
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            log_line = f"{current_time}, {ip_address}, {user}, {file_name}, {size_str}, {event_type}"
            if additional_info:
                log_line += f", {additional_info}"
            log_line += f", {file_folder}\n"
            f.write(log_line)
    except Exception as e:
        print(f"Error writing to log file: {e}")
    
    # Also print to console (tab-separated for easy reading)
    log_entry = f"{current_time}\t{ip_address}\t{user}\t{file_name}\t{size_str}\t{event_type}"
    if additional_info:
        log_entry += f"\t{additional_info}"
    log_entry += f"\t{file_folder}"
    print(log_entry)

# Ensure destination directory exists
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def update_synology_indexer(old_path=None, new_path=None):
    """Update Synology DSM photo indexer after file operations.
    
    Args:
        old_path: Path to remove from index (if file was moved/deleted)
        new_path: Path to add to index (if file was moved/created)
    """
    if not is_synology_nas():
        return
    
    try:
        # Remove old path from index if provided
        if old_path and os.path.exists('/usr/syno/bin/synoindex'):
            try:
                subprocess.run(['/usr/syno/bin/synoindex', '-D', old_path], 
                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except Exception:
                pass  # Silently fail if synoindex is not available or times out
        
        # Add new path to index if provided
        if new_path and os.path.exists(new_path) and os.path.exists('/usr/syno/bin/synoindex'):
            try:
                subprocess.run(['/usr/syno/bin/synoindex', '-A', new_path], 
                             check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except Exception:
                pass  # Silently fail if synoindex is not available or times out
    except Exception:
        pass  # Silently fail if indexer update fails

def is_video_file(file_path):
    """Check if the file is a video file based on extension."""
    video_extensions = {'.mp4', '.m4v', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', 
                       '.wmv', '.flv', '.webm', '.3gp', '.mts', '.m2ts', '.ts'}
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in video_extensions

def is_image_file(file_path):
    """Check if the file is an image file based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
                       '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.orf', 
                       '.sr2', '.arw', '.dng', '.ico', '.svg', '.psd'}
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in image_extensions

def get_video_taken_date(video_path):
    """Get creation date from video file metadata and return as datetime object."""
    try:
        # Try using mutagen for MP4/MOV files
        if MUTAGEN_AVAILABLE:
            file_ext = os.path.splitext(video_path)[1].lower()
            
            if file_ext in {'.mp4', '.m4v'}:
                mp4_file = MP4(video_path)
                # Try to get creation date from MP4 metadata
                if '©day' in mp4_file:
                    date_str = mp4_file['©day'][0]
                    # Format: 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'
                    try:
                        if 'T' in date_str:
                            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
                # Try creation date tag
                if '\xa9day' in mp4_file:
                    date_str = mp4_file['\xa9day'][0]
                    try:
                        if 'T' in date_str:
                            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
            
            elif file_ext == '.mov':
                # MOV files use the same container format as MP4, so use MP4 module
                mov_file = MP4(video_path)
                # Try to get creation date from MOV metadata (same tags as MP4)
                if '©day' in mov_file:
                    date_str = mov_file['©day'][0]
                    try:
                        if 'T' in date_str:
                            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
                # Try creation date tag (alternative)
                if '\xa9day' in mov_file:
                    date_str = mov_file['\xa9day'][0]
                    try:
                        if 'T' in date_str:
                            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
        else:
            # mutagen not available, will fall back to file date
            pass
    except Exception as e:
            # Error reading video metadata, will fall back to file date
            pass
    except Exception as e:
        pass
    return None

def get_exif_taken_date(image_path):
    """Get EXIF date (DateTimeOriginal, CreateDate, DateTimeDigitized, or DateTime) and return as datetime object.
    
    Checks in priority order:
    1. Nested ExifIFD DateTimeOriginal (highest priority)
    2. Nested ExifIFD DateTimeDigitized
    3. Nested ExifIFD CreateDate
    4. Top-level DateTimeOriginal
    5. Top-level DateTimeDigitized
    6. Top-level CreateDate
    7. Top-level DateTime (lowest priority)
    """
    try:
        with Image.open(image_path) as image:
            exif_data = None
            
            # Try getexif() first (newer Pillow versions)
            try:
                exif_data = image.getexif()
            except AttributeError:
                # Fallback to _getexif() for older versions
                try:
                    exif_data = image._getexif()
                except AttributeError:
                    return None
            
            if not exif_data:
                return None
            
            # Try to get date following priority order
            date_time_original = None
            
            # Method 1: Try direct tag access (for getexif())
            if hasattr(exif_data, 'get'):
                # New getexif() returns a dict-like object
                # PRIORITY 1-3: Check nested EXIF data FIRST (ExifIFD - tag 34665 / 0x8769)
                try:
                    # Tag 34665 (0x8769) is ExifIFD - contains nested EXIF tags
                    # DateTimeOriginal is tag 0x9003 (36867) in ExifIFD
                    if hasattr(exif_data, 'get_ifd'):
                        # Use get_ifd() method to access nested IFD (Pillow 8.0+)
                        try:
                            exif_ifd = exif_data.get_ifd(0x8769)  # ExifIFD
                            # PRIORITY 1: DateTimeOriginal is tag 0x9003 (36867) in ExifIFD
                            date_time_original = exif_ifd.get(0x9003)  # DateTimeOriginal
                            # PRIORITY 2: Try DateTimeDigitized (0x9004) as fallback
                            if not date_time_original:
                                date_time_original = exif_ifd.get(0x9004)
                            # PRIORITY 3: Try CreateDate in nested EXIF (some cameras use this)
                            if not date_time_original:
                                # CreateDate might be stored as a custom tag, check by iterating
                                for nested_tag_id in exif_ifd.keys():
                                    nested_tag_name = TAGS.get(nested_tag_id, nested_tag_id)
                                    if nested_tag_name == 'CreateDate' or 'CreateDate' in str(nested_tag_name):
                                        date_time_original = exif_ifd.get(nested_tag_id)
                                        if date_time_original:
                                            break
                        except Exception:
                            pass
                    
                    # Alternative: Try accessing ExifIFD tag directly
                    if not date_time_original:
                        exif_ifd_tag = exif_data.get(34665)  # ExifIFD tag (0x8769)
                        if exif_ifd_tag and hasattr(exif_ifd_tag, 'get'):
                            # PRIORITY 1: DateTimeOriginal
                            date_time_original = exif_ifd_tag.get(0x9003) or exif_ifd_tag.get(36867)
                            # PRIORITY 2: DateTimeDigitized
                            if not date_time_original:
                                date_time_original = exif_ifd_tag.get(0x9004) or exif_ifd_tag.get(36868)
                            # PRIORITY 3: CreateDate
                            if not date_time_original and hasattr(exif_ifd_tag, 'keys'):
                                for nested_tag_id in exif_ifd_tag.keys():
                                    nested_tag_name = TAGS.get(nested_tag_id, nested_tag_id)
                                    if nested_tag_name == 'CreateDate' or 'CreateDate' in str(nested_tag_name):
                                        date_time_original = exif_ifd_tag.get(nested_tag_id)
                                        if date_time_original:
                                            break
                except Exception:
                    pass
                
                # PRIORITY 4-7: If not found in nested, check top-level tags in priority order
                if not date_time_original:
                    # PRIORITY 4: Top-level DateTimeOriginal
                    for tag_id in exif_data.keys():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name == 'DateTimeOriginal':
                            date_time_original = exif_data.get(tag_id)
                            break
                    # PRIORITY 5: Top-level DateTimeDigitized
                    if not date_time_original:
                        for tag_id in exif_data.keys():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == 'DateTimeDigitized':
                                date_time_original = exif_data.get(tag_id)
                                break
                    # PRIORITY 6: Top-level CreateDate
                    if not date_time_original:
                        for tag_id in exif_data.keys():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == 'CreateDate' or 'CreateDate' in str(tag_name):
                                date_time_original = exif_data.get(tag_id)
                                break
                    # PRIORITY 7: Top-level DateTime (lowest priority)
                    if not date_time_original:
                        for tag_id in exif_data.keys():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == 'DateTime':
                                date_time_original = exif_data.get(tag_id)
                                break
            else:
                # Method 2: Old _getexif() returns a dict - iterate through items
                # Note: Old _getexif() doesn't support nested ExifIFD easily, so we check top-level only
                # But we still follow priority order: DateTimeOriginal > DateTimeDigitized > CreateDate > DateTime
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        date_time_original = value
                        break
                # If not found, try DateTimeDigitized
                if not date_time_original:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeDigitized':
                            date_time_original = value
                            break
                # If not found, try CreateDate
                if not date_time_original:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'CreateDate' or 'CreateDate' in str(tag):
                            date_time_original = value
                            break
                # If not found, try DateTime (lowest priority)
                if not date_time_original:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTime':
                            date_time_original = value
                            break
            
            if date_time_original:
                # Format: 'YYYY:MM:DD HH:MM:SS'
                try:
                    return datetime.strptime(date_time_original, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    # Try alternative format without colons in date
                    try:
                        return datetime.strptime(date_time_original.replace(':', '-', 2), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        print(f"Error parsing EXIF date format: {date_time_original}")
                        return None
    except Exception:
        # Not an image file or error reading EXIF
        pass
    return None

def get_file_date(file_path):
    """Get the older of creation or modification date from file metadata and return as datetime object."""
    try:
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)
        # Use the older (earlier) date
        oldest_timestamp = min(creation_time, modification_time)
        return datetime.fromtimestamp(oldest_timestamp)
    except Exception as e:
        print(f"Error reading file date from {file_path}: {e}")
        return None

def get_file_modification_time(file_path):
    """Get the modification time of a file as datetime object."""
    try:
        modification_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(modification_time)
    except Exception as e:
        print(f"Error reading modification time from {file_path}: {e}")
        return None

def format_datetime_for_filename(dt, include_subseconds=False):
    """Format datetime object as yyyymmdd_hhmmss or yyyymmdd_hhmmss.XXXX if microseconds are available.
    
    Args:
        dt: datetime object
        include_subseconds: If True, include subseconds in format (for duplicates folder)
                           If False, return base format without subseconds (for destination folder)
    
    Returns:
        Formatted string: yyyymmdd_hhmmss or yyyymmdd_hhmmss.XXXX
    """
    base_format = dt.strftime('%Y%m%d_%H%M%S')
    # Only include subseconds if requested and available
    if include_subseconds and dt.microsecond > 0:
        # Convert microseconds to a 4-digit value (divide by 100 to get 0-9999 range)
        # This represents the fractional seconds with 4-digit precision
        milliseconds_value = dt.microsecond // 100
        # Format as .XXXX (4 digits with leading zeros)
        return f"{base_format}.{milliseconds_value:04d}"
    return base_format

def calculate_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating MD5 for {file_path}: {e}")
        return None

def check_duplicate_md5_in_folder(file_path, folder_path):
    """Check if a file with the same MD5 hash already exists in the specified folder.
    
    Args:
        file_path: Path to the file to check
        folder_path: Path to the folder to search in
        
    Returns:
        Path to the existing duplicate file if found, None otherwise
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return None
    
    source_hash = calculate_md5(file_path)
    if source_hash is None:
        return None
    
    # Check all files in the folder
    try:
        for filename in os.listdir(folder_path):
            existing_file_path = os.path.join(folder_path, filename)
            if os.path.isfile(existing_file_path):
                existing_hash = calculate_md5(existing_file_path)
                if existing_hash == source_hash:
                    return existing_file_path
    except Exception as e:
        print(f"Error checking for duplicate MD5 in {folder_path}: {e}")
    
    return None

def get_unique_duplicate_filename(duplicates_folder, base_filename, media_datetime=None):
    """Get a unique filename in the Duplicates folder with subseconds format.
    
    Format: yyyymmdd_hhmmss.ssss.ext
    If subseconds are not available, use sequential numbers: yyyymmdd_hhmmss.0001.ext, etc.
    
    Args:
        duplicates_folder: Path to duplicates folder
        base_filename: Base filename (without path)
        media_datetime: datetime object if available, None otherwise
    
    Returns:
        Unique filename with subseconds or sequential number
    """
    # Extract base name and extension
    name, ext = os.path.splitext(base_filename)
    
    # If we have datetime, try to use subseconds format
    if media_datetime:
        base_format = format_datetime_for_filename(media_datetime, include_subseconds=False)
        # If subseconds were available, try using them first
        if media_datetime.microsecond > 0:
            subseconds_format = format_datetime_for_filename(media_datetime, include_subseconds=True)
            test_filename = f"{subseconds_format}{ext}"
            test_path = os.path.join(duplicates_folder, test_filename)
            if not os.path.exists(test_path):
                return test_filename
        
        # If no subseconds or file exists, use base format with sequential numbers
        counter = 1
        while True:
            test_filename = f"{base_format}.{counter:04d}{ext}"
            test_path = os.path.join(duplicates_folder, test_filename)
            if not os.path.exists(test_path):
                return test_filename
            counter += 1
    else:
        # No datetime available, try to extract date from filename if it matches pattern
        # Pattern: yyyymmdd_hhmmss.ext or yyyymmdd_hhmmss.XXXX.ext
        import re
        # Try to match yyyymmdd_hhmmss pattern (with or without subseconds)
        match = re.match(r'(\d{8}_\d{6})(?:\.\d{4})?(.*)', name)
        if match:
            base_date = match.group(1)
            counter = 1
            while True:
                test_filename = f"{base_date}.{counter:04d}{ext}"
                test_path = os.path.join(duplicates_folder, test_filename)
                if not os.path.exists(test_path):
                    return test_filename
                counter += 1
        else:
            # Fallback: use original name with sequential numbers
            counter = 1
            while True:
                test_filename = f"{name}.{counter:04d}{ext}"
                test_path = os.path.join(duplicates_folder, test_filename)
                if not os.path.exists(test_path):
                    return test_filename
                counter += 1

def process_photo(file_path):
    """Process a single photo or video file and move it to the appropriate date folder."""
    global bytes_moved, bytes_deleted, last_file_detected_time, statistics_reset_time
    
    # Skip Windows Zone.Identifier files
    if file_path.endswith('.Zone.Identifier'):
        return
    
    # Verify file exists before processing
    if not os.path.isfile(file_path):
        return
    
    # Verify file is still in the source directory (hasn't been moved already)
    # This prevents processing files that have already been moved by a previous process_photo() call
    try:
        # Get absolute paths for comparison
        abs_file_path = os.path.abspath(file_path)
        abs_source_dir = os.path.abspath(SOURCE_DIR)
        
        # Check if file is within the source directory
        if not abs_file_path.startswith(abs_source_dir + os.sep) and abs_file_path != abs_source_dir:
            # File is not in source directory, skip processing
            return
    except Exception:
        # If path comparison fails, continue (better to try than skip)
        pass
    
    # Double-check file still exists (race condition protection)
    if not os.path.isfile(file_path):
        return
    
    # Update last file detected time
    last_file_detected_time = time.time()
    
    # Clear the reset flag when new activity is detected (statistics were already logged on reset)
    if statistics_reset_time is not None:
        statistics_reset_time = None
    
    # Wait a moment to ensure file is fully written (useful for large files being copied)
    time.sleep(0.5)
    
    # Final check after sleep - file might have been moved during sleep
    if not os.path.isfile(file_path):
        return
    
    original_filename = os.path.basename(file_path)
    file_ext = os.path.splitext(original_filename)[1]  # Get extension including dot
    
    # Determine if this is a video or image file
    is_video = is_video_file(file_path)
    is_image = is_image_file(file_path)
    
    # If file is neither image nor video, move to Unknown File Types folder
    if not is_video and not is_image:
        unknown_folder = os.path.join(DEST_DIR, 'Unknown File Types')
        ensure_dir(unknown_folder)
        dest_path = os.path.join(unknown_folder, original_filename)
        
        # Check if file already exists in Unknown File Types folder
        if os.path.exists(dest_path):
            # Compare MD5 hashes to determine if it's a duplicate
            try:
                source_size = os.path.getsize(file_path)
                dest_size = os.path.getsize(dest_path)
                if source_size == dest_size:
                    source_hash = calculate_md5(file_path)
                    if source_hash is not None:
                        dest_hash = calculate_md5(dest_path)
                        if source_hash == dest_hash:
                            # Files are identical (duplicate)
                            file_size = source_size
                            if DELETE_DUPLICATES:
                                os.remove(file_path)
                                # Format destination path for log
                                dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                                log_file_event("Duplicate Deleted", file_path, None, file_size, f"Exact duplicate to {dest_format} detected and deleted")
                                stats["files_deleted"] += 1
                                stats["bytes_deleted"] += file_size
                                bytes_deleted += file_size  # Legacy compatibility
                                save_statistics_if_needed()
                                update_synology_indexer(old_path=file_path, new_path=None)
                            else:
                                # Keep duplicate with unique name
                                duplicates_folder = os.path.join(unknown_folder, 'Duplicates')
                                ensure_dir(duplicates_folder)
                                unique_name = get_unique_duplicate_filename(duplicates_folder, original_filename)
                                duplicates_path = os.path.join(duplicates_folder, unique_name)
                                shutil.move(file_path, duplicates_path)
                                # Format destination path for log
                                dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                                log_file_event("Moved to Duplicates", file_path, duplicates_path, file_size, f"Unknown file type - exact duplicate to {dest_format} detected (kept, not deleted)")
                                stats["files_moved_to_duplicates"] += 1
                                stats["bytes_moved_to_duplicates"] += file_size
                                bytes_moved += file_size  # Legacy compatibility
                                save_statistics_if_needed()
                                update_synology_indexer(old_path=file_path, new_path=duplicates_path)
                            return
            except Exception:
                pass
        
        # Move file to Unknown File Types folder
        try:
            file_size = os.path.getsize(file_path)
            shutil.move(file_path, dest_path)
            # Format destination path for log
            dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
            log_file_event("File moved", file_path, dest_path, file_size, f"Unknown file type moved to {dest_format}")
            stats["files_moved_to_destination"] += 1
            stats["bytes_moved_to_destination"] += file_size
            bytes_moved += file_size  # Legacy compatibility
            save_statistics_if_needed()
            update_synology_indexer(old_path=file_path, new_path=dest_path)
        except Exception as e:
            log_file_event("Error", file_path, dest_path, None, f"Error moving unknown file type: {e}")
        return
    
    # Try to get date from metadata
    media_datetime = None
    if is_video:
        # For video files, try to get date from video metadata
        media_datetime = get_video_taken_date(file_path)
    else:
        # For image files, try to get date from EXIF
        media_datetime = get_exif_taken_date(file_path)
    
    # If no metadata date found, try file metadata (works for both images and videos)
    if not media_datetime:
        media_datetime = get_file_date(file_path)
    
    if media_datetime:
        # We have a date, rename file to yyyymmdd_hhmmss.* (without subseconds for destination folder)
        new_filename = format_datetime_for_filename(media_datetime, include_subseconds=False) + file_ext
        year = media_datetime.strftime('%Y')
        # Format month as mm_MMM (e.g., 08_Aug)
        month_num = media_datetime.strftime('%m')
        month_abbr = media_datetime.strftime('%b')
        month_folder = f"{month_num}_{month_abbr}"
        dest_folder = os.path.join(DEST_DIR, year, month_folder)
        dest_filename = new_filename
    else:
        # No date found, keep original filename and move to NoDateFound
        dest_folder = os.path.join(DEST_DIR, 'NoDateFound')
        dest_filename = original_filename
    
    ensure_dir(dest_folder)
    dest_path = os.path.join(dest_folder, dest_filename)
    
    # Check if destination file already exists
    if os.path.exists(dest_path):
        # Compare MD5 hashes to determine if it's a duplicate
        print(f"File {dest_filename} already exists at {dest_path}, comparing MD5 hashes...")
        # Get file sizes first - if different, they're not duplicates (optimization)
        try:
            source_size = os.path.getsize(file_path)
            dest_size = os.path.getsize(dest_path)
        except Exception:
            source_size = dest_size = 0
        
        # Only check MD5 if sizes match (optimization)
        source_hash = None
        dest_hash = None
        if source_size == dest_size:
            source_hash = calculate_md5(file_path)
            if source_hash is not None:
                dest_hash = calculate_md5(dest_path)
        
        if source_hash == dest_hash and source_hash is not None:
            # Files are identical (duplicate)
            file_size = source_size
            try:
                if DELETE_DUPLICATES:
                    # Delete the duplicate file
                    os.remove(file_path)
                    # Format destination path for log (yyyy/mm_MMM/yyyymmdd_hhmmss.ext)
                    dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                    log_file_event("Duplicate Deleted", file_path, None, file_size, f"Exact duplicate to {dest_format} detected and deleted")
                    # Update statistics
                    stats["files_deleted"] += 1
                    stats["bytes_deleted"] += file_size
                    bytes_deleted += file_size  # Legacy compatibility
                    save_statistics_if_needed()
                    # Update Synology indexer (remove deleted file from index)
                    update_synology_indexer(old_path=file_path, new_path=None)
                else:
                    # Keep duplicates: move to Duplicates folder instead of deleting
                    duplicates_folder = os.path.join(DEST_DIR, 'Duplicates')
                    ensure_dir(duplicates_folder)
                    # Use the destination filename (without subseconds) as base for duplicates
                    unique_name = get_unique_duplicate_filename(duplicates_folder, dest_filename, media_datetime)
                    duplicates_path = os.path.join(duplicates_folder, unique_name)

                    shutil.move(file_path, duplicates_path)
                    # Format destination path for log
                    dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                    log_file_event("Moved to Duplicates", file_path, duplicates_path, file_size, f"Exact duplicate to {dest_format} detected (kept, not deleted)")
                    # Update statistics
                    stats["files_moved_to_duplicates"] += 1
                    stats["bytes_moved_to_duplicates"] += file_size
                    bytes_moved += file_size  # Legacy compatibility
                    save_statistics_if_needed()
                    # Update Synology indexer to reflect new location
                    update_synology_indexer(old_path=file_path, new_path=duplicates_path)

            except Exception as e:
                log_file_event("Error", file_path, None, None, f"Error handling duplicate: {e}")
            return
        else:
            # Files have different content (MD5 mismatch), check which file was modified
            source_mod_time = get_file_modification_time(file_path)
            dest_mod_time = get_file_modification_time(dest_path)
            
            if source_mod_time and dest_mod_time:
                # Determine which file is newer (modified)
                if source_mod_time > dest_mod_time:
                    # Source file is newer, move it to Duplicates
                    file_to_move = file_path
                    file_name = dest_filename
                    event_info = f"Newer file (modified: {source_mod_time.strftime('%Y-%m-%d %H:%M:%S')})"
                else:
                    # Destination file is newer, move it to Duplicates and keep source
                    file_to_move = dest_path
                    file_name = dest_filename
                    event_info = f"Older file (modified: {dest_mod_time.strftime('%Y-%m-%d %H:%M:%S')})"
            else:
                # Fallback if we can't get modification times
                file_to_move = file_path
                file_name = dest_filename
                event_info = "Unable to get modification times"
            
            # Move the modified file to Duplicates folder
            duplicates_folder = os.path.join(DEST_DIR, 'Duplicates')
            ensure_dir(duplicates_folder)
            
            # Check if a file with the same MD5 hash already exists in Duplicates folder
            existing_duplicate = check_duplicate_md5_in_folder(file_to_move, duplicates_folder)
            if existing_duplicate:
                # A duplicate already exists in Duplicates folder, delete the current file instead
                try:
                    file_size = os.path.getsize(file_to_move)
                    os.remove(file_to_move)
                    # Format destination path for log
                    if file_to_move == dest_path:
                        # File was in destination folder, show destination format
                        dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                    else:
                        # File was in source, show where duplicate exists
                        dest_format = os.path.relpath(existing_duplicate, DEST_DIR).replace(os.sep, '/')
                    log_file_event("Duplicate Deleted", file_to_move, None, file_size, f"Exact duplicate to {dest_format} detected and deleted")
                    # Update statistics
                    # If deleting from destination, subtract from destination stats
                    if file_to_move == dest_path:
                        stats["files_moved_to_destination"] = max(0, stats["files_moved_to_destination"] - 1)
                        stats["bytes_moved_to_destination"] = max(0, stats["bytes_moved_to_destination"] - file_size)
                        bytes_moved = max(0, bytes_moved - file_size)  # Legacy compatibility
                    # Add to deleted stats
                    stats["files_deleted"] += 1
                    stats["bytes_deleted"] += file_size
                    bytes_deleted += file_size  # Legacy compatibility
                    save_statistics_if_needed()
                    # Update Synology indexer (remove deleted file from index)
                    update_synology_indexer(old_path=file_to_move, new_path=None)
                except Exception as e:
                    log_file_event("Error", file_to_move, None, None, f"Error deleting duplicate that exists in Duplicates folder: {e}")
                
                # If we were going to move the destination file, now move the source to its place
                if file_to_move == dest_path:
                    try:
                        file_size = os.path.getsize(file_path)
                        shutil.move(file_path, dest_path)
                        # Format destination path for log
                        dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                        log_file_event("File moved", file_path, dest_path, file_size, f"Replaced existing {dest_format} file with current file (is older)")
                        # Update statistics
                        stats["files_moved_to_destination"] += 1
                        stats["bytes_moved_to_destination"] += file_size
                        bytes_moved += file_size  # Legacy compatibility
                        save_statistics_if_needed()
                        # Update Synology indexer
                        update_synology_indexer(old_path=file_path, new_path=dest_path)
                    except Exception as e:
                        log_file_event("Error", file_path, dest_path, None, f"Error moving source to destination: {e}")
                return
            
            # No duplicate found in Duplicates folder, proceed with moving
            unique_filename = get_unique_duplicate_filename(duplicates_folder, file_name, media_datetime)
            duplicates_path = os.path.join(duplicates_folder, unique_filename)
            
            try:
                file_size = os.path.getsize(file_to_move)
                shutil.move(file_to_move, duplicates_path)
                # Format destination path for log
                dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                log_file_event("Moved to Duplicates", file_to_move, duplicates_path, file_size, f"Different content than file {dest_format} - {event_info}")
                # Update statistics
                # If moving from destination to duplicates, adjust destination stats
                if file_to_move == dest_path:
                    # File was previously in destination, subtract from destination stats
                    stats["files_moved_to_destination"] = max(0, stats["files_moved_to_destination"] - 1)
                    stats["bytes_moved_to_destination"] = max(0, stats["bytes_moved_to_destination"] - file_size)
                    bytes_moved = max(0, bytes_moved - file_size)  # Legacy compatibility
                # Add to duplicates stats
                stats["files_moved_to_duplicates"] += 1
                stats["bytes_moved_to_duplicates"] += file_size
                save_statistics_if_needed()
                # Update Synology indexer
                update_synology_indexer(old_path=file_to_move, new_path=duplicates_path)
                
                # If we moved the destination file, now move the source to its place
                if file_to_move == dest_path:
                    try:
                        file_size = os.path.getsize(file_path)
                        shutil.move(file_path, dest_path)
                        # Format destination path for log
                        dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
                        log_file_event("File moved", file_path, dest_path, file_size, f"Replaced existing {dest_format} file with the oldest file")
                        # Update statistics
                        stats["files_moved_to_destination"] += 1
                        stats["bytes_moved_to_destination"] += file_size
                        bytes_moved += file_size  # Legacy compatibility
                        save_statistics_if_needed()
                        # Update Synology indexer
                        update_synology_indexer(old_path=file_path, new_path=dest_path)
                    except Exception as e:
                        log_file_event("Error", file_path, dest_path, None, f"Error moving source to destination: {e}")
            except Exception as e:
                log_file_event("Error", file_to_move, duplicates_path, None, f"Error moving to Duplicates: {e}")
            return
    
    try:
        # Final check before moving - file might have been moved by another process
        if not os.path.isfile(file_path):
            return
        
        file_size = os.path.getsize(file_path)
        shutil.move(file_path, dest_path)
        # Format destination path for log
        dest_format = os.path.relpath(dest_path, DEST_DIR).replace(os.sep, '/')
        if media_datetime:
            log_file_event("File moved", file_path, dest_path, file_size, f"Renamed to {dest_filename} and moved to {dest_format}")
        else:
            log_file_event("File moved", file_path, dest_path, file_size, f"No date found keeping original name, moved to {dest_format}")
        # Update statistics
        stats["files_moved_to_destination"] += 1
        stats["bytes_moved_to_destination"] += file_size
        bytes_moved += file_size  # Legacy compatibility
        save_statistics_if_needed()
        # Update Synology indexer
        update_synology_indexer(old_path=file_path, new_path=dest_path)
    except FileNotFoundError:
        # File was already moved or deleted, ignore silently
        pass
    except Exception as e:
        # Only log error if file still exists (might be a real error)
        if os.path.exists(file_path):
            log_file_event("Error", file_path, dest_path, None, f"Error moving file: {e}")

def move_photos_by_date():
    """Process all existing photos in the source directory."""
    if not os.path.exists(SOURCE_DIR):
        print(f"Source directory {SOURCE_DIR} does not exist. Creating it...")
        ensure_dir(SOURCE_DIR)
        return
    
    files_found = []
    for filename in os.listdir(SOURCE_DIR):
        # Skip Windows Zone.Identifier files
        if filename.endswith('.Zone.Identifier'):
            continue
        file_path = os.path.join(SOURCE_DIR, filename)
        if os.path.isfile(file_path):
            files_found.append(file_path)
    
    for file_path in files_found:
        try:
            process_photo(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

class PhotoHandler(FileSystemEventHandler):
    """Handler for file system events in the watched directory."""
    
    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory:
            # Skip Windows Zone.Identifier files
            if event.src_path.endswith('.Zone.Identifier'):
                return

            try:
                file_size = os.path.getsize(event.src_path)
                log_file_event("File Detected", event.src_path, None, file_size, "File detected")
            except Exception:
                log_file_event("File Detected", event.src_path, None, None, "New file detected")
            process_photo(event.src_path)
    
    def on_moved(self, event):
        """Called when a file or directory is moved/renamed."""
        if not event.is_directory:
            # Only process moves if the destination is in the source directory
            # This prevents processing files that were moved OUT of the source directory
            try:
                abs_dest_path = os.path.abspath(event.dest_path)
                abs_source_dir = os.path.abspath(SOURCE_DIR)
                
                # Only process if destination is within source directory
                if abs_dest_path.startswith(abs_source_dir + os.sep) or abs_dest_path == abs_source_dir:
                    try:
                        file_size = os.path.getsize(event.dest_path)
                        log_file_event("File Moved/Renamed", event.src_path, event.dest_path, file_size, "External move detected")
                    except Exception:
                        log_file_event("File Moved/Renamed", event.src_path, event.dest_path, None, "External move detected")
                    process_photo(event.dest_path)
            except Exception:
                # If path check fails, skip to avoid errors
                pass

def start_watching():
    """Start watching the source directory for new files."""
    global last_file_detected_time, last_statistics_log_time, statistics_reset_time
    
    if not os.path.exists(SOURCE_DIR):
        print(f"Source directory {SOURCE_DIR} does not exist. Creating it...")
        ensure_dir(SOURCE_DIR)
    
    print(f"Starting folder watcher for: {os.path.abspath(SOURCE_DIR)}")
    print("Press Ctrl+C to stop watching...")
    
    # Initialize last file detected time to now (so we don't log immediately)
    last_file_detected_time = time.time()
    last_statistics_log_time = time.time()
    statistics_reset_time = None
    
    event_handler = PhotoHandler()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=False)
    observer.start()
    
    try:
        check_interval = 0
        while True:
            time.sleep(1)
            check_interval += 1
            
            # Periodically check for unprocessed files (every 10 seconds) - helps with WSL path issues
            if check_interval >= 10:
                check_interval = 0
                try:
                    if os.path.exists(SOURCE_DIR):
                        files = [f for f in os.listdir(SOURCE_DIR) 
                                if os.path.isfile(os.path.join(SOURCE_DIR, f)) 
                                and not f.endswith('.Zone.Identifier')]
                        if files:
                            for filename in files:
                                file_path = os.path.join(SOURCE_DIR, filename)
                                # Verify file still exists and is in source directory before processing
                                if os.path.isfile(file_path):
                                    # Only process if file is older than 2 seconds (fully written)
                                    if time.time() - os.path.getmtime(file_path) > 2:
                                        try:
                                            process_photo(file_path)
                                        except FileNotFoundError:
                                            # File was moved/deleted during processing, ignore
                                            pass
                                        except Exception:
                                            # Other errors, log but don't crash
                                            pass
                except Exception:
                    pass
            
            # Check if 1 minute (60 seconds) has passed since last file detection
            current_time = time.time()
            if last_file_detected_time is not None:
                time_since_last_file = current_time - last_file_detected_time
                
                # If 1 minute has passed with no file activity, log statistics and reset
                if time_since_last_file >= 60 and statistics_reset_time is None:
                    global bytes_moved, bytes_deleted
                    # Log statistics before resetting (if there are any to log)
                    # Check if there are any statistics to log
                    has_stats = (stats["files_moved_to_destination"] > 0 or 
                                stats["files_moved_to_duplicates"] > 0 or 
                                stats["files_deleted"] > 0 or
                                bytes_moved > 0 or bytes_deleted > 0)
                    if has_stats:
                        log_statistics("timeout", force=True)
                    # Note: We don't reset the persistent statistics (stats dict) as those
                    # are cumulative. Only reset the session-based bytes_moved/bytes_deleted
                    bytes_moved = 0
                    bytes_deleted = 0
                    statistics_reset_time = current_time
                    # Reset the last file detected time to prevent repeated resets
                    last_file_detected_time = current_time
    except KeyboardInterrupt:
        print("\nStopping folder watcher...")
        observer.stop()
    
    observer.join()
    print("Folder watcher stopped.")

if __name__ == "__main__":
    # Register cleanup function to log statistics on exit (only if not already logged)
    def exit_handler():
        global statistics_already_logged
        if not statistics_already_logged:
            # Force save statistics before logging
            save_statistics(force=True)
            log_statistics()
    atexit.register(exit_handler)
    
    # Register signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal, logging statistics...")
        try:
            # Force save statistics before logging
            save_statistics(force=True)
            log_statistics()
            log_system_event("Info", "Photo Organizer service stopped by signal")
        except Exception as e:
            print(f"Error logging statistics: {e}")
        sys.exit(0)
    
    # Only register signal handlers on Unix-like systems (Windows handles CTRL-C differently)
    if hasattr(signal, 'SIGINT'):
        try:
            signal.signal(signal.SIGINT, signal_handler)
        except (AttributeError, ValueError):
            pass  # Signal handling not available on this platform
    if hasattr(signal, 'SIGTERM'):
        try:
            signal.signal(signal.SIGTERM, signal_handler)
        except (AttributeError, ValueError):
            pass  # Signal handling not available on this platform
    
    # Initialize system log first
    initialize_system_log()
    
    # Load runtime configuration (paths, duplicate policy)
    load_runtime_config()
    
    # Detect if running on Synology NAS and log it
    if is_synology_nas():
        log_system_event("Info", "Photo Organizer service starting (Synology NAS detected)")
        print(f"Synology NAS detected - using {SOURCE_DIR} as source directory")
    else:
        log_system_event("Info", "Photo Organizer service starting")
    
    # Test dependencies first
    if not test_dependencies():
        print("ERROR: Required dependencies are missing. Please install them before running the script.")
        log_system_event("Error", "Photo Organizer service failed to start: Missing required dependencies")
        sys.exit(1)
    
    print("=" * 80)
    
    # Initialize log file
    initialize_log_file()
    print(f"Log file: {LOG_FILE}")
    print(f"System log: {SYSTEM_LOG_FILE}")
    print(f"Source directory: {os.path.abspath(SOURCE_DIR) if not os.path.isabs(SOURCE_DIR) else SOURCE_DIR}")
    print(f"Destination directory: {os.path.abspath(DEST_DIR) if not os.path.isabs(DEST_DIR) else DEST_DIR}")
    print("=" * 80)
    print()
    
    log_system_event("Info", "Photo Organizer service started successfully and watching for new files")
    
    # Process any existing photos first
    print("Processing existing photos...")
    move_photos_by_date()
    print("Existing photos processed.\n")
    
    # Start watching for new files
    statistics_logged = False
    try:
        start_watching()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, logging statistics...")
        log_statistics()
        statistics_logged = True
        log_system_event("Info", "Photo Organizer service stopped by user")
    except Exception as e:
        log_statistics()
        statistics_logged = True
        log_system_event("Error", f"Photo Organizer service stopped due to error: {str(e)}")
        raise
    finally:
        # Log statistics before stopping (in case it wasn't logged above)
        if not statistics_logged:
            log_statistics()
        log_system_event("Info", "Photo Organizer service stopped")
