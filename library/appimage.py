#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

DOCUMENTATION = r"""
module: appimage
short_description: Manage AppImage applications
description:
  - Downloads and installs AppImage applications.
  - Extracts the bundled C(.desktop) file, rewrites C(Exec=),
    C(TryExec=), and C(Icon=) to point to installed absolute paths,
    and symlinks it into C(~/.local/share/applications/).
  - Pulls icons from the AppImage hicolor theme or C(.DirIcon) and
    installs them into C(~/.local/share/icons/hicolor/).
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
      - Desired state for the AppImage application.
      - V(present) downloads and installs the AppImage when absent.
        If the AppImage already exists but the desktop entry is missing,
        only the desktop entry is recreated without re-downloading.
      - V(latest) re-downloads the AppImage and re-extracts the desktop entry.
      - V(absent) removes the AppImage and desktop entry.
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
      - URL to download the AppImage from.
      - Required when O(state=present) or O(state=latest).
    type: str
  args:
    description:
      - Extra arguments to pass when launching the AppImage.
    type: str
author:
  - Leandro Lemos (@ceso)
"""

EXAMPLES = r"""
- name: Install Ghostty
  appimage:
    name: ghostty
    url: "https://github.com/pkgforge-dev/ghostty-appimage/releases/download/v1.3.1/Ghostty-1.3.1-x86_64.AppImage"

- name: Install appimageupdatetool
  appimage:
    name: appimageupdatetool
    url: "https://github.com/AppImageCommunity/AppImageUpdate/releases/download/2.0.0-alpha-1-20251018/appimageupdatetool-x86_64.AppImage"

- name: Remove an AppImage
  appimage:
    name: ghostty
    state: absent

- name: Manage AppImages in a loop
  appimage:
    name: "{{ item.name }}"
    url: "{{ item.url }}"
    state: "{{ item.state | default('present') }}"
  loop:
    - name: ghostty
      url: "https://example.com/ghostty.AppImage"
    - name: appimageupdatetool
      url: "https://example.com/appimageupdatetool.AppImage"
  loop_control:
    label: "{{ item.name }}"
"""

RETURN = r"""
actions:
  description: List of actions performed.
  type: list
  elements: str
  returned: always
  sample: ["downloaded", "desktop_extracted"]
appimage_path:
  description: Path to the installed AppImage file.
  type: str
  returned: always
  sample: "/home/user/.local/bin/ghostty.AppImage"
"""

import os
import shutil
import tempfile

from ansible.module_utils.basic import AnsibleModule

_PREFERRED_ICON_SIZES = ("512x512", "256x256", "128x128", "64x64", "48x48")


# ── path helpers ──────────────────────────────────────────────────────


def _home() -> str:
    return os.path.expanduser("~")


def _bin_dir() -> str:
    return os.path.join(_home(), ".local", "bin")


def _share_dir(name: str) -> str:
    return os.path.join(_home(), ".local", "share", name)


def _appimage_path(name: str) -> str:
    return os.path.join(_bin_dir(), "{0}.AppImage".format(name))


def _applications_dir() -> str:
    return os.path.join(_home(), ".local", "share", "applications")


def _desktop_path(name: str) -> str:
    return os.path.join(_applications_dir(), "{0}.desktop".format(name))


def _hicolor_apps_dir(size: str) -> str:
    return os.path.join(_home(), ".local", "share", "icons", "hicolor", size, "apps")


# ── ensure helpers ────────────────────────────────────────────────────


def _ensure_directory(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, 0o755)


def _ensure_download(module: AnsibleModule, url: str, dest: str, force: bool = False) -> bool:
    if os.path.exists(dest) and not force:
        return False
    if module.check_mode:
        return True
    module.run_command(["curl", "-fsSL", "-o", dest, url], check_rc=True)
    os.chmod(dest, 0o755)
    return True


# ── icon extraction ───────────────────────────────────────────────────


def _extract_icons(module: AnsibleModule, appimage_path: str,
                   icon_name: str) -> str | None:
    tmpdir = tempfile.mkdtemp(prefix="appimage_icon_")
    try:
        squashfs = os.path.join(tmpdir, "squashfs-root")

        module.run_command(
            ["bash", "-c", "cd {0} && {1} --appimage-extract 'usr/share/icons'".format(
                tmpdir, appimage_path)],
            check_rc=False,
        )

        hicolor_root = os.path.join(squashfs, "usr", "share", "icons", "hicolor")
        installed_paths: list[tuple[str, str]] = []

        if os.path.isdir(hicolor_root):
            for size in os.listdir(hicolor_root):
                src_dir = os.path.join(hicolor_root, size, "apps")
                if not os.path.isdir(src_dir):
                    continue
                for f in os.listdir(src_dir):
                    if f.endswith((".png", ".svg")):
                        dest_dir = _hicolor_apps_dir(size)
                        _ensure_directory(dest_dir)
                        dest = os.path.join(dest_dir, f)
                        shutil.copy2(os.path.join(src_dir, f), dest)
                        installed_paths.append((size, dest))

        if installed_paths:
            by_size = {s: p for s, p in installed_paths}
            return next(
                (by_size[s] for s in _PREFERRED_ICON_SIZES if s in by_size),
                installed_paths[0][1],
            )

        # Fallback: resolve .DirIcon (may be a multi-level symlink chain)
        module.run_command(
            ["bash", "-c", "cd {0} && {1} --appimage-extract '.DirIcon'".format(
                tmpdir, appimage_path)],
            check_rc=False,
        )

        diricon = os.path.join(squashfs, ".DirIcon")
        if not os.path.exists(diricon) and not os.path.islink(diricon):
            return None

        current = diricon
        for _ in range(5):
            if not os.path.islink(current):
                break
            target = os.readlink(current)
            module.run_command(
                ["bash", "-c", "cd {0} && {1} --appimage-extract '{2}'".format(
                    tmpdir, appimage_path, target)],
                check_rc=False,
            )
            current = os.path.join(squashfs, target)

        if not os.path.isfile(current):
            return None

        best_size = _PREFERRED_ICON_SIZES[0]
        dest_dir = _hicolor_apps_dir(best_size)
        _ensure_directory(dest_dir)
        dest = os.path.join(dest_dir, "{0}.png".format(icon_name))
        shutil.copy2(current, dest)
        return dest

    except Exception:
        return None

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── desktop extraction ────────────────────────────────────────────────


def _rewrite_desktop_line(line: str, exec_path: str,
                          args: str | None,
                          icon_path: str | None) -> str:
    if line.startswith("TryExec="):
        return "TryExec={0}".format(exec_path)
    if line.startswith("Exec="):
        _, _, value = line.partition("=")
        _, _, rest = value.partition(" ")
        parts = [exec_path]
        if args:
            parts.append(args)
        if rest:
            parts.append(rest)
        return "Exec={0}".format(" ".join(parts))
    if line.startswith("Icon=") and icon_path:
        return "Icon={0}".format(icon_path)
    return line


def _extract_and_install_desktop(module: AnsibleModule, appimage_path: str,
                                 name: str, args: str | None) -> bool:
    share = _share_dir(name)
    symlink = _desktop_path(name)
    exec_path = _appimage_path(name)
    tmpdir = tempfile.mkdtemp(prefix="appimage_desktop_")

    try:
        rc, _, _ = module.run_command(
            ["bash", "-c", "cd {0} && {1} --appimage-extract '*.desktop'".format(
                tmpdir, appimage_path)],
            check_rc=False,
        )
        if rc != 0:
            return False

        squashfs_root = os.path.join(tmpdir, "squashfs-root")
        if not os.path.isdir(squashfs_root):
            return False

        desktop_files = [f for f in os.listdir(squashfs_root) if f.endswith(".desktop")]
        if not desktop_files:
            return False

        original_name = desktop_files[0]
        src = os.path.join(squashfs_root, original_name)

        with open(src, "r") as fh:
            lines = fh.read().splitlines()

        original_icon = next(
            (l.partition("=")[2].strip() for l in lines if l.startswith("Icon=")),
            None,
        )
        icon_path = None
        if original_icon:
            icon_path = _extract_icons(module, appimage_path, original_icon)

        new_lines = [_rewrite_desktop_line(l, exec_path, args, icon_path) for l in lines]
        if new_lines and not new_lines[0].startswith("#!"):
            new_lines.insert(0, "#!/usr/bin/env xdg-open")
        new_content = "\n".join(new_lines) + "\n"

        dest = os.path.join(share, original_name)

        if os.path.exists(dest):
            with open(dest, "r") as fh:
                if fh.read() == new_content and os.path.islink(symlink) and os.readlink(symlink) == dest:
                    return False

        _ensure_directory(share)
        with open(dest, "w") as fh:
            fh.write(new_content)
        os.chmod(dest, 0o644)

        _ensure_directory(_applications_dir())
        if os.path.islink(symlink) or os.path.exists(symlink):
            os.remove(symlink)
        os.symlink(dest, symlink)

        return True

    except Exception as exc:
        module.warn("Exception during .desktop extraction: {0}".format(exc))
        return False

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── removal helpers ───────────────────────────────────────────────────


def _remove_file(path: str) -> bool:
    if os.path.exists(path) or os.path.islink(path):
        os.remove(path)
        return True
    return False


def _remove_dir(path: str) -> bool:
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        return True
    return False


def _icon_paths(name: str):
    return (
        os.path.join(_hicolor_apps_dir(size), "{0}{1}".format(name, ext))
        for size in _PREFERRED_ICON_SIZES
        for ext in (".png", ".svg")
    )


def _remove_icons(name: str) -> bool:
    removed = False
    for path in _icon_paths(name):
        if os.path.exists(path):
            os.remove(path)
            removed = True
    return removed


# ── state handlers ────────────────────────────────────────────────────


def _state_install(module: AnsibleModule, force_download: bool = False) -> tuple[bool, list[str]]:
    name = module.params["name"]
    url = module.params["url"]
    args = module.params.get("args")

    actions: list[str] = []
    changed = False

    appimage = _appimage_path(name)
    _ensure_directory(_bin_dir())

    need_download = force_download or not os.path.exists(appimage)

    if need_download:
        if _ensure_download(module, url, appimage, force=force_download):
            actions.append("downloaded")
            changed = True

    need_desktop = force_download or not os.path.exists(_desktop_path(name))
    if need_desktop and not module.check_mode:
        if _extract_and_install_desktop(module, appimage, name, args):
            actions.append("desktop_extracted")
            changed = True

    return changed, actions


def state_present(module: AnsibleModule) -> tuple[bool, list[str]]:
    return _state_install(module, force_download=False)


def state_latest(module: AnsibleModule) -> tuple[bool, list[str]]:
    return _state_install(module, force_download=True)


def state_absent(module: AnsibleModule) -> tuple[bool, list[str]]:
    name = module.params["name"]

    if module.check_mode:
        exists = os.path.exists(_appimage_path(name))
        return exists, ["removed"] if exists else []

    actions: list[str] = []
    changed = False

    if _remove_file(_desktop_path(name)):
        actions.append("desktop_entry_removed")
        changed = True

    if _remove_dir(_share_dir(name)):
        actions.append("share_dir_removed")
        changed = True

    if _remove_icons(name):
        actions.append("icons_removed")
        changed = True

    if _remove_file(_appimage_path(name)):
        actions.append("appimage_removed")
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
            args=dict(type="str"),
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
        appimage_path=_appimage_path(name),
    )


if __name__ == "__main__":
    main()
