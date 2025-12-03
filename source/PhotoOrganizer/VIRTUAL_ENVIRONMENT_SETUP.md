# Virtual Environment Setup for PhotoOrganizer Package

## Overview

The PhotoOrganizer package now runs in its own isolated Python virtual environment to ensure:
- **Dependency Isolation**: Package dependencies don't conflict with system Python packages
- **Version Control**: Specific package versions are maintained independently
- **Clean Uninstall**: Virtual environment can be removed without affecting system Python

## Python Version Requirements

- **Minimum Python Version**: 3.7 or higher
- **Check**: The package verifies Python version during pre-installation
- **Dependency**: Specified in `SynoBuildConf/depends` as `python3>=3.7`

## PIP Availability

- **Requirement**: `pip3` must be available on the system
- **Check**: The package verifies pip3 availability during pre-installation
- **Usage**: pip3 is used to install dependencies in the virtual environment

## Virtual Environment Location

The virtual environment is created at:
```
/usr/local/PhotoOrganizer/venv/
```

## Installation Process

### 1. Pre-Installation Checks (`preinst`)
- Verifies Python 3.7+ is installed
- Verifies pip3 is available
- Exits with error if requirements not met

### 2. Post-Installation Setup (`postinst`)
- Creates virtual environment: `python3 -m venv /usr/local/PhotoOrganizer/venv`
- Activates virtual environment
- Upgrades pip in the venv
- Installs dependencies: `Pillow>=12.0.0`, `watchdog`, `imagehash`, `mutagen`
- Deactivates virtual environment

### 3. Service Execution (`start-stop-status`)
- Uses virtual environment Python: `/usr/local/PhotoOrganizer/venv/bin/python`
- Runs Photo_Organizer.py with isolated dependencies
- Verifies venv exists before starting service

### 4. Upgrade Process (`postupgrade`)
- Recreates venv if missing
- Upgrades pip and all dependencies in venv
- Ensures service uses updated dependencies

## Dependencies Installed in Virtual Environment

- **Pillow** (>=12.0.0): Image processing and EXIF metadata
- **watchdog**: File system monitoring
- **imagehash**: Perceptual image hashing for duplicate detection
- **mutagen**: Audio metadata handling (if needed)

## Benefits

1. **Isolation**: No conflicts with system Python packages
2. **Reproducibility**: Same dependencies across installations
3. **Security**: Isolated from system Python environment
4. **Maintainability**: Easy to update or remove dependencies

## Manual Virtual Environment Management

If you need to manually manage the virtual environment:

```bash
# Activate virtual environment
source /usr/local/PhotoOrganizer/venv/bin/activate

# Install additional packages
pip install package-name

# Upgrade packages
pip install --upgrade package-name

# List installed packages
pip list

# Deactivate
deactivate
```

## Troubleshooting

### Virtual Environment Not Created
- Check Python 3.7+ is installed: `python3 --version`
- Check pip3 is available: `pip3 --version`
- Check installation logs: `/var/log/packages/PhotoOrganizer.log`

### Service Won't Start
- Verify venv exists: `ls -la /usr/local/PhotoOrganizer/venv/bin/python`
- Check service logs: `/var/log/photo-organizer.log`
- Reinstall package to recreate venv

### Dependency Issues
- Reinstall package to recreate venv with fresh dependencies
- Check requirements.txt for correct versions
- Verify internet connection for pip downloads

