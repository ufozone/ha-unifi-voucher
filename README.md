# UniFi Hotspot Manager

[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]
[![GitHub Activity][commits-shield]][commits]

[![hacs][hacsbadge]][hacs]
[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

[![GitHub Release][release-shield]][releases]
[![issues][issues-shield]][issues-link]
[![release-badge]][release-workflow]
[![validate-badge]][validate-workflow]
[![lint-badge]][lint-workflow]

UniFi Hotspot Manager as a Custom Component for Home Assistant.

This integration facilitates user-friendly management of guest Wi-Fi vouchers. By integrating with Home Assistant, users can swiftly and easily generate and display personalized access codes. These vouchers can then be shared with guests, granting temporary access to the Wi-Fi network.

Key features of the integration include:

* **Voucher Creation:** Users can effortlessly generate new access codes, with various configuration options such as validity period and available data volume.
* **Display of Voucher:** The last created voucher is presented in the Home Assistant interface. As soon as the voucher has been used, the next one will be displayed.
* **QR Code Display:** The integration enables the display of a QR code for the guest Wi-Fi, facilitating quick connectivity for guests.
* **Automation:** The integration can be integrated into existing automations and allows, for example, the time-controlled creation of vouchers.
* **User-Friendliness:** The integration is designed to offer an intuitive user experience, utilizing the Home Assistant interface as a central control center for guest Wi-Fi management.

The UniFi Hotspot Manager Integration provides a practical solution for the temporary provision of Wi-Fi access, seamlessly integrating into the Home Assistant environment for intuitive use.

The most UniFi Network Controller by Ubiquiti Networks, inc., e.g. Cloud Key 2, UDM, UDM Pro are supported.

## Example of use

The voucher can be presented together with the QR code on a lovelace card:

![Lovelace Card](https://github.com/ufozone/ha-unifi-voucher/blob/main/screenshots/lovelace-card.jpg?raw=true)

<details>
  <summary>Blueprint of the example</summary>
  The example shown can be implemented as follows. The image file for the background must be stored in the `/config/www/` folder.

  ```yaml
  type: picture-elements
  image: /local/hotspot-bg.jpg
  elements:
    - type: state-label
      entity: image.123456789073fdb051c706194_qr_code
      attribute: wlan_name
      style:
        top: 15%
        left: 50%
        color: white
        font-size: 200%
        font-weight: bold
        cursor: default
      tap_action:
        action: none
      hold_action:
        action: none
    - type: image
      entity: image.123456789073fdb051c706194_qr_code
      style:
        top: 53%
        left: 20%
        width: 30%
        cursor: default
    - type: state-label
      entity: sensor.123456789073fdb051c706194_voucher
      style:
        top: 53%
        left: 67%
        background: rgba(11, 11, 11, 70%)
        padding: 10px
        height: 60px
        color: white
        border-radius: 12px
        font-size: 275%
        font-weight: bold
        cursor: default
      tap_action:
        action: none
      hold_action:
        action: none
    - type: state-label
      entity: sensor.123456789073fdb051c706194_voucher
      attribute: duration
      prefix: 'Duration: '
      style:
        top: 61%
        left: 67%
        color: white
        cursor: default
      tap_action:
        action: none
      hold_action:
        action: none
    - type: service-button
      title: Refresh
      style:
        transform: none
        bottom: 5%
        left: 5%
      service: button.press
      service_data:
        entity_id: button.123456789073fdb051c706194_update
    - type: service-button
      title: Create
      style:
        transform: none
        bottom: 5%
        right: 5%
      service: button.press
      service_data:
        entity_id: button.123456789073fdb051c706194_create
  ```

</details>

## Installation

Requires Home Assistant 2023.11.0 or newer.

### Installation through HACS

Installation using Home Assistant Community Store (HACS) is recommended.

1. If HACS is not installed, follow HACS installation and configuration at <https://hacs.xyz/>.

2. Click the button below or visit the HACS _Integrations_ pane and search for "UniFi Hotspot Manager".

    [![my_button](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ufozone&repository=ha-unifi-voucher&category=integration)

3. Install the integration.

4. Restart Home Assistant!

5. Make sure that you refresh your browser window too.

### Manual installation

1. Download the `unifi_voucher.zip` file from the repository [release section](https://github.com/ufozone/ha-unifi-voucher/releases).

   Do **not** download directly from the `main` branch.

2. Extract and copy the content into the path `/config/custom_components/unifi_voucher` of your HA installation.

3. Restart Home Assistant!

4. Make sure that you refresh your browser window too.

### Setup integration

Start setup:

* Click this button:

    [![my_button](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=unifi_voucher)

* Or use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "UniFi Hotspot Manager".

## Configuration

* All configuration options are offered from the front end.
* For UniFi OS a local-only user needs to be created. A user who uses the Ubiquiti cloud will not work.
* The user needs super admin, site admin or hotspot privileges in order to manage guest vouchers.

## Available components

### Buttons

* create

  Attributes:

  ```text
  last_poll
  ```

* delete

  Attributes:

  ```text
  last_poll
  ```

* update

  Attributes:

  ```text
  last_poll
  ```

### Images

_This entity is disabled by default. You have to activate it if you want to use it._

* qr_code

  Attributes:

  ```text
  wlan_name, last_poll
  ```

### Numbers

_These entities are disabled by default. You have to activate it if you want to use it._

* voucher_quota

  Attributes:

  ```text
  last_poll
  ```

* voucher_duration

  Attributes:

  ```text
  last_poll
  ```

* voucher_usage_quota

  Attributes:

  ```text
  last_poll
  ```

* voucher_rate_max_up

  Attributes:

  ```text
  last_poll
  ```

* voucher_rate_max_down

  Attributes:

  ```text
  last_poll
  ```

### Sensors

* voucher

  Attributes:

  ```text
  wlan_name, id, quota, used, duration, status, create_time, start_time, end_time, status_expires, usage_quota, rate_max_up, rate_max_down, last_poll
  ```

### Services

* `unifi_voucher.list`:

    Get a list of all valid vouchers.

* `unifi_voucher.create`:

    Create a new voucher with your own parameters or the default settings of the integration.

* `unifi_voucher.delete`:

    Delete a special voucher or the last created voucher.

* `unifi_voucher.update`:

    Fetch data from UniFi Controller immediately.

## Debugging

To enable debug logging for this integration you can control this in your Home Assistant `configuration.yaml` file.

Set the logging to debug with the following settings in case of problems:

```yaml
logger:
  default: warn
  logs:
    aiounifi: debug
    custom_components.unifi_voucher: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.

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

[releases]: https://github.com/ufozone/ha-unifi-voucher/releases
[release-shield]: https://img.shields.io/github/v/release/ufozone/ha-unifi-voucher?style=flat

[issues-shield]: https://img.shields.io/github/issues/ufozone/ha-unifi-voucher?style=flat
[issues-link]: https://github.com/ufozone/ha-unifi-voucher/issues

[lint-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/lint.yaml/badge.svg
[lint-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/lint.yaml
[validate-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/validate.yaml/badge.svg
[validate-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/validate.yaml
[release-badge]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/release.yaml/badge.svg
[release-workflow]: https://github.com/ufozone/ha-unifi-voucher/actions/workflows/release.yaml
