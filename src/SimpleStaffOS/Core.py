import json
import time
import datetime
from adafruit_extended_bus import ExtendedI2C as I2CEnhanced
import board
import neopixel
import digitalio
import adafruit_ssd1306
from adafruit_seesaw.seesaw import Seesaw
from PIL import Image, ImageDraw, ImageFont
from adafruit_seesaw.digitalio import DigitalIO
from pathlib import Path
import subprocess
import os
from pygame import mixer
import adafruit_max1704x

#region Setup audio
try:
    mixer.init()
    takeImageSound = mixer.Sound("Resources/CaptureImage.mp3")
except:
    print("Audio initialization failed.")
    audioSystem = False
#endregion

pathToSettings = os.path.dirname(__file__) + "/settings.json"
with open(pathToSettings) as settings_data:
    Settings: dict = json.load(settings_data)

i2c = I2CEnhanced(1) 
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
ledRing = neopixel.NeoPixel(board.D10,7, brightness=0.2, pixel_order=neopixel.GRBW)
try:
    fuelGauge = adafruit_max1704x.MAX17048(i2c)
except:
    fuelGaugeActive = False

try:
    ss = Seesaw(i2c)
except:
    try:
        # If the default address doesn't work, try the alternate one.
        ss = Seesaw(i2c,0x4a)
    except:
        ss = Seesaw(i2c,0x4b)


# Base oled setup
oled.fill(0)
oled.show()
imageBuffer = Image.new("1", (oled.width, oled.height))
font = ImageFont.load_default()

background = ImageDraw.Draw(imageBuffer)
timeElement = ImageDraw.Draw(imageBuffer)
staffElement = ImageDraw.Draw(imageBuffer)
chestElement = ImageDraw.Draw(imageBuffer)
messageElement = ImageDraw.Draw(imageBuffer)

# Clock
timeText = "12:12pm"
bbox = font.getbbox(timeText)
(font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
timeElement.text(
    (0, 0),
    timeText,
    font=font,
    fill=255,
)

# Staff
staffText = "100%"
bbox = font.getbbox(staffText)
(font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
timeElement.text((oled.width - 28, 0), staffText, font=font, fill=255,)

# Chest
staffText = "100%"
bbox = font.getbbox(staffText)
(font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
chestElement.text(((oled.width // 2) - 8, 0), staffText, font=font, fill=255,)

# Message
messageText = "ABCDEFGHIJKLMNOPQR"
bbox = font.getbbox(messageText)
(font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
messageElement.text((0, 16), messageText, font=font, fill=255,)

# Display image
oled.image(imageBuffer)
oled.show()

# Seesaw IO
actionButton = DigitalIO(ss, 5)
actionButton.direction = digitalio.Direction.INPUT
actionButton.pull = digitalio.Pull.UP

secondButton = DigitalIO(ss, 1)
secondButton.direction = digitalio.Direction.INPUT
secondButton.pull = digitalio.Pull.UP

buttonLed = DigitalIO(ss, 3)
buttonLed.direction = digitalio.Direction.OUTPUT

#File management
# Create directory for today's pictures if it doesn't exist
current_date = datetime.date.today().strftime("%Y-%m-%d")
# directory = Path("StaffOS/" + current_date)
p = Path("StaffOS/" + current_date)

try:
    p.mkdir(parents=True, exist_ok=True)
except FileExistsError:
    pass  # Directory already exists

def take_picture():
    curr_time = time.strftime("%H%M%S", time.localtime())
    filename = 'StaffOS/' + p.name + '/' + curr_time + ".jpg"
    command = 'rpicam-still --immediate=1 --output ' + filename
    subprocess.Popen(command, shell=True)


def update_element(text, element, xPos, yPos):
    messageText = text
    element.text((xPos, yPos), messageText, font=font, fill=255,)

#Start the timelapse
# timelapseCommand = 'rpicam-still -t 28800000 -o StaffOS/timelapse%d.jpg 60000'
# subprocess.Popen(timelapseCommand, shell=True)

while True:
    # Clear image buffer
    oled.fill(0)
    background.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
    oled.show()

    # Update time
    timestamp = time.strftime('%H:%M')
    update_element(timestamp, timeElement, 0, 0)
    # Update Staff battery
    if fuelGaugeActive:
        staffText = fuelGauge.cell_percent_remaining.__str__() + "%"
    else:
        staffText = "N/A"
    update_element(staffText, staffElement, oled.width - 28, 0)
    # Update Chest battery
    chestText = "90%"
    update_element(chestText, chestElement, (oled.width // 2) - 8, 0)

    # Check buttons
    if actionButton.value is False:
        print("Action Button pressed") # replace with log
        buttonLed.value = True
        ledRing.fill((255, 0, 0))
        ledRing.show()
        if audioSystem:
            takeImageSound.play()
        take_picture()
        messageText = "PICTURE TAKEN!"
        update_element(messageText, messageElement, 0, 16)
        time.sleep(0.25)  # Debounce delay
        buttonLed.value = False
        ledRing.fill((0, 0, 0))
        ledRing.show()
    if secondButton.value is False:
        print("Second Button pressed") # replace with log
        staffText = "SOMETHING ELSE!"
    
    oled.image(imageBuffer)
    oled.show()
    time.sleep(0.25)