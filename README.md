# HF APRS on a Raspberry Pi
This isn't a guide, this is me documenting what I have done for me.

## Initial Setup

### Operating System Version

* Raspberry Pi OS Lite (64 Bit)

```bash
cat /etc/os-release

PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

```bash
uname -a

Linux piprs 6.1.0-rpi4-rpi-v8 #1 SMP PREEMPT Debian 1:6.1.54-1+rpt2 (2023-10-05) aarch64 GNU/Linux
```

### Update and Upgrade

```bash
sudo apt update
sudo apt upgrade
```

## Install Hamlib

### Install dependencies

```bash
sudo apt install automake libtool texinfo
```

### Clone and compile

```bash
cd ~
git clone https://github.com/Hamlib/Hamlib
cd Hamlib
git checkout Hamlib-4.5.5
./bootstrap
./configure --prefix=/usr
make
make check
sudo make install
```

## Install GPSd

Note: apt will install 3.22 which has issues with some GPS receivers not updating after first fix. I opted to install from apt to setup the GPSd system service and then compile from source and replace the binary. A bit hacky but it works.

```bash
sudo apt install gpsd
sudo apt install libgps-dev scons libncurses-dev python3 pps-tools git-core asciidoctor python3-matplotlib build-essential manpages-dev pkg-config python3-distutils
wget https://download-mirror.savannah.gnu.org/releases/gpsd/gpsd-3.25.tar.gz
tar -xzf gpsd-3.25.tar.gz
cd gpsd-3.25/

sudo systemctl stop gpsd
sudo scons prefix=/usr
sudo scons install
```

## Install Direwolf

### Install dependencies

```bash
sudo apt install git gcc g++ make cmake libasound2-dev libudev-dev libavahi-client-dev
```

### Clone and compile

```bash
cd ~
git clone https://www.github.com/wb2osz/direwolf
cd direwolf
git checkout dev
rm -rf build
mkdir build && cd build
cmake -DUNITTEST=1 ..
make -j4
make test
sudo make install
make install-conf
```

### Setup

#### Find audio device

```bash
aplay -l

**** List of PLAYBACK Hardware Devices ****
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

```bash
arecord -l

**** List of CAPTURE Hardware Devices ****
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```


#### Configuration

```bash
sudo nano /etc/direwolf.conf
```

##### direwolf.conf

```
ADEVICE plughw:1,0

ACHANNELS 1
CHANNEL 0

MYCALL N0CALL

MODEM 300 1600:1800 7@30 E /4

PTT RIG 1036 /dev/ttyUSB0 38400

GPSD
TBEACON DELAY=0:15 EVERY=10:00 VIA=WIDE1-1,WIDE2-1 SYMBOL=car

#CBEACON DELAY=0:00 EVERY=0:10 INFO="N0CALL TEST"

KISSPORT 8001
```

#### Add direwolf user
```bash
sudo useradd direwolf
sudo usermod -a -G audio direwolf
```

#### Register as service

```bash
sudo nano /lib/systemd/system/direwolf.service
```

##### direwolf.service
```
[Unit]
Description=DireWolf is a software "soundcard" modem/TNC and APRS decoder
Documentation=man:direwolf
AssertPathExists=/etc/direwolf.conf

[Service]
User=direwolf
SupplementaryGroups=dialout audio
ExecStartPre=/bin/sleep 30
ExecStart=/usr/local/bin/direwolf -c /etc/direwolf.conf
StandardOutput=append:/var/log/direwolf.log
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

#### Configure to run on startup

```bash
sudo systemctl daemon-reload
sudo systemctl enable direwolf.service
sudo systemctl start direwolf.service
```

## Install PyPRS
### Create APRS user
```bash
sudo adduser aprs
sudo usermod -a -G audio aprs
sudo usermod -a -G aprs user
```

### Install dependencies
```bash
sudo apt install python3-venv
```

### Setup PyPRS
```bash
su aprs
cd ~
git clone https://github.com/tom-acco/PyPRS.git
cd PyPRS
chmod +x setup.sh
./setup.sh
exit
```

### Start on login
```bash
sudo nano /home/aprs/.bashrc
```

Add to the bottom
```bash
echo Starting APRS display
cd ~/PyPRS
source .venv/bin/activate
python main.py
```

## Setup Access Point
### Create AP
```bash
sudo nmcli con add type wifi ifname wlan0 mode ap con-name PIPRS-AP ssid PIPRS autoconnect false
sudo nmcli con modify PIPRS-AP wifi.band bg
sudo nmcli con modify PIPRS-AP wifi.channel 3
sudo nmcli con modify PIPRS-AP wifi.cloned-mac-address 00:12:34:56:78:9a
sudo nmcli con modify PIPRS-AP wifi-sec.key-mgmt wpa-psk
sudo nmcli con modify PIPRS-AP wifi-sec.proto rsn
sudo nmcli con modify PIPRS-AP wifi-sec.group ccmp
sudo nmcli con modify PIPRS-AP wifi-sec.pairwise ccmp
sudo nmcli con modify PIPRS-AP wifi-sec.psk "piprs12345"
sudo nmcli con modify PIPRS-AP ipv4.method shared ipv4.address 192.168.110.1/24
sudo nmcli con modify PIPRS-AP ipv6.method disabled
```
### Start AP
```bash
sudo nmcli con up PIPRS-AP
```

### Stop the AP (will become a WiFi client again)
```bash
sudo nmcli con down PIPRS-AP
```

### Start AP on startup

```bash
sudo nano /etc/rc.local
```

##### Add before exit 0
```bash
nmcli con up PIPRS-AP
```
