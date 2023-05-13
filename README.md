# PyGMC

PyGMC is a Python library for interfacing with the GQ Electronics GMC 500, 500+, 600, and 600+ Geiger-Muller Counters using the device's custom protocol. It implements all documented commands and provides an easy-to-use interface for accessing and updating the device configuration.

## Installation
```bash
pip install pygmc
```

## Usage
```python
from pygmc import GMCConnection, GMCGeigerCounter

# Establish a connection
connection = GMCConnection(port='COM4')

# Create a Geiger counter instance
geiger = GMCGeigerCounter(connection=connection)

# Fetch the current CPM (Counts Per Minute)
cpm = geiger.get_CPM()

# Print the CPM
print(cpm)
```

## Documentation
Detailed documentation for each method is provided in the source code itself. The following are a few key methods and what they do:

* `GMCGeigerCounter.get_CPM()`: Fetches the current CPM (Counts Per Minute) from the device.
* `GMCGeigerCounter.get_battery_voltage()`: Fetches the battery voltage from the device.
* `GMCGeigerCounter.get_config()`: Fetches the current device configuration.
* `GMCGeigerCounter.set_config(config)`: Sets the device configuration. The `config` parameter should be a dictionary matching the structure defined in the `config_format` constant.
* `GMCGeigerCounter.reboot()`: Reboots the device.
* `GMCGeigerCounter.factory_reset()`: Resets the device to factory settings.

You can find the complete list of methods and their description in the `GMCGeigerCounter` class in the code.

## Contributing
We welcome contributions from the community! If you have suggestions for improvements, please open an issue to discuss your ideas or feel free to submit a pull request.
