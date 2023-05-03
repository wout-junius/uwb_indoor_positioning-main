
<div  align="center">

# UWB Indoor Positioning

<a href="https://www.espressif.com/en/products/socs/esp32" ><img alt="Python"  src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white" /></a>
<a href="https://www.espressif.com/en/products/socs/esp32" ><img alt="Python"  src="https://img.shields.io/badge/Arduino-00979D?style=for-the-badge&logo=Arduino&logoColor=white" /></a>

<a href="https://www.espressif.com/en/products/socs/esp32" ><img alt="Esp 32s"  src="https://img.shields.io/badge/ESP%2032-000000?style=for-the-badge&logo=ESPHome&logoColor=white" /></a>

</div>

## Description



## Structure

```js
├───example
│   ├───anchor//=> Code for the anchor ESP32
│   ├───IndoorPositioning
│   │   └───udp_uwb_tag //=> Code for the tag ESP32 using wifi as transmittor
│   │   └───uwb_position_display.py //=> Python server to calculate and visulise the position
│   ├───tag //=> Code for the tag ESP32 using serial
├───hardware
└─── DW1000.zip //=> Edited version of the DW1000 lib
```

## How to run

### Python

To run its simply running the script

`python .\example\IndoorPositioning\uwb_position_display.py` 