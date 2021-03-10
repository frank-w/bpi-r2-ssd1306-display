# BPI-R2 stats python program for SSD1306 OLED display

## Intro 
The code found in this repo is based on the [stats.py](https://github.com/adafruit/Adafruit_Python_SSD1306/blob/master/examples/stats.py) file
found in Adafruit's Python SSD1306 repo.  It has been customized by xptsp to use Python calls only, thereby freeing it from use of Bash calls.
It has only be tested on a Debian 10 install on the Banana Pi R2, and may require modifications to work on other OSes, kernels, and/or architectures.

## Hardware and Software Used
- [Banana Pi R2](http://www.banana-pi.org/r2.html)
- [Frank-W's kernel 5.10.11](https://github.com/frank-w/BPI-R2-4.14) - branch **5.10-main**
- [Frank-W's Debian 10](https://drive.google.com/file/d/1VbV_IaUy92p1bIrd74sahs77LQNSQEVd/view?usp=sharing)
- [SSD1306 Display](https://www.amazon.com/gp/product/B076PM5ZSJ)

## Expected GPIO configuration
- VCC is on pin 1 (3.3V)
- GND is on pin 9
- SDA on pin 27
- SCL on pin 28

## Display In Action
![](https://github.com/frank-w/bpi-r2-ssd1306-display/blob/master/display_in_action.jpg)

## Script Customization
Inside the `stats.py` script, there are several lines to change.  These lines control which interface each of the 4 icons represent.
```
wan_interface = "wan"
w24_interface = "wlp1s0"
w5G_interface = "wlp1s0"
vpn_interface = "vpn_in"
```
Further modification is planned to modulize the text and images.

## Installation
Install required system packages (root):
```
#python3-pip will recommend many build-tools (cpp,gcc,g++,make,...)
apt install --no-install-recommends i2c-tools python3-pip python3-pil
#if i2c is not available
modprobe i2c-dev
#maybe install i2c-tools and get address
i2cdetect -y -r 2
#it should display your address (mine is 3c)
#register display on i2c-bus
echo "ssd1306 0x3C" > /sys/class/i2c-adapter/i2c-2/new_device
#check rights and add user to group i2c (created by i2c-tools)
ls -l /dev/i2c-*
adduser username i2c
```

Install required Python packages via PIP (user):
```
python3 -m pip install --upgrade pip wheel setuptools
#this will fail if you have not the build.tools installed
python3 -m pip install Adafruit-SSD1306 Adafruit-BBIO psutil
#Adafruit-GPIO Adafruit-PureIO will be installed additionally
```
there are no binary-packages available, but i have precompiled
them (whl) and packed into ssd1306_python3.tar.gz
simply unpack and install it via

```
python3 -m pip install --no-index --find-links=~/whl psutil Adafruit-SSD1306 Adafruit-BBIO
```

Clone the repo, install  and enable the service file:
```
git clone https://github.com/frank-w/bpi-r2-ssd1306-display /opt/stats
cp /opt/stats/stats.service /etc/systemd/system/stats.service
systemctl enable stats
systemctl start stats
```
