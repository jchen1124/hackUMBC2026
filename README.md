# HackUMBC 2025 Project

This is the official repository for our HackUMBC 2025 project. It uses a high-performance C++ backend, managed by vcpkg, with a Python frontend.

## Installing (MacOS Only)

### Prerequisties

- Homebrew https://brew.sh/ (for package installation)
- Git
- CMake
- Python3
- C++ Compiler
  - Do `xcode-select --install
`

And all of these too! (You need homebrew)

```bash
brew install pkg-config autoconf autoconf-archive automake libtool
```

### Clone Repo

```bash
git clone --recursive https://github.com/jacomemateo/hackumbc2025
cd hackumbc2025
```

### Building and installing the C++ modules

```bash
# the first time run it like so (this command will take a WHILE 5-20 mins since it's dowloading and compiling a bunch of stuff but subsequent runs should be a lot faster):
VCPKG_GNU_MIRROR=https://mirror.rit.edu/gnu/ cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build --target install
```

### Set Up the Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Development Workflow

### Python

Make sure you guys are always using the python virutal enviroment to reduce errors. If you guys need to use a python package, do the whole `pip install xyz` BUT also make sure that you add said package to the `pyproject.toml` file under the `dependecies` and then run `pip-compile pyproject.toml` to update the `requirements.txt` file.

### C++

Every time you make a change to the C++ library you can just do:
`cmake --build build --target install`
If you guys are getting weird errors with CMake after editing any of the `CMakeLists.txt` file, then do `rm -rf build` and re-run the commands under the "Building and installing the C++ modules" section.
