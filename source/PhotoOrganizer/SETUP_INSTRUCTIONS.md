# PhotoOrganizer Package Setup

## Package Structure Created

The PhotoOrganizer package has been set up with the following structure:

```
PhotoOrganizer/
├── Photo_Organizer.py          # Main Python script (service)
├── requirements.txt            # Python dependencies
├── README.md                   # Original README
├── INFO.sh                    # Package metadata
├── LICENSE                    # Package license
├── SynoBuildConf/
│   ├── build                  # Build script (installs Python deps)
│   ├── install                # Install script (packages files)
│   └── depends                # Package dependencies
├── scripts/
│   ├── start-stop-status      # Service control script
│   ├── preinst                # Pre-installation script
│   ├── postinst               # Post-installation script
│   ├── preuninst              # Pre-uninstallation script
│   ├── postuninst             # Post-uninstallation script
│   ├── preupgrade             # Pre-upgrade script
│   └── postupgrade            # Post-upgrade script
└── conf/
    ├── privilege               # Package privileges
    └── resource               # Resource configuration
```

## Next Steps

### 1. Flatten Directory Structure

Run this in your WSL terminal:
```bash
cd /home/remco/DSM-Projects/source/PhotoOrganizer
# Move files from Photo-Organizer/ subdirectory to current directory
mv Photo-Organizer/* . 2>/dev/null || true
rmdir Photo-Organizer 2>/dev/null || true
# Remove venv (not needed in package)
rm -rf venv_organizer
```

### 2. Make Scripts Executable

```bash
chmod +x INFO.sh
chmod +x SynoBuildConf/*
chmod +x scripts/*
chmod +x Photo_Organizer.py
```

### 3. Add Package Icons (Optional)

Copy icons from ExamplePackage or create your own:
```bash
# Copy example icons (you can replace with your own later)
cp ../ExamplePackage/PACKAGE_ICON*.PNG . 2>/dev/null || true
```

### 4. Build the Package

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng
./PkgCreate.py -v 7.2 -p geminilake -c PhotoOrganizer
```

### 5. Find Your Package

```bash
ls -lh /home/remco/DSM-Projects/result_spk/
```

## Package Features

- **Service Management**: Photo_Organizer.py runs as a background service
- **Auto-start**: Service can be started/stopped from Package Center
- **Python Dependencies**: Automatically installed during package installation
- **Logging**: Service logs to `/var/log/photo-organizer.log`
- **Default Paths**: 
  - Source: `/volume1/photo/PhotosToProcess`
  - Destination: `/volume1/photo/`

## Service Control

After installation, the service can be controlled via:
- Package Center (start/stop)
- Command line: `/var/packages/PhotoOrganizer/scripts/start-stop-status {start|stop|status}`

## Notes

- The service runs as the `package` user (configured in conf/privilege)
- Python dependencies are installed to user directory (`--user` flag)
- User photos in `/volume1/photo/` are preserved during uninstallation
- PID file is stored at `/var/run/photo-organizer.pid`

