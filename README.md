** VIRTUAPLANT IS NO LONGER MAINTAINED. THERE ARE SECURITY VULNERABILITIES IN THE `twisted` AND `pycrypto` VERSIONS ON THIS PROJECT. ALSO, THE CODE SEEMS TO BE BROKEN SINCE `pymodbus` WAS UPDATED**

# VirtuaPlant

VirtuaPlant is a Industrial Control Systems simulator which adds a “similar to real-world control logic” to the basic “read/write tags” feature of most PLC simulators. Paired with a game library and 2d physics engine, VirtuaPlant is able to present a GUI simulating the “world view” behind the control system allowing the user to have a vision of the would-be actions behind the control systems.

All the software is written in (guess what?) Python. The idea is for VirtuaPlant to be a collection of different plant types using different protocols in order to be a learning platform and testbed.

The first release introduces a as-simple-as-it-can-get one-process “bottle-filling factory” running Modbus as its protocol.

## Components
### World View

![World View](http://wroot.org/wp/wp-content/uploads/2015/03/worldview.png)

World View consits on the game and 2d physics engine, simulating the effects of the control systems’ action on virtual (cyberz!) assets.

It uses python’s pygame and pymunk (Chipmunk engine for python — intended to be replaced by pybox2d due the lack of swept collision handling which currently limits us a little).

### PLC controller

The soft-plc is implemented over the pymodbus library which runs on a separate thread in the World View component and shares its context (i.e. Registers/Inputs/Tags) with the World View functions in order to simulate assets being “plugged in” to the controller.

### HMI

![HMI](http://wroot.org/wp/wp-content/uploads/2015/03/hmi.png)

The HMI is written using GTK3 and is quite dead simple. Also runs pymodbus client on a separate thread and connects over TCP/IP to the server (so it could be technically on a separate machine), constantly polling (i.e. reading) the server’s (soft PLC in World View) tags. Control is also possible by writing in the soft-PLC tags.

### Attack scripts

![Attack all the things](http://wroot.org/wp/wp-content/uploads/2015/03/spill.png)

You didn’t thought I was leaving this behind, did you? The phun on having a World View is to see the results when you start messing around with the soft-PLCs tags! Some pre-built scripts for determined actions are available so you can unleash the script-kiddie on yourself and make the plant go nuts! YAY!

Check the [demo on YouTube](https://www.youtube.com/watch?v=kAfV8acCwfw)

## Installation requirements

The following packages are required:

* PyGame
* PyMunk
* PyModbus (requires pycrypto, pyasn1)
* PyGObject / GTK

On debian-based systems (like Ubuntu) you can apt-get the packages which are not provided over pip:

    apt-get install python-pygame python-gobject python-pip python-dev

Then install the pip ones:

    pip install pymunk
    pip install pymodbus
    pip install pyasn1
    pip install pycrypto

or install all of the pip packages by using our provided requirement.txt file:

    pip install < requirements.txt


## Running

Enter the `/plants` directory, select the plant you want (currently only one available) and start both the world simulator and the HMI with the `start.sh` script. Parts can be ran individually by running `world.py` and `hmi.py` (self-explanatory). All the attack scripts are under the `/attacks` subdirectory.

## Future
### The following plant scenarios are being considered:

* Oil Refinery Boiler
* Nuclear Power Plant Reactor
* Steel Plant Furnace

### The following protocols are being considered:
* DNP3 (based on OpenDNP3)
* S7
