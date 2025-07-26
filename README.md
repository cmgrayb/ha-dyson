# Home Assistant Integration for Wi-Fi Connected Dyson Devices

This is a Home Assistant custom integration for Wi-Fi connected Dyson devices, and is being actively developed. It replaces the Dyson Local and Dyson Cloud integrations by shenxn, which are no longer maintained.

**� Platinum Ready**: This integration is prepared for Platinum status by migrating from vendored dependencies to using the external [`libdyson-neon`](https://pypi.org/project/libdyson-neon/) package, meeting Home Assistant Core integration requirements.

[![GitHub (Pre-)Release Date](https://img.shields.io/github/release-date-pre/libdyson-wg/ha-dyson)](https://github.com/libdyson-wg/ha-dyson/releases/)
[![Latest Release](https://badgen.net/github/release/libdyson-wg/ha-dyson)](https://github.com/libdyson-wg/ha-dyson/releases/)
[![validate](https://badgen.net/github/checks/libdyson-wg/ha-dyson/main/validate)](https://github.com/libdyson-wg/ha-dyson/actions/workflows/hassfest.yaml)
[![HACS Action](https://badgen.net/github/checks/libdyson-wg/ha-dyson/main/HACS%20Action)](https://github.com/libdyson-wg/ha-dyson/actions/workflows/hacs.yaml)
[![Latest Commit](https://badgen.net/github/last-commit/libdyson-wg/ha-dyson/main)](https://github.com/libdyson-wg/ha-dyson/commit/HEAD)

## What's New - Platinum Readiness

### 🎯 External Dependencies

This integration now uses the external [`libdyson-neon`](https://pypi.org/project/libdyson-neon/) package instead of vendored code, preparing it for **Platinum status** and Home Assistant Core integration standards.

### 🔧 Key Improvements

- **Clean Architecture**: Removed all vendored dependencies
- **Better Maintenance**: Easier updates through external package management
- **Core Integration Ready**: Meets all Home Assistant Core requirements for Platinum status
- **Static Typing**: Full type annotations throughout the codebase
- **Quality Assurance**: Comprehensive linting, formatting, and testing

### 🚀 Migration Notes

If you're upgrading from a previous version, the integration will automatically use the new external dependency. No user action required - your devices and configuration will continue to work seamlessly.

## Troubleshooting

### Fan connection failures

Please try power-cycling the fan device and try connecting again.

Dyson fans run an MQTT Broker which this integration connects to as a client. The broker has a connection limit and some devices appear to have a firmware bug where they hold onto dead connections and fill up the connection pool, causing new connections to fail. This behavior has been observed on the following device models, but may also include others:

- TP07 Purifier Cool
- TP09 Purifier Cool Formaldehyde
- HP07 Purifier Hot+Cool
- HP09 Purifier Hot+Cool Formaldehyde

### Authentication Issues

If you experience authentication failures:

1. **Power cycle your device** - Unplug for 10 seconds and reconnect
2. **Check WiFi connection** - Ensure device is connected to your network
3. **Verify credentials** - Re-run the setup flow if needed
4. **Cloud authentication** - For cloud-connected devices, check your Dyson account status

### Device Discovery Problems

If devices aren't being discovered:

1. **Enable auto-discovery** in integration options
2. **Check network** - Ensure Home Assistant and device are on same network
3. **Firewall settings** - Allow MQTT traffic (port 1883)
4. **Device compatibility** - Verify your model is supported (see list below)

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=libdyson-wg&repository=ha-dyson&category=integration)

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Search for "Dyson Local"
3. Install the integration
4. Restart Home Assistant
5. Add the integration through Settings → Devices & Services

### Manual Installation

You can also install manually by copying the `custom_components` from this repository into your Home Assistant installation:

1. Download the latest release
2. Extract to `custom_components/dyson_local/`
3. Restart Home Assistant
4. Add the integration through Settings → Devices & Services

## Configuration

### Local Device Setup

1. Go to Settings → Devices & Services
2. Click "Add Integration" and search for "Dyson Local"
3. Choose "Set up a new device manually"
4. Enter your device credentials:
   - **Serial Number**: Found on device label or in Dyson app
   - **Credential**: Device password (usually on device label)
   - **Device Type**: Select your model from the dropdown

### Cloud Account Setup (Optional)

For automatic device discovery and cloud features:

1. Choose "Sign in with Dyson account" during setup
2. Enter your Dyson app credentials
3. Select your region (Global or China)
4. The integration will automatically discover and set up your devices

### Configuration Options

#### Device Options

- **Enable Polling**: Enable environmental data polling (default: enabled)
- **Static Host**: Set a fixed IP address for the device (optional)

#### Cloud Options

- **Auto Discovery**: Automatically discover new devices (default: enabled)
- **Cloud Poll Interval**: How often to check for new devices (default: 3600 seconds)

## Dyson Devices Supported

This integration uses MQTT-based protocol to communicate with Dyson devices. Only WiFi enabled models have this capability. Currently the following models are supported, and support for more models can be added on request.

### Air Purifiers & Fans

- Dyson Pure Cool
- Dyson Purifier Cool
- Dyson Purifier Cool Formaldehyde
- Dyson Pure Cool Desk
- Dyson Pure Cool Link
- Dyson Pure Cool Link Desk
- Dyson Pure Hot+Cool
- Dyson Pure Hot+Cool Link
- Dyson Purifier Hot+Cool
- Dyson Purifier Hot+Cool Formaldehyde

### Humidifiers

- Dyson Pure Humidity+Cool
- Dyson Purifier Humidity+Cool
- Dyson Purifier Humidity+Cool Formaldehyde

### Large Room Purifiers

- Dyson Purifier Big+Quiet
- Dyson Purifier Big+Quiet Formaldehyde

### Robot Vacuums

- Dyson 360 Eye robot vacuum
- Dyson 360 Heurist robot vacuum
- Dyson 360 Vis Nav robot vacuum

## Features

### Available Entities

Each supported device provides different entities based on its capabilities:

#### Air Quality Sensors

- PM2.5, PM10 particle levels
- Volatile Organic Compounds (VOC)
- Nitrogen Dioxide (NO2)
- Formaldehyde (HCHO) - on supported models
- Air Quality Index (AQI)

#### Environmental Sensors

- Temperature
- Humidity
- Filter life remaining
- Carbon filter life (where applicable)
- HEPA filter life

#### Controls

- Fan speed control
- Oscillation toggle
- Timer controls
- Air quality targets
- Night mode
- Continuous monitoring

#### Climate Controls (Hot+Cool models)

- Heating/cooling modes
- Target temperature
- Auto mode

#### Humidifier Controls (Humidity+Cool models)

- Humidification toggle
- Target humidity level
- Water level monitoring

#### Vacuum Controls (Robot models)

- Start/stop/pause cleaning
- Return to dock
- Cleaning mode selection
- Battery level
- Cleaning maps (where supported)

## Development

### Prerequisites

- Python 3.11+
- Home Assistant development environment
- [`libdyson-neon`](https://pypi.org/project/libdyson-neon/) package

### Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/libdyson-wg/ha-dyson.git
   cd ha-dyson
   ```

2. **Install development dependencies**:

   ```bash
   pip install -r requirements_dev.txt
   ```

3. **Install pre-commit hooks**:

   ```bash
   pre-commit install
   ```

4. **Run quality checks**:

   ```bash
   # All checks
   flake8 custom_components/dyson_local/
   black custom_components/dyson_local/
   isort custom_components/dyson_local/
   mypy custom_components/dyson_local/
   bandit -r custom_components/dyson_local/

   # Or run all at once
   pre-commit run --all-files
   ```

5. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

### Architecture

The integration follows Home Assistant best practices:

- **External Dependencies**: Uses `libdyson-neon` package for device communication
- **Config Flow**: Modern configuration with automatic discovery
- **Coordinators**: Efficient data updates with proper error handling
- **Static Typing**: Full type annotations for better code quality
- **Async/Await**: Non-blocking operations throughout

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Ensure all quality checks pass
5. Submit a pull request

For major changes, please open an issue first to discuss the proposed changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/libdyson-wg/ha-dyson/issues)
- **Discussions**: [GitHub Discussions](https://github.com/libdyson-wg/ha-dyson/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/libdyson-wg/ha-dyson/wiki)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to [shenxn](https://github.com/shenxn) for the original Dyson integrations
- The [`libdyson-neon`](https://github.com/libdyson-wg/libdyson-neon) library maintainers
- The Home Assistant community for their support and feedback
