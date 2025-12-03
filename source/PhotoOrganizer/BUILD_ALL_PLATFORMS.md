# Building PhotoOrganizer for All Platforms

## Overview

Since PhotoOrganizer is a Python package (no platform-specific compiled binaries), you can build it for all platforms. Each platform will get its own `.spk` file, but the package contents are identical.

## Option 1: Build for All Deployed Platforms (Recommended)

If you have multiple build environments deployed, build for all of them:

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Build for ALL platforms you have build environments for
./PkgCreate.py -v 7.2 -c PhotoOrganizer
```

This will automatically detect all platforms you have build environments for and build packages for each.

## Option 2: Build for Specific Platforms

If you want to build for specific platforms:

```bash
# Build for multiple specific platforms
./PkgCreate.py -v 7.2 -p "geminilake rtd1296 avoton apollolake" -c PhotoOrganizer
```

## Option 3: Use geminilake Package for All Platforms (NOT Recommended)

**Note:** While you *could* try to install the geminilake package on other platforms, it's **not recommended** because:
- The package metadata specifies the platform (`arch` field in INFO)
- DSM Package Center checks platform compatibility
- You'll get "incompatible platform" errors

## Deploy Build Environments for Common Platforms

To build for multiple platforms, deploy their build environments first:

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Deploy common platforms
./EnvDeploy -v 7.2 -p geminilake  # DS220+, DS720+, DS920+ (already deployed)
./EnvDeploy -v 7.2 -p rtd1296    # DS218play, DS220j, DS120j
./EnvDeploy -v 7.2 -p apollolake # DS218+, DS718+
./EnvDeploy -v 7.2 -p avoton      # DS216+, DS716+
./EnvDeploy -v 7.2 -p broadwell   # DS415+, DS1515+

# Fix permissions for all
sudo chown -R $USER:$USER /home/remco/DSM-Projects/build_env
```

## Build for All Deployed Platforms

After deploying environments, build for all:

```bash
# This will build for ALL platforms you have environments for
./PkgCreate.py -v 7.2 -c PhotoOrganizer
```

## Find Your Packages

After building, you'll find packages for each platform:

```bash
ls -lh /home/remco/DSM-Projects/result_spk/
```

You should see something like:
- `PhotoOrganizer-geminilake-7.2_1.0.0-0001.spk`
- `PhotoOrganizer-rtd1296-7.2_1.0.0-0001.spk`
- `PhotoOrganizer-apollolake-7.2_1.0.0-0001.spk`
- etc.

## Install the Correct Package

Install the package that matches your NAS platform:
- Check your NAS model/platform
- Install the corresponding `.spk` file

## Why Build for Multiple Platforms?

Even though it's a Python package:
- Each platform's package has correct metadata
- Package Center validates platform compatibility
- Users can easily find the right package for their NAS
- Follows Synology package development best practices

