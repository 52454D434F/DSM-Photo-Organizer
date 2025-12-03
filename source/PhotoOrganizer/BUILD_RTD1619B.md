# Building PhotoOrganizer for rtd1619b Platform

This guide explains how to build the PhotoOrganizer package for the **rtd1619b** platform (DSM 7.2).

## Prerequisites

- WSL (Windows Subsystem for Linux) with Ubuntu
- Synology Package Toolkit (`pkgscripts-ng`) installed
- DSM 7.2 build environment

## Step 1: Clean Up Old Build Environments (Optional)

If you have old build environments you want to remove:

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Remove rtd1296 environment if it exists
sudo rm -rf /home/remco/DSM-Projects/build_env/ds.rtd1296-7.2
```

## Step 2: Deploy rtd1619b Build Environment

Deploy the build environment for rtd1619b:

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Deploy rtd1619b environment for DSM 7.2
./EnvDeploy -v 7.2 -p rtd1619b
```

**Wait for completion** - You should see:
```
[INFO] All task finished.
```

This process will:
- Download the necessary toolchain tarballs
- Extract them into the build environment
- Set up the chroot environment

## Step 3: Fix Permissions (If Needed)

After deployment, fix ownership of the build environment:

```bash
# Fix ownership (ignore /proc errors - they're harmless)
sudo chown -R $USER:$USER /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2 2>/dev/null || true
```

Note: Some errors about `/proc`, `/sys`, or `/dev` are normal - these are virtual filesystems.

## Step 4: Verify Deployment

Check that the deployment was successful:

```bash
# Check if PkgVersion file exists (indicates successful deployment)
ls -la /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2/PkgVersion

# Check if bash exists (needed for script execution)
ls -la /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2/bin/bash

# Check if the script directory will be linked
ls -la /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2/pkgscripts-ng 2>/dev/null || echo "Will be linked during build"
```

## Step 5: Build the Package

Build the PhotoOrganizer package:

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Build for all deployed platforms automatically (recommended)
./PkgCreate.py -v 7.2 -c PhotoOrganizer
```

**Note:** Since the package is `noarch`, it will work on **all DSM platforms** regardless of which build environment is used. The build process will automatically detect and build for all platforms that have deployed environments in `build_env/`.

Alternatively, you can specify specific platforms:

```bash
# Build for specific platforms only
./PkgCreate.py -v 7.2 -p rtd1619b -c PhotoOrganizer
./PkgCreate.py -v 7.2 -p "geminilake rtd1619b" -c PhotoOrganizer
```

## Step 6: Find Your Built Package

After successful build, find your package:

```bash
ls -lh /home/remco/DSM-Projects/result_spk/
```

The package will be named something like:
- `PhotoOrganizer-1.0.0-0001-noarch-7.2.spk` (since `arch="noarch"` in INFO.sh)

**Important:** Even though the package name may include a platform identifier, the `noarch` architecture means it will install and work on **all DSM platforms**.

## Troubleshooting

### Error: "Chroot *ds.rtd1619b-7.2' not found"

The build environment wasn't deployed. Go back to Step 2.

### Error: "failed to run command '/pkgscripts-ng/SynoBuild': No such file or directory"

The script linking failed. Try:
```bash
# Re-link scripts
cd /home/remco/DSM-Projects/pkgscripts-ng
./PkgCreate.py -v 7.2 -p rtd1619b -c PhotoOrganizer
```

The build process will automatically link the scripts.

### Error: Permission Denied

The build environment might have permission issues. Try:
```bash
sudo chown -R $USER:$USER /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2/source
sudo chown -R $USER:$USER /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2/tmp
```

### Build Environment Incomplete

If the deployment seems incomplete, re-deploy:
```bash
cd /home/remco/DSM-Projects/pkgscripts-ng
sudo rm -rf /home/remco/DSM-Projects/build_env/ds.rtd1619b-7.2
./EnvDeploy -v 7.2 -p rtd1619b
```

## Installing the Package

1. Copy the `.spk` file to your Synology NAS
2. Open **Package Center** → **Manual Install**
3. Select the `.spk` file
4. Follow the installation wizard

The package will:
- **Automatically install Python 3.9** as a dependency (via `install_dep_packages` in INFO.sh)
- Create a Python virtual environment
- Install dependencies from `requirements.txt`
- Set up the service to run automatically

## Notes

- The build process uses `sudo` automatically for chroot operations (WSL requirement)
- Environment variables are passed via subprocess (no need for `env` command)
- Scripts are executed via `/bin/bash` explicitly (handles shebang issues)
- The package runs in its own Python virtual environment on the NAS

