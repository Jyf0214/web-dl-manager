# Gallery-DL Web - Binary Build

This project can be built into a standalone binary executable for easy distribution and deployment.

## Building the Binary

To build the application into a binary:

```bash
# Make the build script executable
chmod +x build.sh

# Run the build script
./build.sh
```

Alternatively, you can run the build script directly with Python:

```bash
python build.py
```

The binary will be created in the `dist/` directory.

## Running the Binary

After building, you can run the binary directly:

```bash
# On Linux/macOS
./dist/gallery-dl-web/gallery-dl-web

# On Windows
./dist/gallery-dl-web/gallery-dl-web.exe
```

Or use the Python run script:

```bash
python run_binary.py --port 8000 --host 0.0.0.0
```

## Requirements for Building

- Python 3.7+
- pip

The build process will automatically install PyInstaller and other necessary dependencies.

## What the Build Includes

- The main application code
- All necessary dependencies
- Templates and static files
- Configuration files

## Notes

- The binary includes all dependencies, so it can run independently without Python installed
- The first run after building may take a little longer as it extracts necessary files
- The binary will be larger than the source code due to included dependencies