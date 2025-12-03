# Debugging Photo Organizer Service Issues

## Problem: Service Stops Automatically After a Few Seconds

If the service shows "Photo Organizer is not running" shortly after starting, follow these debugging steps:

## Step 1: Check the Log File

The most important step - check what errors are being logged:

```bash
# Check the main log file
tail -n 100 /var/packages/PhotoOrganizer/photo-organizer.log

# Or if it's in an alternative location:
tail -n 100 /var/packages/PhotoOrganizer/target/var/photo-organizer.log
tail -n 100 /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/var/photo-organizer.log
```

## Step 2: Check System Log

```bash
# Check system log
cat /var/packages/PhotoOrganizer/System.log

# Or alternative location:
cat /var/packages/PhotoOrganizer/target/var/System.log
```

## Step 3: Check if Process is Actually Running

```bash
# Check if the Python process is running
ps aux | grep Photo_Organizer.py

# Check the PID file
cat /var/run/photo-organizer.pid

# Verify if that PID is actually running
ps -p $(cat /var/run/photo-organizer.pid)
```

## Step 4: Test Python Script Manually

Run the script manually to see what errors occur:

```bash
# Find the script location
ls -la /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/Photo_Organizer.py

# Find the Python interpreter
ls -la /var/packages/PhotoOrganizer/venv/bin/python

# Run the script manually (this will show errors immediately)
/var/packages/PhotoOrganizer/venv/bin/python /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/Photo_Organizer.py
```

## Step 5: Check Dependencies

The script exits with code 1 if dependencies are missing:

```bash
# Test if dependencies are installed
/var/packages/PhotoOrganizer/venv/bin/python -c "import PIL; import watchdog; import imagehash; import mutagen; print('All dependencies OK')"
```

## Step 6: Check Permissions

```bash
# Check if script is executable
ls -la /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/Photo_Organizer.py

# Check if directories exist and are accessible
ls -la /var/packages/PhotoOrganizer/
ls -la /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/

# Check if source/destination directories exist
ls -la /volume1/photo/
ls -la /var/services/photo/
```

## Step 7: Check Configuration File

```bash
# Check if config file exists and is readable
cat /var/packages/PhotoOrganizer/config.ini

# Or alternative locations:
cat /var/packages/PhotoOrganizer/var/config.ini
cat /var/packages/PhotoOrganizer/target/var/config.ini
```

## Step 8: Run with Verbose Output

Modify the start script temporarily to see what's happening:

```bash
# Edit the start script to add debugging
vi /var/packages/PhotoOrganizer/target/scripts/start-stop-status

# In the start section, change:
"$VENV_PYTHON" "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1 &

# To:
"$VENV_PYTHON" -u "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1 &
# The -u flag makes Python output unbuffered
```

## Step 9: Check Service Status

```bash
# Check service status
/var/packages/PhotoOrganizer/target/scripts/start-stop-status status

# Check what DSM sees
# Go to Package Center > Photo Organizer > Status
```

## Common Issues and Solutions

### Issue 1: Missing Dependencies
**Symptom:** Script exits immediately with "Required dependencies are missing"
**Solution:** Reinstall the package or manually install dependencies in venv

### Issue 2: Source/Destination Directory Doesn't Exist
**Symptom:** Script can't find source or destination directory
**Solution:** Create the directories or update config.ini with correct paths

### Issue 3: Permission Denied
**Symptom:** "Permission denied" errors in log
**Solution:** Check that PhotoOrganizer user has read/write access to photo shared folder

### Issue 4: Python Script Syntax Error
**Symptom:** Python errors in log file
**Solution:** Check the log file for specific Python errors

### Issue 5: PID File Contains Wrong PID
**Symptom:** Service shows as running but process doesn't exist
**Solution:** Remove PID file and restart: `rm /var/run/photo-organizer.pid`

## Quick Diagnostic Script

Run this to get a full diagnostic:

```bash
#!/bin/sh
echo "=== Photo Organizer Diagnostic ==="
echo ""
echo "1. PID File:"
ls -la /var/run/photo-organizer.pid 2>/dev/null || echo "  PID file not found"
if [ -f /var/run/photo-organizer.pid ]; then
    PID=$(cat /var/run/photo-organizer.pid)
    echo "  PID: $PID"
    ps -p $PID > /dev/null 2>&1 && echo "  Process is running" || echo "  Process is NOT running (stale PID)"
fi
echo ""
echo "2. Python Process:"
ps aux | grep Photo_Organizer.py | grep -v grep || echo "  No Photo_Organizer.py process found"
echo ""
echo "3. Script Location:"
ls -la /var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/Photo_Organizer.py 2>/dev/null || echo "  Script not found"
echo ""
echo "4. Python Interpreter:"
ls -la /var/packages/PhotoOrganizer/venv/bin/python 2>/dev/null || echo "  Python not found in primary location"
ls -la /var/packages/PhotoOrganizer/target/var/venv/bin/python 2>/dev/null || echo "  Python not found in alternative location"
echo ""
echo "5. Log File (last 20 lines):"
tail -n 20 /var/packages/PhotoOrganizer/photo-organizer.log 2>/dev/null || echo "  Log file not found"
echo ""
echo "6. Dependencies Test:"
/var/packages/PhotoOrganizer/venv/bin/python -c "import PIL; import watchdog; import imagehash; import mutagen; print('  All dependencies OK')" 2>&1 || echo "  Dependencies missing or error"
echo ""
echo "7. Configuration:"
cat /var/packages/PhotoOrganizer/config.ini 2>/dev/null || echo "  Config file not found"
```

