# Smart Scale

A raspberry pi script that allows you to track the weight of something in a container (or not) over time.
It makes use of a scale and a RFID reader hooked up to a raspberry pi.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

1) Clone the repository.
2) Install the required packages
	- If on a raspberry pi `pip install -r requirements.txt`
	- else `pip install -r requirements.test.txt`
3) If you have them connect the rfid sensor and scale to your raspberry pi.
	- Scale Documentation: https://tutorials-raspberrypi.com/digital-raspberry-pi-scale-weight-sensor-hx711/
	- Scale Used: https://www.amazon.com/MakerHawk-Converter-Breakout-Portable-Electronic/dp/B07GQPV6C4/ref=sr_1_6
	- RFID Documentation: https://pimylifeup.com/raspberry-pi-rfid-rc522/
	- RFID Used: https://www.amazon.com/gp/product/B076HTH56Q
4) Setup MySQL
	1) Create database
	2) Assign user to database
	3) Create table - ./database/CreateTables.sql
	4) Create a ./database/dbConfig.py file based on the ./database/sample.dbConfig.py file
		- database host
		- user assigned to database
		- user password
		- database name

## Usage
So this is a raspberry pi project that makes uses of a scale and rfid sensor connected to it. However it can be run in
emulated mode on any computer as long as if you can run python and a mysql database. When run in emulated mode it
skips the use of the scale and RFID reader and relies on user input which is makes this program way less cool but
still a way to track a key/value pair (int/float) over time I suppose.

The interfaces for reading the scale and RFID sensor are from open source projects. What this project does is 
utilize the scale, rfid and a MySQL database to track the weight of objects (containers) over time. To run the program
simply run

`python program.py`

You will then be prompted as to if it you are running the program on a raspberry pi with the scale and rfid sensor setup.
If you do not have it setup then it will run in emulate mode.

Regardless of the mode the first thing you will see are all the previous measurements saved in the `Scale` MySQL table.


# You entered 'y'
Sweet you have everything setup! So you will now be prompted to scan your RFID device. So just wave your tag around the reader
until it is picked up. In RFID tags you can save a string, for this project we are using the string as a place to store the weight
of the container that the tag is assigned to. So what we return after reading the tag is the ID and container weight.

Now you place your object or container on the scale to measure it. The scale will takes an average of 10 measurements once the measured
value is over 1 gram three times in a row. That is done because the scale does not stay on 0 exactly so it fluxuates a small amount constantly around 0.


# You entered 'n'
So just testing out the flow of the data to the database. You will be prompted for inputs instead of using the RFID reader and scale.

You will be prompted to:
	- Enter an ID
	- Enter a container weight
	- Enter a weight for the imaginary object

# Calculate, save, and repeat
Once we get an averaged weight (not averaged in emulation) we subtract the container weight from it to get the weight of the contents inside. 

We then compare that weight to what it last was (if it is not a new ID) and then save the new values into the database.

You are then prompted if you want to run it again.


# RFID Folder
The RFID Folder containers 
	- Write.py
	- Read.py

Both of these make use of the `mfrc522` library which does all the magic. I would use Write.py to write the container weight to RFID tags. I should probably
incorporate that process into the program.