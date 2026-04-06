#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

DOCUMENTATION = r"""
module: binaryapp
short_description: Manage binary applications distributed as archives
description:
  - Downloads an archive, extracts it into a temporary directory, moves
    the binary to C(~/.local/bin/), and cleans up.
  - Creates a C(.desktop) entry in C(~/.local/share/applications/)
    when C(desktop) options are provided.
  - Auto-detects icons from the extracted archive and installs them
    into C(~/.local/share/icons/hicolor/<size>/apps/).
attributes:
  check_mode:
    description: Can run in check mode and return changed status prediction without modifying the target.
    support: full
  diff_mode:
    description: Will return details on what has changed (or possibly needs changing in check mode) when in diff mode.
    support: none
options:
  state:
    description:
      - Desired state for the binary application.
      - V(present) downloads and installs the binary when absent.
      - V(latest) re-downloads and reinstalls the binary.
      - V(absent) removes the binary, desktop entry, and icons.
    type: str
    choices:
      - present
      - absent
      - latest
    default: present
  name:
    description:
      - Name of the application.
      - Used as the base name for all created files.
    type: str
    required: true
  url:
    description:
      - URL to download the archive from.
      - Required when O(state=present) or O(state=latest).
    type: str
  binary:
    description:
      - Filename of the binary inside the archive.
      - If not provided, O(name) is used.
    type: str
  checksum_url:
    description:
      - URL to a checksum file for the archive.
      - The hash algorithm is auto-detected from the hash length
        (MD5, SHA1, SHA224, SHA256, SHA384, SHA512).
      - Accepts both bare hashes and C(hash  filename) format.
      - When provided, the downloaded archive is verified before extraction.
        On mismatch the archive is deleted and the module fails.
    type: str
  desktop:
    description:
      - Desktop entry options. When provided, a C(.desktop) file is created.
    type: dict
    suboptions:
      display_name:
        description: Human-readable application name.
        type: str
        required: true
      comment:
        description: Short description of the application.
        type: str
        required: true
      categories:
        description: Semicolon-separated list of desktop categories.
        type: str
        required: true
author:
  - Leandro Lemos (@ceso)
"""

EXAMPLES = r"""
- name: Install WinBox
  binaryapp:
    name: winbox
    url: "https://download.mikrotik.com/routeros/winbox/4.0.1/WinBox_Linux.zip"
    binary: WinBox
    desktop:
      display_name: WinBox
      comment: Configuration tool for RouterOS
      categories: "Network;RemoteAccess;"

- name: Remove WinBox
  binaryapp:
    name: winbox
    state: absent

- name: Manage binary apps in a loop
  binaryapp:
    name: "{{ item.name }}"
    url: "{{ item.url }}"
    binary: "{{ item.binary | default(omit) }}"
    state: "{{ item.state | default('present') }}"
  loop:
    - name: winbox
      url: "https://download.mikrotik.com/routeros/winbox/4.0.1/WinBox_Linux.zip"
      binary: WinBox
  loop_control:
    label: "{{ item.name }}"
"""

RETURN = r"""
actions:
  description: List of actions performed.
  type: list
  elements: str
  returned: always
  sample: ["downloaded", "binary_installed", "desktop_created"]
binary_path:
  description: Path to the installed binary.
  type: str
  returned: always
  sample: "/home/user/.local/bin/winbox"
"""

import glob
import hashlib
import os
import re
import shutil
import tempfile

from ansible.module_utils.basic import AnsibleModule


# ── checksum verification ─────────────────────────────────────────────

_HASH_ALGO_BY_LENGTH: dict[int, str] = {
    32: "md5",
    40: "sha1",
    56: "sha224",
    64: "sha256",
    96: "sha384",
    128: "sha512",
}


def _parse_checksum_file(content: str) -> str:
    """Extract the hex hash from checksum file content.

    Handles both bare hashes and 'hash  filename' / 'hash *filename' formats.
    """
    for line in content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([0-9a-fA-F]+)(?:\s+.+)?$", line)
        if match:
            return match.group(1).lower()
    raise ValueError("No hex hash found in checksum file")


def _detect_hash_algo(hex_hash: str) -> str:
    """Detect hash algorithm from the length of the hex digest."""
    algo = _HASH_ALGO_BY_LENGTH.get(len(hex_hash))
    if algo is None:
        raise ValueError(
            "Cannot detect hash algorithm for digest length {0}".format(len(hex_hash))
        )
    return algo


def _compute_file_hash(path: str, algo: str) -> str:
    """Compute the hash of a file using the given algorithm."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_checksum(module: AnsibleModule, archive_path: str, checksum_url: str) -> None:
    """Download checksum file, auto-detect algo, verify archive. Deletes and fails on mismatch."""
    checksum_file = archive_path + ".checksum"
    module.run_command(["curl", "-fsSL", "-o", checksum_file, checksum_url], check_rc=True)

    try:
        with open(checksum_file, "r") as f:
            content = f.read()
        expected = _parse_checksum_file(content)
        algo = _detect_hash_algo(expected)
        actual = _compute_file_hash(archive_path, algo)
    finally:
        os.remove(checksum_file)

    if actual != expected:
        os.remove(archive_path)
        module.fail_json(
            msg="Checksum verification failed ({algo}): expected {expected}, got {actual}".format(
                algo=algo, expected=expected, actual=actual,
            )
        )


# ── path helpers ──────────────────────────────────────────────────────


def _home() -> str:
    return os.path.expanduser("~")


def _bin_dir() -> str:
    return os.path.join(_home(), ".local", "bin")


def _binary_path(name: str) -> str:
    return os.path.join(_bin_dir(), name)


def _applications_dir() -> str:
    return os.path.join(_home(), ".local", "share", "applications")


def _desktop_path(name: str) -> str:
    return os.path.join(_applications_dir(), "{0}.desktop".format(name))


def _hicolor_apps_dir(size: str) -> str:
    return os.path.join(_home(), ".local", "share", "icons", "hicolor", size, "apps")


_PREFERRED_ICON_SIZES = ("256x256", "128x128", "64x64", "48x48")


# ── ensure helpers ────────────────────────────────────────────────────


def _ensure_directory(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, 0o755)


def _download_archive(module: AnsibleModule, url: str, dest: str) -> None:
    module.run_command(["curl", "-fsSL", "-o", dest, url], check_rc=True)


# ── icon detection ───────────────────────────────────────────────────


def _icon_paths(name: str):
    return (
        os.path.join(_hicolor_apps_dir(size), "{0}{1}".format(name, ext))
        for size in _PREFERRED_ICON_SIZES
        for ext in (".png", ".svg")
    )


def _detect_and_install_icon(tmpdir: str, name: str) -> str | None:
    for pattern in ("**/*.png", "**/*.svg"):
        matches = glob.glob(os.path.join(tmpdir, pattern), recursive=True)
        if matches:
            ext = os.path.splitext(matches[0])[1]
            dest_dir = _hicolor_apps_dir(_PREFERRED_ICON_SIZES[0])
            _ensure_directory(dest_dir)
            dest = os.path.join(dest_dir, "{0}{1}".format(name, ext))
            shutil.copy2(matches[0], dest)
            return dest
    return None


def _find_installed_icon(name: str) -> str | None:
    return next((p for p in _icon_paths(name) if os.path.exists(p)), None)


def _remove_icons(name: str) -> bool:
    removed = False
    for path in _icon_paths(name):
        if os.path.exists(path):
            os.remove(path)
            removed = True
    return removed


# ── desktop creation ─────────────────────────────────────────────────


def _create_desktop(name: str, desktop: dict, icon_path: str | None) -> bool:
    dest = _desktop_path(name)
    exec_path = _binary_path(name)

    lines = [
        "#!/usr/bin/env xdg-open",
        "[Desktop Entry]",
        "Name={0}".format(desktop["display_name"]),
        "Comment={0}".format(desktop["comment"]),
        "Exec={0}".format(exec_path),
    ]
    if icon_path:
        lines.append("Icon={0}".format(icon_path))
    lines.extend([
        "Terminal=false",
        "Type=Application",
        "Categories={0}".format(desktop["categories"]),
    ])

    new_content = "\n".join(lines) + "\n"

    if os.path.exists(dest):
        with open(dest, "r") as fh:
            if fh.read() == new_content:
                return False

    _ensure_directory(_applications_dir())
    with open(dest, "w") as fh:
        fh.write(new_content)
    os.chmod(dest, 0o644)
    return True


# ── removal helpers ───────────────────────────────────────────────────


def _remove_file(path: str) -> bool:
    if os.path.exists(path) or os.path.islink(path):
        os.remove(path)
        return True
    return False


# ── state handlers ────────────────────────────────────────────────────


def _state_install(module: AnsibleModule, force: bool = False) -> tuple[bool, list[str]]:
    name = module.params["name"]
    url = module.params["url"]
    binary = module.params.get("binary") or name
    checksum_url = module.params.get("checksum_url")
    desktop = module.params.get("desktop")

    actions: list[str] = []
    changed = False
    binary_dest = _binary_path(name)

    need_download = force or not os.path.exists(binary_dest)

    if need_download:
        if module.check_mode:
            return True, ["downloaded"]

        _ensure_directory(_bin_dir())
        tmpdir = tempfile.mkdtemp(prefix="binaryapp_{0}_".format(name))
        try:
            archive = os.path.join(tmpdir, "archive")
            _download_archive(module, url, archive)
            actions.append("downloaded")

            if checksum_url:
                _verify_checksum(module, archive, checksum_url)
                actions.append("checksum_verified")

            module.run_command(
                ["bash", "-c", "cd {0} && unzip -qo archive || tar xf archive".format(tmpdir)],
                check_rc=False,
            )
            os.remove(archive)

            src = os.path.join(tmpdir, binary)
            if not os.path.isfile(src):
                for root, _dirs, files in os.walk(tmpdir):
                    if binary in files:
                        src = os.path.join(root, binary)
                        break

            if not os.path.isfile(src):
                module.fail_json(msg="Binary '{0}' not found in extracted archive".format(binary))

            shutil.move(src, binary_dest)
            os.chmod(binary_dest, 0o755)
            actions.append("binary_installed")
            changed = True

            icon_path = _detect_and_install_icon(tmpdir, name)
            if icon_path:
                actions.append("icon_installed")

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        icon_path = _find_installed_icon(name)

    if desktop and not module.check_mode:
        need_desktop = force or not os.path.exists(_desktop_path(name))
        if need_desktop:
            if _create_desktop(name, desktop, icon_path):
                actions.append("desktop_created")
                changed = True

    return changed, actions


def state_present(module: AnsibleModule) -> tuple[bool, list[str]]:
    return _state_install(module, force=False)


def state_latest(module: AnsibleModule) -> tuple[bool, list[str]]:
    return _state_install(module, force=True)


def state_absent(module: AnsibleModule) -> tuple[bool, list[str]]:
    name = module.params["name"]

    if module.check_mode:
        exists = os.path.exists(_binary_path(name))
        return exists, ["removed"] if exists else []

    actions: list[str] = []
    changed = False

    if _remove_file(_desktop_path(name)):
        actions.append("desktop_removed")
        changed = True

    if _remove_icons(name):
        actions.append("icons_removed")
        changed = True

    if _remove_file(_binary_path(name)):
        actions.append("binary_removed")
        changed = True

    return changed, actions


# ── dispatch ──────────────────────────────────────────────────────────


STATE_MAP: dict[str, callable] = {
    "present": state_present,
    "latest": state_latest,
    "absent": state_absent,
}


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type="str",
                default="present",
                choices=list(STATE_MAP.keys()),
            ),
            name=dict(type="str", required=True),
            url=dict(type="str"),
            checksum_url=dict(type="str"),
            binary=dict(type="str"),
            desktop=dict(
                type="dict",
                options=dict(
                    display_name=dict(type="str", required=True),
                    comment=dict(type="str", required=True),
                    categories=dict(type="str", required=True),
                ),
            ),
        ),
        required_if=[
            ("state", "present", ["url"]),
            ("state", "latest", ["url"]),
        ],
        supports_check_mode=True,
    )

    name = module.params["name"]
    changed, actions = STATE_MAP[module.params["state"]](module)

    module.exit_json(
        changed=changed,
        actions=actions,
        binary_path=_binary_path(name),
    )


if __name__ == "__main__":
    main()
