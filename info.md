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

UniFi Hotspot Manager as a Custom Component for Home Assistant.

This integration facilitates user-friendly management of guest Wi-Fi vouchers. By integrating with Home Assistant, users can swiftly and easily generate and display personalized access codes. These vouchers can then be shared with guests, granting temporary access to the Wi-Fi network.

Key features of the integration include:
* **Voucher Creation:** Users can effortlessly generate new access codes, with various configuration options such as validity period and available data volume.
* **Display of Voucher:** The last created voucher is presented in the Home Assistant interface.
* **QR Code Display:** The integration enables the display of a QR code for the guest Wi-Fi, facilitating quick connectivity for guests.
* **Automation:** The integration can be incorporated into existing automations, enabling, for instance, time-triggered voucher creation.
* **User-Friendliness:** The integration is designed to offer an intuitive user experience, utilizing the Home Assistant interface as a central control center for guest Wi-Fi management.

The UniFi Hotspot Manager Integration provides a practical solution for the temporary provision of Wi-Fi access, seamlessly integrating into the Home Assistant environment for intuitive use.

The most UniFi Network Controller by Ubiquiti Networks, inc., e.g. Cloud Key 2, UDM, UDM Pro are supported.

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

### Buttons

* update

    ```
    attributes: 
    last_poll
    ```

* create

    ```
    attributes: 
    last_poll
    ```

* remove

    ```
    attributes: 
    last_poll
    ```

### Images

* qr_code

    ```
    attributes: 
    wlan_name, last_poll
    ```

### Numbers

* voucher_quota

    ```
    attributes: 
    last_poll
    ```

* voucher_expire

    ```
    attributes: 
    last_poll
    ```

### Sensors

* voucher

    ```
    attributes: 
    quota, used, duration, status, create_time, start_time, end_time, status_expires, last_poll
    ```

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
