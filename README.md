# ansible-role-packages

Install packages via OS native package manager, Linux Homebrew, Python uv, AppImages and plain binaries

## Table of contents

- [Requirements](#requirements)
- [Default Variables](#default-variables)
  - [__packages_brew_bin](#__packages_brew_bin)
  - [__packages_local_applications](#__packages_local_applications)
  - [__packages_local_bin](#__packages_local_bin)
  - [__packages_local_icons](#__packages_local_icons)
  - [extra_packages_appimage](#extra_packages_appimage)
  - [extra_packages_binary](#extra_packages_binary)
  - [extra_packages_flatpak](#extra_packages_flatpak)
  - [extra_packages_flatpak_remotes](#extra_packages_flatpak_remotes)
  - [extra_packages_homebrew](#extra_packages_homebrew)
  - [extra_packages_homebrew_taps](#extra_packages_homebrew_taps)
  - [extra_packages_native](#extra_packages_native)
  - [extra_packages_native_name_per_distro](#extra_packages_native_name_per_distro)
  - [extra_packages_repos](#extra_packages_repos)
  - [packages_appimage](#packages_appimage)
  - [packages_binary](#packages_binary)
  - [packages_flatpak](#packages_flatpak)
  - [packages_flatpak_remotes](#packages_flatpak_remotes)
  - [packages_homebrew](#packages_homebrew)
  - [packages_homebrew_taps](#packages_homebrew_taps)
  - [packages_native](#packages_native)
  - [packages_native_name_per_distro](#packages_native_name_per_distro)
  - [packages_repos](#packages_repos)
  - [packages_uv](#packages_uv)
- [Discovered Tags](#discovered-tags)
- [Dependencies](#dependencies)
- [License](#license)
- [Author](#author)

---

## Requirements

- Minimum Ansible version: `2.15`

## Default Variables

### __packages_brew_bin

#### Default value

```YAML
__packages_brew_bin: /home/linuxbrew/.linuxbrew/bin
```

### __packages_local_applications

#### Default value

```YAML
__packages_local_applications: "{{ ansible_facts['user_dir'] }}/.local/share/applications"
```

### __packages_local_bin

#### Default value

```YAML
__packages_local_bin: "{{ ansible_facts['user_dir'] }}/.local/bin"
```

### __packages_local_icons

#### Default value

```YAML
__packages_local_icons: "{{ ansible_facts['user_dir'] }}/.local/share/icons"
```

### extra_packages_appimage

Additional AppImage applications appended to the default 'packages_appimage'.

#### Default value

```YAML
extra_packages_appimage: []
```

### extra_packages_binary

Additional direct download apps appended to the default 'packages_binary'.

#### Default value

```YAML
extra_packages_binary: []
```

### extra_packages_flatpak

Additional Flatpak packages appended to the default 'packages_flatpak'.

#### Default value

```YAML
extra_packages_flatpak: []
```

### extra_packages_flatpak_remotes

Additional Flatpak remotes appended to the default 'packages_flatpak_remotes'.

#### Default value

```YAML
extra_packages_flatpak_remotes: []
```

### extra_packages_homebrew

Additional Homebrew packages appended to the default 'packages_homebrew'.

#### Default value

```YAML
extra_packages_homebrew: []
```

### extra_packages_homebrew_taps

Additional Homebrew taps appended to the default 'packages_homebrew_taps'.

#### Default value

```YAML
extra_packages_homebrew_taps: []
```

### extra_packages_native

Additional native packages appended to the default 'packages_native'.

#### Default value

```YAML
extra_packages_native: []
```

### extra_packages_native_name_per_distro

Additional distro-specific package name mappings appended to the default 'packages_native_name_per_distro'.

#### Default value

```YAML
extra_packages_native_name_per_distro: {}
```

### extra_packages_repos

Additional repositories appended to the default 'packages_repos'.

**_Type:_** list[dict]<br />

#### Default value

```YAML
extra_packages_repos: []
```

### packages_appimage

AppImage applications managed by the install_appimage module.
Bundled .desktop files are automatically extracted and symlinked
to ~/.local/share/applications/.

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_appimage:
  - name: appimageupdatetool
    url: 
      https://github.com/AppImageCommunity/AppImageUpdate/releases/download/2.0.0-alpha-1-20251018/appimageupdatetool-x86_64.AppImage
  - name: ghostty
    url: 
      https://github.com/pkgforge-dev/ghostty-appimage/releases/download/v1.3.1/Ghostty-1.3.1-x86_64.AppImage
```

#### Example usage

```YAML
packages_appimage:
  - name: ghostty
    url: "https://github.com/pkgforge-dev/ghostty-appimage/releases/download/v1.3.1/Ghostty-1.3.1-x86_64.AppImage"
```

### packages_binary

Zip/binary applications downloaded and extracted directly.

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_binary: []
```

#### Example usage

```YAML
packages_binary:
  - name: winbox
    url: "https://download.mikrotik.com/routeros/winbox/4.0.1/WinBox_Linux.zip"
    binary: WinBox
    desktop:
      display_name: WinBox
      comment: Configuration tool for RouterOS
      categories: "Network;RemoteAccess;"
```

### packages_flatpak

Packages to be installed via Flatpak.
Each entry accepts name, state (default: present), remote (default: flathub),
and method (default: system). Method controls system or user installation.

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_flatpak: []
```

#### Example usage

```YAML
packages_flatpak:
  - name: com.discordapp.Discord
  - name: org.kde.kate
    method: user
  - name: com.example.OldApp
    state: absent
```

### packages_flatpak_remotes

Flatpak remote repositories to register before installing packages.
Each entry needs a name and a url. Optional method controls system
or user installation (default: system).

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_flatpak_remotes:
  - name: flathub
    url: https://dl.flathub.org/repo/flathub.flatpakrepo
```

#### Example usage

```YAML
packages_flatpak_remotes:
  - name: flathub
    url: "https://dl.flathub.org/repo/flathub.flatpakrepo"
  - name: flathub-beta
    url: "https://dl.flathub.org/beta-repo/flathub-beta.flatpakrepo"
    method: user
```

### packages_homebrew

Packages installed via Homebrew from the default repository.

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_homebrew:
  - name: bat
  - name: fish
  - name: bat-extras
  - name: btop
  - name: entr
  - name: eza
  - name: fd
  - name: fzf
  - name: jq
  - name: kubectx
  - name: prek
  - name: reuse
  - name: ripgrep
  - name: shellcheck
  - name: shfmt
  - name: tre-command
  - name: zellij
  - name: zoxide
  - name: fastfetch
  - name: awscli
  - name: ansible
  - name: ansible-lint
```

#### Example usage

```YAML
packages_homebrew:
  - name: bat
  - name: fzf
```

### packages_homebrew_taps

Third-party Homebrew taps to register before installing packages.
Each entry needs a name (formula) and a tap (repository).

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_homebrew_taps:
  - name: vet-run
    tap: vet-run/vet
```

#### Example usage

```YAML
packages_homebrew_taps:
  - name: vet-run
    tap: vet-run/vet
```

### packages_native

Packages installed via the OS native package manager

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_native:
  - name: unzip
  - name: flatpak
  - name: screen
  - name: brave-browser
  - name: upower
  - name: golang
  - name: neovim
  - name: podman
  - name: vlc
  - name: hexyl
  - name: flameshot
```

### packages_native_name_per_distro

Maps package logical names to their distro-specific package names.
Keys are looked up by the role and resolved to the correct name
for the target OS family.

**_Type:_** dict[string, dict[string, string]]<br />

#### Default value

```YAML
packages_native_name_per_distro:
  fonts-nerd:
    Debian: fonts-jetbrains-mono
    RedHat: jetbrains-mono-fonts-all
    Archlinux: ttf-jetbrains-mono-nerd
  libnotify:
    Debian: libnotify-bin
    RedHat: libnotify
    Archlinux: libnotify
  zim:
    RedHat: Zim
    Debian: zim
  lm_sensors:
    RedHat: lm_sensors
    Debian: lm-sensors
```

#### Example usage

```YAML
packages_native_name_per_distro:
  fonts-nerd:
    Debian: fonts-jetbrains-mono
    RedHat: jetbrains-mono-fonts-all
    Archlinux: ttf-jetbrains-mono-nerd
```

### packages_repos

Extra third party repositories to be added by Linux OS flavour

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_repos:
  - name: brave-browser
    Debian:
      types: [deb]
      uris: https://brave-browser-apt-release.s3.brave.com/
      suites: [stable]
      components: [main]
      signed_by: 
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    RedHat:
      baseurl: https://brave-browser-rpm-release.s3.brave.com/$basearch
      gpgkey: https://brave-browser-rpm-release.s3.brave.com/brave-core.asc
      gpgcheck: true
```

#### Example usage

```YAML
packages_repos:
  - name: mullvad
    Debian:
      types: [deb]
      uris: "https://repository.mullvad.net/deb/stable"
      suites: [stable]
      components: [main]
      signed_by: "https://repository.mullvad.net/deb/mullvad-keyring.asc"
    RedHat:
      baseurl: "https://repository.mullvad.net/rpm/stable/$basearch"
      gpgkey: "https://repository.mullvad.net/rpm/mullvad-keyring.asc"
      gpgcheck: true
```

### packages_uv

Python tools installed via uv in isolated virtual environments.
Each entry accepts name, state, and with_packages keys.

**_Type:_** list[dict]<br />

#### Default value

```YAML
packages_uv:
  - name: molecule
    with_packages:
      - molecule-plugins[podman]
      - molecule-plugins[vagrant]
  - name: ansible-doctor
    with_packages:
      - ansible-core
```

#### Example usage

```YAML
packages_uv:
  - name: molecule
    with_packages:
      - molecule-plugins[podman]
  - name: ruff
```

## Discovered Tags

**_always_**

**_appimage_**

**_binary-app_**

**_flatpak_**

**_homebrew_**

**_os-pkgmanager_**

**_python-uv_**

## Dependencies

None.

## License

MIT

## Author

ceso
