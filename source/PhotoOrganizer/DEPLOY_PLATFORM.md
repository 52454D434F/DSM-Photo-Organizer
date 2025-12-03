# Deploy Build Environment for Additional Platforms

## Problem
You're trying to build for a platform (rtd1296) that doesn't have a build environment deployed yet.

## Solution: Deploy the Build Environment

Before building for a platform, you need to deploy its build environment.

### Step 1: Deploy Build Environment for rtd1296

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Deploy build environment for rtd1296
./EnvDeploy -v 7.2 -p rtd1296
```

This will download and set up the chroot environment for rtd1296 platform.

**Note:** This may take a while as it downloads the build environment.

### Step 2: Fix Permissions (if needed)

```bash
sudo chown -R $USER:$USER /home/remco/DSM-Projects/build_env/ds.rtd1296-7.2
```

### Step 3: Build the Package

```bash
./PkgCreate.py -v 7.2 -p rtd1296 -c PhotoOrganizer
```

## Build for Multiple Platforms

If you want to build for multiple platforms, deploy environments for each:

```bash
# Deploy multiple platforms
./EnvDeploy -v 7.2 -p geminilake
./EnvDeploy -v 7.2 -p rtd1296
./EnvDeploy -v 7.2 -p avoton
./EnvDeploy -v 7.2 -p apollolake

# Then build for all of them
./PkgCreate.py -v 7.2 -p "geminilake rtd1296 avoton apollolake" -c PhotoOrganizer
```

## List Available Platforms

To see all available platforms for DSM 7.2:

```bash
./EnvDeploy -v 7.2 -l
```

## Common Platform Deployments

For a Python package like PhotoOrganizer, you typically need these common platforms:

```bash
# Deploy common platforms
./EnvDeploy -v 7.2 -p geminilake  # DS220+, DS720+, DS920+
./EnvDeploy -v 7.2 -p apollolake  # DS218+, DS718+
./EnvDeploy -v 7.2 -p avoton      # DS216+, DS716+
./EnvDeploy -v 7.2 -p rtd1296    # DS218play, DS220j, DS120j
./EnvDeploy -v 7.2 -p broadwell   # DS415+, DS1515+
```

Then build for all:
```bash
./PkgCreate.py -v 7.2 -p "geminilake apollolake avoton rtd1296 broadwell" -c PhotoOrganizer
```

