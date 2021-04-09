#!/usr/bin/python3
###################################################################################
# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###################################################################################

use_img=False
use_img=True

use_disp=False
use_disp=True

import os
import time
import socket
import fcntl
import struct
import psutil
import signal
import sys
#import Adafruit_GPIO.SPI as SPI

if use_disp:
    import Adafruit_SSD1306

if use_img:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont

iconpath = os.path.dirname(os.path.abspath(__file__))
iconwidth = 16

###################################################################################
# Change these variables to reflect which network adapter to use during this check
###################################################################################
wan_interface = "ppp8"
w24_interface = "ap0"
w5G_interface = "wlan1"
vpn_interface = "tun0"
voip_checkscript='/usr/local/bin/check_voip.sh'
conf2g='/etc/hostapd/hostapd_ap0.conf'
conf5g='/etc/hostapd/hostapd_wlan1.conf'

i2cbus=2
disp_w=128
disp_h=64

if use_disp:
    # Initialize library.
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_bus=i2cbus)
    disp.begin()

    # Clear display.
    disp.clear()
    disp.display()

if use_img:
    if use_disp:
        width = disp.width
        height = disp.height
    else:
        width=disp_w
        height=disp_h

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Load default font.
    font = ImageFont.load_default()

    ###################################################################################
    # Load images once into memory:
    ###################################################################################
    globe = Image.open(iconpath+"/"+'earth16w.png').convert('1')
    wifi = Image.open(iconpath+"/"+'wifi16w.png').convert('1')
    phone = Image.open(iconpath+"/"+'phone16w.png').convert('1')
    no_wifi = Image.open(iconpath+"/"+'no16w.png').convert('1')
    vpn   = Image.open(iconpath+"/"+'vpn16w.png').convert('1')

###################################################################################
# Function to get IP address about a specific network adapter:
###################################################################################
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('UTF-8'))
    )[20:24])

def disk_usage(mp='/'):
    mem = psutil.disk_usage(mp)
    total = int(mem.total / 1024 / 1024)
    used = total - int(mem.free / 1024 / 1024)
    percent = int(used / total * 100)
    if used < 10000:
        s1 = "{:4d}M".format(used)
    else:
        s1 = "{:2.1f}G".format(used / 1024)
    if total < 10000:
        s2 = "{:4d}M".format(total)
    else:
        s2 = "{:2.1f}G".format(total / 1024)

    txt="Disk: " + s1 + "/" + s2 + " " + "{:2d}".format(percent) + "%"
    return txt

def convertSeconds(sec):
    days = sec // 86400
    sec -= 86400*days

    hrs = sec // 3600
    sec -= 3600*hrs

    mins = sec // 60
    sec -= 60*mins
    return [days, hrs, mins, sec]

def uptime():
    ut = int(time.time() - psutil.boot_time()) #seconds
    utd=convertSeconds(ut)
    #return "%dd%dh%dm%ds" % tuple(utd)
    return '{}d{}h{}m{}s'.format(*utd)

def isInterfaceUp(ifname):
    try:
        with open("/sys/class/net/" + ifname + "/operstate") as f:
            if f.read().strip() == "down":
                throw
        return True
    except:
        return False

def getTemp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            mdc = f.read().strip()
        return int(mdc) // 1000
    except:
        return "(?)"


import subprocess
def checkvoip():
    completedProc = subprocess.run(voip_checkscript)
    #print(completedProc.stdout,completedProc.stderr)
    return (completedProc.returncode == 0)

def getProcInfo(appname):
    res={}
    for p in psutil.process_iter():
        try:
            #print(p.pid,p.name(),p.cmdline())
            if p.name().startswith(appname):
                res[p.pid]=p.cmdline()
                #print("found: ",p.pid,p.name(),p.cmdline())
        except psutil.NoSuchProcess:
            pass
    return res

###################################################################################
# Our signal handler to clear the screen upon exiting the script:
###################################################################################
def signal_handler(sig, frame):
    #disp.clear()
    #disp.display()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

###################################################################################
# Main loop which shows information about our computer:
###################################################################################
while True:
    temp_txt = str(getTemp())+"°"
    print(temp_txt)
    ###############################################################################
    # Show the globe symbol if the WAN interface up and cable connected.
    ###############################################################################
    wan_txt="WAN: "
    wan_ico=None

    if isInterfaceUp(wan_interface):
        wan_ico=globe
        wan_txt+= get_ip_address(wan_interface)
    else:
        wan_txt+="disconnected"

    print(wan_txt)

    #check for hostapd-processes
    procinfo=getProcInfo("hostapd")
    h2run=False
    h5run=False

    for pid in procinfo:
        if "conf2g" in locals() and conf2g in procinfo[pid]:
#            print(conf2g,"in",pid)
            h2run=True
        if "conf5g" in locals() and conf5g in procinfo[pid]:
#            print(conf5g,"in",pid)
            h5run=True

    ###############################################################################
    # Show the first symbol if the 2.4Ghz wifi interface is up.
    ###############################################################################
    wifi24_txt="2G4: "
    wifi24_ico=None

    if isInterfaceUp(w24_interface) and h2run:
        wifi24_ico=wifi
        wifi24_txt+="up"
    else:
        wifi24_ico=no_wifi
        wifi24_txt+="none"

    print(wifi24_txt)

    ###############################################################################
    # Show the second wifi symbol if the 5Ghz wifi interface is up.
    ###############################################################################
    wifi5_txt="5G: "
    wifi5_ico=None

    if isInterfaceUp(w5G_interface) and h5run:
        wifi5_ico=wifi
        wifi5_txt+="up"
    else:
        wifi5_ico=no_wifi
        wifi5_txt+="none"

    print(wifi5_txt)

    ###############################################################################
    # Show the VPN symbol if the VPN_IN interface is up.
    ###############################################################################
    vpn_ico=None

    if isInterfaceUp(vpn_interface):
        vpn_ico=vpn

    if "voip_checkscript" in locals() and voip_checkscript and checkvoip():
        phone_ico=phone
    else:
        phone_ico=None
    ###############################################################################
    # Write the CPU load values
    ###############################################################################
    load = os.getloadavg()
    load_txt="Load: " + '{:.2f}'.format(load[0]) + "," + '{:.2f}'.format(load[1]) + "," + '{:.2f}'.format(load[2])
    print(load_txt)

    ###############################################################################
    # Write the available and total memory
    ###############################################################################
    mem = psutil.virtual_memory()
    total = int(mem.total / 1024 / 1024)
    used = total - int(mem.available / 1024 / 1024)
    percent = int(used / total * 100)
    if used < 10000:
        s1 = "{:4d}M".format(used)
    else:
        s1 = "{:2.1f}G".format(used / 1024)
    if total < 10000:
        s2 = "{:4d}M".format(total)
    else:
        s2 = "{:2.1f}G".format(total / 1024)
    mem_txt="Mem:  " + s1 + "/" + s2 + " " + "{:2d}".format(percent) + "%"
    print(mem_txt)

    ###############################################################################
    # Write the available and total disk space
    ###############################################################################
    disk_txt = disk_usage()
    print(disk_txt)
    ut=uptime()
    print(ut)
    ###############################################################################
    # Generate image.
    ###############################################################################
    if use_img:
        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        if wan_ico:
           image.paste(wan_ico, ((iconwidth + 2) * 0, 0))
        if wifi24_ico:
            image.paste(wifi24_ico, ((iconwidth + 2) * 1, 0))
        draw.text((iconwidth * 1 + 4, 16), "2G",  font=font, fill=255)
        if wifi5_ico:
            image.paste(wifi5_ico, ((iconwidth + 2) * 2, 0))
        draw.text((iconwidth * 2 + 6, 16), "5G",  font=font, fill=255)
        if phone_ico:
            image.paste(phone_ico, ((iconwidth + 2) * 3, 0))

        draw.text((0,16), temp_txt,  font=font, fill=255)
        draw.text((iconwidth * 3 + 6, 16), ut,  font=font, fill=255)

        if iconwidth < 24: #128/5=~25;-2=23
            if vpn_ico:
                image.paste(vpn_ico, ((iconwidth + 2) * 4, 0))
        if iconwidth < 20: #128/6=~21;-2=19
            if vpn_ico:
                image.paste(vpn_ico, ((iconwidth + 2) * 4, 0))

        draw.text((0, 30), wan_txt,  font=font, fill=255)
        draw.text((0, 38), load_txt,  font=font, fill=255)
        draw.text((0, 46), mem_txt, font=font, fill=255)
        draw.text((0, 54), disk_txt, font=font, fill=255)
        if use_disp:
            ###############################################################################
            # Display image.
            ###############################################################################
            disp.image(image)
            disp.display()
        else:
            image.save('/home/frank/stats.png')
    time.sleep(15)
