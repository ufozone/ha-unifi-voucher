# UniFi Hotspot Manager
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]
[![GitHub Activity][commits-shield]][commits]

[![hacs][hacsbadge]][hacs]
[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

Stable -
[![GitHub Release][stable-release-shield]][releases]
[![release-badge]][release-workflow]

Latest -
[![GitHub Release][latest-release-shield]][releases]
[![validate-badge]][validate-workflow]
[![lint-badge]][lint-workflow]
[![issues][issues-shield]][issues-link]

UniFi Hotspot Manager as a Custom Component for Home Assistant. The most UniFi Network Controller by Ubiquiti Networks, inc., e.g. Cloud Key 2, UDM, UDM Pro are supported.

## Installation
* First: This is not a Home Assistant Add-On. It's a custom component.
* There are three ways to install:
    * First you can download the folder custom_component and copy it into your Home-Assistant config folder.
    * Second option is to install HACS (Home Assistant Custom Component Store) and visit the HACS _Integrations_ pane and add `https://github.com/ufozone/ha-unifi-voucher.git` as an `Integration` by following [these instructions](https://hacs.xyz/docs/faq/custom_repositories/). You'll then be able to install it through the _Integrations_ pane.
    * ~~Third option is to install HACS (Home Assistant Custom Component Store) and select "UniFi Hotspot Managervoucher" from the Integrations catalog.~~
* Restart Home Assistant after installation.
* Make sure that you refresh your browser window too.
* Use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "UniFi Hotspot Managervoucher".

## Configuration
* All configuration options are offered from the front end.
* For UniFi OS a local-only user needs to be created. A user who uses the Ubiquiti cloud will not work.
* The user needs administrator or hotspot privileges in order to manage guest vouchers.

## Available components 

### Binary Sensors

coming soon...

### Buttons

coming soon...

### Sensors

coming soon...

### Services

coming soon...

### Logging

Set the logging to debug with the following settings in case of problems.

```
logger:
  default: warn
  logs:
    aiounifi: debug
    custom_components.unifi_voucher: debug
```


***

[commits-shield]: https://img.shields.io/github/commit-activity/y/ufozone/ha-unifi-voucher?style=for-the-badge
[commits]: https://github.com/ufozone/ha-unifi-voucher/commits/main
[license-shield]: https://img.shields.io/github/license/ufozone/ha-unifi-voucher.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-ufozone-blue.svg?style=for-the-badge

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/

[issues-shield]: https://img.shields.io/github/issues/ufozone/ha-unifi-voucher?style=flat
[issues-link]: https://github.com/ufozone/ha-unifi-voucher/issues

[releases]: https://github.com/ufozone/ha-unifi-voucher/releases
[stable-release-shield]: https://img.shields.io/github/v/release/ufozone/ha-unifi-voucher?style=flat
[latest-release-shield]: https://img.shields.io/github/v/release/ufozone/ha-unifi-voucher?include_prereleases&style=flat

[lint-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/lint.yaml/badge.svg
[lint-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/lint.yaml
[validate-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/validate.yaml/badge.svg
[validate-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/validate.yaml
[release-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/release.yaml/badge.svg
[release-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/release.yaml
