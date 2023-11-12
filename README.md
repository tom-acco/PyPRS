# HF APRS on a Raspberry Pi
This isn't a guide, this is me documenting what I have done for me.

## Initial Setup

### Operating System Version

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
./bootstrap
./configure --prefix=/usr
make
make check
sudo make install
```

## Install GPS Daemon

```bash
sudo apt install gpsd libgps-dev
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