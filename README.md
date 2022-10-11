# solax-x3

<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />

<h3 align="center">Solax X3</h3>

  <p align="center">
    A module to read from the solar inverter Solax X3's registers via its modbus interface (RS-485).
    <br />


<!-- TABLE OF CONTENTS -->
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>



<!-- ABOUT THE PROJECT -->
## About The Project


<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- GETTING STARTED -->
## Getting Started

This is module is build on top of pymodbus and add specifics to the work with Solax X3 inverter via its RTU interface.

### Prerequisites

* Solax X3 inverter
* Modbus RS-485 serial adapter/interface
* Modbus cable
* Install this python module

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/mkfam7/solax-x3.git
   ```
2. Install python packages
   ```sh
   pip pymodbus install solax-x3
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

```
from pymodbus.client.sync import ModbusSerialClient
from solaxx3.rs485 import SolaxX3


s = SolaxX3(port="/dev/ttyUSB0", baudrate=115200)


if s.connect():
    s.read_all_registers()
    print(f"Battery temperature: {s.read('temperature_battery')}")
else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()

```

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/mkfam7/solax-x3](https://github.com/mkfam7/solax-x3)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>

