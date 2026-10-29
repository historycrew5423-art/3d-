"""Extract RPM payloads without cpio: pipe through rpm2cpio, then parse the newc cpio stream."""
import os
import subprocess
import sys

dest = sys.argv[1]
for rpm in sys.argv[2:]:
    data = subprocess.run(["rpm2cpio", rpm], check=True, capture_output=True).stdout
    pos = 0
    while pos + 110 <= len(data):
        hdr = data[pos:pos + 110]
        if hdr[:6] not in (b"070701", b"070702"):
            raise SystemExit(f"bad cpio header in {rpm}")
        mode = int(hdr[14:22], 16)
        filesize = int(hdr[54:62], 16)
        namesize = int(hdr[94:102], 16)
        name_start = pos + 110
        name = data[name_start:name_start + namesize - 1].decode()
        pos = (name_start + namesize + 3) & ~3
        body = data[pos:pos + filesize]
        pos = (pos + filesize + 3) & ~3
        if name == "TRAILER!!!":
            break
        path = os.path.join(dest, name.lstrip("./"))
        kind = mode & 0o170000
        if kind == 0o040000:
            os.makedirs(path, exist_ok=True)
        elif kind == 0o120000:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.lexists(path):
                os.remove(path)
            os.symlink(body.decode(), path)
        elif kind == 0o100000:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(body)
            os.chmod(path, mode & 0o777)
    print("extracted", os.path.basename(rpm))
