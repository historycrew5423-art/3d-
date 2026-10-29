#!/usr/bin/env bash
# Install Blender (as a Python module, no GUI) in a Kiro Web sandbox.
# Verified 2026-10-29 on Amazon Linux 2023, Python 3.11, bpy 5.0.1.
#
# Usage:  bash tools/blender/setup.sh [install_dir]     (default: /projects/sandbox/.tools)
# Then:   <install_dir>/blender-py your_script.py
#
# Why it is done this way (see docs/13):
# - download.blender.org blocks scripted downloads, so Blender comes from PyPI ("bpy").
# - The system disk is read-only, so dnf cannot install libraries. We download the
#   RPMs and unpack them into the install dir, then point LD_LIBRARY_PATH at them.
# - /tmp can be wiped during a session, and most of /projects is read-only, so the
#   default install dir is inside the workspace but outside the git repo.
set -euo pipefail

DIR="${1:-/projects/sandbox/.tools}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DIR"/{rpms,libroot,dnf/cache,dnf/log,dnf/persist}

python3 -m venv "$DIR/bpyenv"
"$DIR/bpyenv/bin/pip" install -q --upgrade pip
"$DIR/bpyenv/bin/pip" install -q "bpy==5.0.1"

# Libraries bpy needs that the sandbox image lacks: libSM, libICE, libGL (+ deps)
dnf install -y -q --downloadonly --downloaddir="$DIR/rpms" \
  --setopt=cachedir="$DIR/dnf/cache" --setopt=logdir="$DIR/dnf/log" \
  --setopt=persistdir="$DIR/dnf/persist" --setopt=install_weak_deps=False \
  libSM libICE mesa-libGL
python3 "$HERE/extract_rpm.py" "$DIR/libroot" "$DIR"/rpms/*.rpm

cat > "$DIR/blender-py" <<EOF
#!/usr/bin/env bash
export LD_LIBRARY_PATH="$DIR/libroot/usr/lib64\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
exec "$DIR/bpyenv/bin/python" "\$@"
EOF
chmod +x "$DIR/blender-py"

"$DIR/blender-py" -c "import bpy; print('Blender', bpy.app.version_string, 'ready')"
