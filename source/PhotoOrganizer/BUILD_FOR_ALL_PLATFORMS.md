# Building PhotoOrganizer for All Platforms

## Problem
The package was built only for `geminilake` platform, but your NAS might be a different platform.

## Solution: Build for All Platforms

Since PhotoOrganizer is a Python package (no platform-specific binaries), it can run on all Synology NAS platforms.

### Option 1: Build for All Available Platforms (Recommended)

```bash
cd /home/remco/DSM-Projects/pkgscripts-ng

# Build for all platforms you have build environments for
./PkgCreate.py -v 7.2 -c PhotoOrganizer
```

This will create packages for all platforms you've deployed build environments for.

### Option 2: Build for Specific Common Platforms

```bash
# Build for common x86_64 platforms
./PkgCreate.py -v 7.2 -p "geminilake avoton broadwell apollolake denverton" -c PhotoOrganizer
```

### Option 3: Find Your NAS Platform and Build for It

1. **Find your NAS platform:**
   - SSH into your NAS
   - Run: `uname -m` or `cat /proc/sys/kernel/syno_hw_version`
   - Or check in DSM: Control Panel > Info Center > Model

2. **Common platform mappings:**
   - DS220+, DS720+, DS920+ → `geminilake`
   - DS218+, DS718+ → `apollolake`
   - DS216+, DS716+ → `avoton`
   - DS415+, DS1515+ → `avoton`
   - DS918+ → `apollolake`
   - DS218play → `rtd1296`
   - DS220j, DS120j → `rtd1296`

3. **Build for your specific platform:**
   ```bash
   ./PkgCreate.py -v 7.2 -p <your-platform> -c PhotoOrganizer
   ```

## After Building

Check the result_spk directory:
```bash
ls -lh /home/remco/DSM-Projects/result_spk/
```

You should see packages for multiple platforms. Install the one that matches your NAS.

