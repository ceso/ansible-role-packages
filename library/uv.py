#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

DOCUMENTATION = r"""
module: uv
short_description: Manage Python tools with uv
version_added: "10.7.0"
description:
  - Manage Python tool packages via C(uv tool).
  - Each tool lives in its own isolated virtual environment.
attributes:
  check_mode:
    description: Can run in check mode and return changed status prediction without modifying the target.
    support: full
  diff_mode:
    description: Will return details on what has changed (or possibly needs changing in check mode) when in diff mode.
    support: full
options:
  state:
    description:
      - Desired state for the tool.
      - V(present) and V(install) install the tool when absent.
      - V(absent) and V(uninstall) remove the tool.
      - V(latest) installs if missing, then upgrades.
      - V(upgrade) upgrades an already-installed tool.
      - V(upgrade_all) upgrades every installed tool.
      - V(uninstall_all) removes every installed tool.
      - V(reinstall_all) force-reinstalls every installed tool.
    type: str
    choices:
      - present
      - absent
      - install
      - uninstall
      - latest
      - upgrade
      - upgrade_all
      - uninstall_all
      - reinstall_all
    default: present
  name:
    description:
      - Name of the tool to manage.
      - Required for all states except V(upgrade_all), V(uninstall_all), and V(reinstall_all).
    type: str
  version:
    description:
      - Version constraint, git tag, commit hash, or branch name.
      - For PyPI packages a plain version like C(0.3.0) implies C(==0.3.0).
        PEP 440 operators like C(>=1.0) are passed through.
      - For git sources (O(source) starts with C(git+)) the value is appended as C(@version) to the URL.
      - Only used with V(state=present), V(state=install), or V(state=latest).
    type: str
    version_added: "10.7.0"
  source:
    description:
      - Package specification passed to C(uv tool install --from).
      - Use for git URLs, alternative package names, or complex version constraints
        when the tool name differs from the package name.
      - Only used with V(state=present), V(state=install), or V(state=latest).
    type: str
  executable:
    description:
      - Path to the C(uv) binary.
      - Searches C(PATH) when not set.
    type: path
  python:
    description:
      - Python interpreter for the tool virtual environment.
      - Passed as C(--python) to C(uv tool install) and C(uv tool upgrade).
    type: str
  index_url:
    description:
      - Base URL of the Python Package Index.
      - Passed as C(--index-url).
    type: str
  force:
    description:
      - Force installation even when the tool is already present.
      - Passed as C(--force).
    type: bool
    default: false
  editable:
    description:
      - Install the package in editable mode.
      - Passed as C(--editable).
    type: bool
    default: false
  reinstall:
    description:
      - Reinstall tool packages inside the virtual environment.
      - Passed as C(--reinstall).
    type: bool
    default: false
  with_packages:
    description:
      - Extra packages for the tool virtual environment.
      - Each entry is passed as C(--with <package>).
    type: list
    elements: str
  with_executables_from:
    description:
      - Packages whose executables should be exposed alongside the tool.
      - Joined with commas and passed as C(--with-executables-from).
    type: list
    elements: str
    version_added: "10.7.0"
  lfs:
    description:
      - Enable Git LFS when fetching from a repository.
      - Passed as C(--lfs).
    type: bool
    default: false
    version_added: "10.7.0"
requirements:
  - uv >= 0.4.0
seealso:
  - module: community.general.pipx
notes:
  - This module wraps C(uv tool) subcommands.
  - C(uv tool list) does not emit JSON, so tool metadata is parsed from its text output.
author:
  - Leandro Lemos (@ceso)
"""

EXAMPLES = r"""
- name: Install ruff
  community.general.uv:
    name: ruff

- name: Install ruff pinned to 0.3.0
  community.general.uv:
    name: ruff
    version: "0.3.0"

- name: Install with a version constraint
  community.general.uv:
    name: httpie
    version: ">0.1.0"

- name: Install from a git repository
  community.general.uv:
    name: httpie
    source: "git+https://github.com/httpie/cli"

- name: Install from a git repository at a tag
  community.general.uv:
    name: httpie
    source: "git+https://github.com/httpie/cli"
    version: "3.2.4"

- name: Install from a git repository at a commit
  community.general.uv:
    name: httpie
    source: "git+https://github.com/httpie/cli"
    version: "2843b87"

- name: Install from a git repository on a branch
  community.general.uv:
    name: httpie
    source: "git+https://github.com/httpie/cli"
    version: master

- name: Install from a git repository with LFS
  community.general.uv:
    name: lfs-cowsay
    source: "git+https://github.com/astral-sh/lfs-cowsay"
    lfs: true

- name: Install with a specific Python version
  community.general.uv:
    name: ruff
    python: "3.10"

- name: Upgrade with a specific Python version
  community.general.uv:
    name: ruff
    state: latest
    python: "3.10"

- name: Install mkdocs with extra packages
  community.general.uv:
    name: mkdocs
    with_packages:
      - mkdocs-material

- name: Install ansible with executables from related packages
  community.general.uv:
    name: ansible
    with_executables_from:
      - ansible-core
      - ansible-lint

- name: Force reinstall ruff
  community.general.uv:
    name: ruff
    force: true

- name: Ensure tox is at the latest version
  community.general.uv:
    name: tox
    state: latest

- name: Upgrade ruff
  community.general.uv:
    name: ruff
    state: upgrade

- name: Upgrade all installed tools
  community.general.uv:
    state: upgrade_all

- name: Uninstall pycowsay
  community.general.uv:
    name: pycowsay
    state: absent

- name: Uninstall all tools
  community.general.uv:
    state: uninstall_all

- name: Reinstall all tools
  community.general.uv:
    state: reinstall_all

- name: Manage tools in a loop
  community.general.uv:
    name: "{{ item.name }}"
    state: "{{ item.state | default('present') }}"
    executable: /usr/local/bin/uv
  loop:
    - name: ruff
    - name: black
    - name: mypy
  loop_control:
    label: "{{ item.name }}"
"""

RETURN = r"""
cmd:
  description: Last C(uv) command executed.
  type: list
  elements: str
  returned: always
  sample: ["/usr/bin/uv", "tool", "install", "ruff"]
stdout:
  description: Standard output of the last command.
  type: str
  returned: always
  sample: "Installed 1 executable: ruff"
stderr:
  description: Standard error of the last command.
  type: str
  returned: always
  sample: ""
application:
  description: Installed tools after the operation, keyed by tool name.
  type: dict
  returned: always
  sample:
    ruff:
      name: ruff
      version: "0.3.0"
      commands:
        - ruff
"""

import re

from ansible.module_utils.basic import AnsibleModule


def parse_tool_list(output: str) -> dict[str, dict]:
    """Parse C(uv tool list) text into a dict keyed by tool name."""
    tools: dict[str, dict] = {}
    current: dict | None = None
    for line in output.splitlines():
        match = re.match(r"^(\S+)\s+v(.+?)(?:\s+\(.*\))?\s*$", line)
        if match:
            name = match.group(1)
            version = match.group(2)
            current = {"name": name, "version": version, "commands": []}
            tools[name] = current
        elif current and line.startswith("- "):
            cmd_match = re.match(r"^- (\S+)", line)
            if cmd_match:
                current["commands"].append(cmd_match.group(1))
    return tools


def _get_uv(module: AnsibleModule) -> list[str]:
    """Return the uv command as a list."""
    exe = module.params.get("executable")
    if exe:
        return [exe]
    return [module.get_bin_path("uv", required=True)]


def _get_installed(module: AnsibleModule, uv: list[str]) -> dict[str, dict]:
    """Return a dict of currently installed tools."""
    rc, out, _err = module.run_command(uv + ["tool", "list"])
    if rc != 0:
        return {}
    return parse_tool_list(out)


def _run(module: AnsibleModule, uv: list[str], args: list[str]) -> tuple[list[str], str, str]:
    """Run a uv subcommand, failing the module on non-zero exit."""
    cmd = uv + args
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(
            msg="uv command failed", cmd=cmd, rc=rc, stdout=out, stderr=err
        )
    return cmd, out, err


def _build_package_spec(name: str, source: str | None, version: str | None) -> list[str]:
    """Build the package spec and optional --from flag for uv tool install."""
    if source and version:
        if source.startswith("git+"):
            return ["--from", "{0}@{1}".format(source, version), name]
        return ["--from", "{0}=={1}".format(source, version), name]

    if source:
        return ["--from", source, name]

    if version:
        if version[0] in ("=", ">", "<", "!", "~"):
            return ["--from", "{0}{1}".format(name, version), name]
        return ["--from", "{0}=={1}".format(name, version), name]

    return [name]


def _install_args(module: AnsibleModule) -> list[str]:
    """Build the full argument list for uv tool install."""
    p = module.params
    args = ["tool", "install"]

    if p.get("force"):
        args.append("--force")
    if p.get("reinstall"):
        args.append("--reinstall")
    if p.get("editable"):
        args.append("--editable")
    if p.get("lfs"):
        args.append("--lfs")
    if p.get("python"):
        args.extend(["--python", p["python"]])
    if p.get("index_url"):
        args.extend(["--index-url", p["index_url"]])

    for pkg in p.get("with_packages") or []:
        args.extend(["--with", pkg])

    with_exec = p.get("with_executables_from") or []
    if with_exec:
        args.extend(["--with-executables-from", ",".join(with_exec)])

    args.extend(_build_package_spec(p["name"], p.get("source"), p.get("version")))
    return args


def _upgrade_args(module: AnsibleModule, name: str) -> list[str]:
    """Build the argument list for uv tool upgrade."""
    p = module.params
    args = ["tool", "upgrade"]

    if p.get("python"):
        args.extend(["--python", p["python"]])
    if p.get("index_url"):
        args.extend(["--index-url", p["index_url"]])

    args.append(name)
    return args


# ── state handlers ──────────────────────────────────────────────────────


_StateResult = tuple[bool, list[str] | str, str, str, dict[str, dict]]


def state_present(module: AnsibleModule, uv: list[str]) -> _StateResult:
    name = module.params["name"]
    before = _get_installed(module, uv)

    if (
        name in before
        and not module.params.get("force")
        and not module.params.get("reinstall")
    ):
        return False, uv + ["tool", "install", name], "", "", before

    if module.check_mode:
        return True, uv + ["tool", "install", name], "", "", before

    cmd, out, err = _run(module, uv, _install_args(module))
    after = _get_installed(module, uv)
    changed = (
        before != after or module.params.get("force") or module.params.get("reinstall")
    )
    return changed, cmd, out, err, after


def state_absent(module: AnsibleModule, uv: list[str]) -> _StateResult:
    name = module.params["name"]
    before = _get_installed(module, uv)

    if name not in before:
        return False, uv + ["tool", "uninstall", name], "", "", before

    if module.check_mode:
        return True, uv + ["tool", "uninstall", name], "", "", before

    cmd, out, err = _run(module, uv, ["tool", "uninstall", name])
    after = _get_installed(module, uv)
    return True, cmd, out, err, after


def state_upgrade(module: AnsibleModule, uv: list[str]) -> _StateResult:
    name = module.params["name"]
    before = _get_installed(module, uv)

    if name not in before:
        module.fail_json(msg="Cannot upgrade '{0}': not installed".format(name))

    if module.check_mode:
        return True, uv + ["tool", "upgrade", name], "", "", before

    cmd, out, err = _run(module, uv, _upgrade_args(module, name))
    after = _get_installed(module, uv)
    return before != after, cmd, out, err, after


def state_latest(module: AnsibleModule, uv: list[str]) -> _StateResult:
    name = module.params["name"]
    before = _get_installed(module, uv)

    if name not in before:
        changed, cmd, out, err, after = state_present(module, uv)
        if module.check_mode:
            return True, cmd, out, err, after
        before_upgrade = _get_installed(module, uv)
    else:
        before_upgrade = before
        changed = False
        cmd, out, err = uv + ["tool", "upgrade", name], "", ""

    if module.check_mode:
        return True, uv + ["tool", "upgrade", name], "", "", before

    cmd, out, err = _run(module, uv, _upgrade_args(module, name))
    after = _get_installed(module, uv)
    return changed or before_upgrade != after, cmd, out, err, after


def state_upgrade_all(module: AnsibleModule, uv: list[str]) -> _StateResult:
    before = _get_installed(module, uv)

    if not before:
        return False, uv + ["tool", "upgrade", "--all"], "", "", before

    if module.check_mode:
        return True, uv + ["tool", "upgrade", "--all"], "", "", before

    args = ["tool", "upgrade", "--all"]
    if module.params.get("python"):
        args.extend(["--python", module.params["python"]])

    cmd, out, err = _run(module, uv, args)
    after = _get_installed(module, uv)
    return before != after, cmd, out, err, after


def state_uninstall_all(module: AnsibleModule, uv: list[str]) -> _StateResult:
    before = _get_installed(module, uv)

    if not before:
        return False, uv + ["tool", "uninstall", "--all"], "", "", before

    if module.check_mode:
        return True, uv + ["tool", "uninstall", "--all"], "", "", before

    cmd, out, err = _run(module, uv, ["tool", "uninstall", "--all"])
    after = _get_installed(module, uv)
    return True, cmd, out, err, after


def state_reinstall_all(module: AnsibleModule, uv: list[str]) -> _StateResult:
    before = _get_installed(module, uv)

    if not before:
        return False, uv + ["tool", "install", "--force"], "", "", before

    if module.check_mode:
        return True, uv + ["tool", "install", "--force"], "", "", before

    last_cmd: list[str] = []
    out_parts: list[str] = []
    err_parts: list[str] = []
    for tool_name in before:
        cmd, o, e = _run(module, uv, ["tool", "install", "--force", tool_name])
        last_cmd = cmd
        out_parts.append(o)
        err_parts.append(e)

    after = _get_installed(module, uv)
    return True, last_cmd, "\n".join(out_parts), "\n".join(err_parts), after


# ── dispatch ────────────────────────────────────────────────────────────


STATE_MAP = {
    "present": state_present,
    "install": state_present,
    "absent": state_absent,
    "uninstall": state_absent,
    "latest": state_latest,
    "upgrade": state_upgrade,
    "upgrade_all": state_upgrade_all,
    "uninstall_all": state_uninstall_all,
    "reinstall_all": state_reinstall_all,
}


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type="str",
                default="present",
                choices=list(STATE_MAP.keys()),
            ),
            name=dict(type="str"),
            version=dict(type="str"),
            source=dict(type="str"),
            executable=dict(type="path"),
            python=dict(type="str"),
            index_url=dict(type="str"),
            force=dict(type="bool", default=False),
            editable=dict(type="bool", default=False),
            reinstall=dict(type="bool", default=False),
            with_packages=dict(type="list", elements="str"),
            with_executables_from=dict(type="list", elements="str"),
            lfs=dict(type="bool", default=False),
        ),
        required_if=[
            ("state", "present", ["name"]),
            ("state", "install", ["name"]),
            ("state", "absent", ["name"]),
            ("state", "uninstall", ["name"]),
            ("state", "upgrade", ["name"]),
            ("state", "latest", ["name"]),
        ],
        supports_check_mode=True,
    )

    uv = _get_uv(module)
    state = module.params["state"]

    before = _get_installed(module, uv)
    changed, cmd, out, err, after = STATE_MAP[state](module, uv)

    diff = {}
    if module._diff:
        diff = {"before": before, "after": after}

    module.exit_json(
        changed=changed,
        cmd=cmd,
        stdout=out,
        stderr=err,
        application=after,
        diff=diff,
    )


if __name__ == "__main__":
    main()
