import time
import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)
from datetime import datetime
sys.path.insert(1, './database')
from SQLDal import SQLDalConn


IS_EMULATED_MODULES = False
isFullySetup = input('Do you have the RFID/Scale hardware insalled and ready to go using a Raspberry Pi? (y/n):\n')
if isFullySetup[0].lower() == 'y':
  import RPi.GPIO as GPIO
  from mfrc522 import SimpleMFRC522
  sys.path.insert(1, './helpers')
  from hx711 import HX711
else:
  IS_EMULATED_MODULES = True



DT = 5 # Read from this
SCK = 6 # Set this true/false

referenceUnit = 465 # Calculated on a known weight
rfid_tag_weight = 3.17 # grams

class Program:
  def __init__(self, IS_EMULATED_MODULES):
    # If running IS_EMULATED_MODULES = true then the program swaps out
    # the RFID reader module and scale module for user input functions
    self.IS_EMULATED_MODULES = IS_EMULATED_MODULES

    # Initalize the scale
    if not self.IS_EMULATED_MODULES:
      self.scale = HX711(DT, SCK)
      self.scale.set_reading_format('MSB', 'MSB')
      self.scale.set_reference_unit(referenceUnit)
      self.scale.reset()
      self.scale.tare()
      print('Scale Module Setup.')

      # Initalize RFID
      self.reader = SimpleMFRC522()
      print('RFID Module Setup.')

    # Read existing weights
    self.dal = SQLDalConn()


  def getExistingWeights(self):
    # Display existing DB Weights
    sqlQuery = """
        SELECT * FROM smartScale.Scale s
        ORDER BY s.weightTime DESC;
      """
    dbWeights = self.dal.executeSelectQuery(sqlQuery)
    print('Existing DB Weights')
    pp.pprint(dbWeights)
    

  # It's important to run GPIO cleanup when finished using them
  def cleanAndExit(self):
    print('Cleaning...')
    if not self.IS_EMULATED_MODULES:
      GPIO.cleanup()
    sys.exit()


  def EMULATE_readRFID(self):
    print('Running test EMULATE_readRFID')
    id = input('\nEnter an ID for the imaginary thing we are about to weigh (Numbers only as it\'s supposed to be an RFID tag):\n')
    containerWeight = input('\nIf weighing something in a container than enter the container weight (Must be a number):\n')

    return [int(id), float(containerWeight)]

  def readRFID(self):
    print('Looking for RFID...')
    try:
      # self.reader.read() returns the ID and the string you can save with it
      # in this case I'm just saving the weight of the container there but
      # maybe I should change it to be JSON to save more info
      id, containerWeight = self.reader.read()
      print('RFID found!')
      print(id)
      print(containerWeight)

      if containerWeight.rstrip('\x00') == '':
        containerWeight = 0

      return [id, float(containerWeight)]

    except Exception as e:
      print(e)
      sys.exit()


  def EMULATE_runScale(self, RFID_CONTAINER_WEIGHT):
    calculatedWeight = input('\nEnter the weight of the imaginary item. If you entered a containerWeight earlier then make sure this value is higher as we subtract the container weight from this value. (Must be a number):\n')

    return float(calculatedWeight) - RFID_CONTAINER_WEIGHT


  def runScale(self, RFID_CONTAINER_WEIGHT):
    # Starting from the 3rd number to ensure no miscalculations when item first placed
    startFrom = 3
    # Want to get a few numbers to average out instead of just grabbing the first one
    # as the values shift a very small amount sometimes
    valuesToAverage = 10
    values = []
    while len(values) < (valuesToAverage + startFrom):
      try:
        val = self.scale.get_weight(5)
        print(val)

        # TODO: See how this works, obviously cant measure anything less than 1g
        # with this but if things are in a container then it should never be 1g
        if val > 1:
          if len(values) >= startFrom:
            print('-------')
            print(f'Adding value to average: {val}')

          values.append(float(val))

        self.scale.power_down()
        self.scale.power_up()
        time.sleep(0.1)

      except (KeyboardInterrupt, SystemExit):
        sys.exit()

    # Rounding to 3 decimal places
    # TODO: Remove outliers?
    avgWeight = sum(values[startFrom:]) / valuesToAverage

    # If there's a container weight we should subtract
    avgWeightSubContainer = avgWeight - RFID_CONTAINER_WEIGHT
    averagedWeight = round(avgWeightSubContainer, 3)
    print('Averaged out weight:')
    print(averagedWeight)

    return averagedWeight

  def saveToDB(self, RFID_ID, averagedWeight):
    print(f'Saving ID and Weight to db: ({RFID_ID}, {averagedWeight})')
    now = datetime.now()
    query = """
        INSERT INTO smartScale.Scale
        VALUES ({}, {}, "{}")
    """.format(RFID_ID, averagedWeight, now.strftime('%Y-%m-%d %H:%M:%S'))

    self.dal.executeInsertOrUpdateQuery(query)
    print('Saved...')


  def compareToPreviousWeight(self, RFID_ID, newWeight):
    print('Comparing to previous weight')
    query = """
        SELECT weight
        FROM smartScale.Scale
        WHERE id = {}
        ORDER BY weightTime DESC
        LIMIT 1
    """.format(RFID_ID)

    prevWeight = self.dal.executeSelectQuery(query)

    if len(prevWeight) > 0:
        change = newWeight - float(prevWeight[0][0])
        print('Previous weight:')
        print(prevWeight[0][0])
        print('Change in weight from last measurement:')
        print(change)
    else:
        print('First time measurement...')

  def run(self):
    print('Starting Smart Scale')
    try:
      while True:
        print('\n-----------------------------------------')
        print('Running smart scale...')
        print('--------------')
        print('Retrieving existing weights from database')
        self.getExistingWeights()

        print('\n-----------------------------------------')
        print('Run RFID:')
        RFID_ID, RFID_CONTAINER_WEIGHT = self.EMULATE_readRFID() if self.IS_EMULATED_MODULES else self.readRFID()

        print('\n-----------------------------------------')
        print('Run Scale:')
        averageWeight = self.EMULATE_runScale(RFID_CONTAINER_WEIGHT) if self.IS_EMULATED_MODULES else self.runScale(RFID_CONTAINER_WEIGHT)
        print(f'Calculated Weight: {averageWeight}')

        print('\n-----------------------------------------')
        print('MySQL Section:')
        self.compareToPreviousWeight(RFID_ID, averageWeight)
        print('--------------')
        self.saveToDB(RFID_ID, averageWeight)

        print('\n-----------------------------------------')
        print('Complete...would you like to run again?')
        response = input('\nY/N:\n')

        if response.lower() != 'y':
          sys.exit()
    
    except (KeyboardInterrupt, SystemExit):
      print('Exiting...')
    except Exception as e:
      print('Ran into an error...')
      print(e)

    print('Ending...')
    self.cleanAndExit()

smartScale = Program(IS_EMULATED_MODULES)
smartScale.run()
