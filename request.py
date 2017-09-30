
import json
import requests
import datetime

# List of airports in IATA code that will be searched as a destination from Boston.
destin_list = ['ATL', 'PEK', 'DXB', 'LAX', 'HND', 'ORD', 'LHR', 'HKG', 'PVG', 'CDG', 'DFW', 'AMS', 'FRA', 'IST', 'CAN', 'SIN', 'DEN', 'ICN', 'BKK', 'DEL', 'CGK', 'SFO', 'KUL', 'MAD', 'CTU', 'SEA', 'BOM', 'MIA', 'YYZ', 'BCN', 'LGW', 'TPE', 'MUC', 'SYD', 'KMG', 'SZX', 'FCO', 'MEX', 'SHA', 'MNL', 'NRT', 'DOH', 'GRU', 'AEP', 'SVO', 'LED', 'JNB', 'CAI', 'CMN', 'ADD']

#Shortened list because it's useful to be able to do more than one request a day
short_list = ['ATL', 'PEK', 'DXB', 'LAX']

class Flight(object):
    """
    Creates a flight class object with the following variables (if not tagged otherwise, they are optional)    

    Flight Details: (When requesting multiple flights, they must occur on different dates and must be in ascending order in the list)
    origin : string (IATA airport codes - REQUIRED)
    destination : string (Reminder that json strings are quoted - REQUIRED)
    date : string (YYYY-MM-DD - Must be in the future - REQUIRED)
    maxStops : integer
    maxConnectionDuration : integer (Not sure about this option yet)
    preferredCabin : string (Allowed values are COACH, PREMIUM_COACH, BUSINESS, and FIRST.)
    earliestTime : string (HH:MM)
    latestTime : string (HH:MM)
    permittedCarrier : list (IATA 2 digit airline codes)
    prohibitedCarrier : list
    alliance: list (Allowed values are ONEWORLD, SKYTEAM, and STAR.)
    maxPrice: string (ISO 4217 Currency codes followed by price in xxx.xx so USD200.00 - Total trip cost)
    saleCountry : string (IATA 2 digit Country Codes - defaults to origin city $$)
    ticketingCountry : string 
    refundable : boolean (Reminder that booleans are quoted a lowercase for json)
    solutions : integer (limits number of responses - Max 500 - defaults to max)
    """
    def __init__(self, origin = 'BOS', destination = 'LHR', date = '2018-12-12'):
        self.origin = origin
        self.destination = destination
        self.date = date
        self.flight_req = {"origin" : self.origin, "destination" : self.destination, 'date' : self.date}

class Qpxreq(object):
    """
    Class that holds the data for a request to google's QPX API
    If you require an API key - https://console.cloud.google.com/apis/dashboard?project=personalfarealert&duration=PT1H
        click on Enable APIs and Services - search for QPX and get a key.  You may need to link a developer account to your gmail to do this.
        You can then paste your API key into the api_key string or handle it in a more secured way if you're doing a more substantial depoloyment.
    Has variables for different flight options:
    Passangers: (REQUIRED adultCount and/or seniorCount >= 1 - child/infantCount values are not required)
       adultCount : integer
       childCount : integer
       infantCount : integer
       infantInLapCount : integer
       infantInSeatCount : integer
       seniorCount: integer
    """    
    def __init__(self, flightCount = 1, adultCount = 1, api_key = '', base_url = 'https://www.googleapis.com/qpxExpress/v1/trips/search?key='):
        self.flightCount = flightCount
        self.adultCount = adultCount
        self.base_url = base_url
        self.api_key = api_key
        self.url = base_url + api_key
        self.headers = {'content-type': 'application/json'}
        self.req = {"request": {"passengers": {"adultCount": self.adultCount}, "slice": [], "solutions" : 500}}

        
    def add_flights(self, flight = ''):
        if not flight:
            flight = Flight()
        for i in range(0, self.flightCount):
            self.req["request"]["slice"].append(flight.flight_req)
    
    def multiLegFlights(self):
        """
        Takes user input to automate the creation of flight requests iterated over given timeframe
        Currently takes no variables.  Max days searched = 10
        """
        legCount = int(input('How many legs do you have in your journey? (Maximum = 10): '))
        for i in range(0, legCount):
            origin = input('Three letter IATA code of the origin city for leg {}: '.format(i+1)).upper()
            destination = input('Three letter IATA code of the destination city for leg {}: '.format(i+1)).upper()
            year = int(input('4-digit year to depart {}: '.format(origin)))
            month = int(input('2-digit month to depart {}: '.format(origin)))
            day = int(input('2-digit day to depart {}: '.format(origin)))
            date = datetime.date(year, month, day)
            flight = Flight(date = str(date), origin = origin, destination = destination)
            self.req["request"]["slice"].append(flight.flight_req)

    def send_req(self):
        """
        Sends the QPX request to google and strips some options for increased usability.
        If the request fails, it will not strip data as the failure response comes in a different format.
        The returned error can be troubleshot on google's FAQ for theri QPX api.
        """
        response = requests.post(self.url, data=json.dumps(self.req), headers = self.headers)
        json_response = response.json()
        try:
            data = json_response['trips']['tripOption'][:]
            return data
        except:
            return json_response
       
    def cull(self, data=''):
        """
        Takes google's response from send_req() and further strips extraneous data and puts it into a more usable format.
        """
        if not data:
            data = self.send_req()
        searchDate = str(datetime.datetime.now().date())
        cull_list = []
        for item in data:
            dD = item['slice'][0]['segment'][0]['leg'][0]['departureTime'].split('T')[0]
            plan = item['pricing'][0]['fare'][0]['origin'] + ' - ' + item['pricing'][0]['fare'][0]['destination']
            price = item['saleTotal']
            layovers = len(item['slice'][0]['segment']) - 1
            origin = item['pricing'][0]['fare'][0]['origin']
            destination =  item['pricing'][0]['fare'][0]['destination']
            carrier = item['pricing'][0]['fare'][0]['carrier']
            leg = []
            for k in range(len(item['slice'][0]['segment'])):
                departureTime = item['slice'][0]['segment'][k]['leg'][0]['departureTime']
                arrivalTime = item['slice'][0]['segment'][k]['leg'][0]['arrivalTime']
                flight = item['slice'][0]['segment'][k]['flight']
                origin = item['slice'][0]['segment'][k]['leg'][0]['origin']
                destination = item['slice'][0]['segment'][k]['leg'][0]['destination']
                mileage = item['slice'][0]['segment'][k]['leg'][0]['mileage']
                duration = item['slice'][0]['segment'][k]['leg'][0]['duration']
                leg.append({'departureTime' : departureTime, 'arrivalTime' : arrivalTime, 'flight' : flight, 'origin' : origin, 'destination' : destination, 'mileage' : mileage, 'duration' : duration})
            cull_list.append({'searchDate': searchDate, 'plan' : plan, 'departureDate' : dD, 'price' : price, 'layovers' : layovers, 'origin' : origin, 'destination' : destination, 'carrier' : carrier, 'leg' : leg})
        return cull_list

    def dump_json(self, cull_list, filename=''):
        """
        Creates a .json file and dumps the culled response from google into that file.
        Default file-name is the current date in YYYY-MM-DD format.
        """
        if not filename:
            filename = '{0}.json'.format(datetime.datetime.now().date())
        with open(filename, 'w') as f:
            json.dump(cull_list, f)
        print('Data saved as {0}'.format(filename))

    
def make_do(destin_list):
    """
    Automates the creation of QPX requests with items from destin_list as the destinations for flights - Boston is the default origin.
    Those requests are then sent and the response is culled and written to a file - default YYYY-MM-DD.json 
    """
    filename = '{0}.json'.format(datetime.datetime.now().date())
    list_all = []
    for item in destin_list:
        a = Qpxreq()
        a.add_flights(Flight(destination = item, date = '2018-04-01'))
        list_all += a.cull()
    with open(filename, 'w') as f:
        json.dump(list_all, f)
    print('Data saved as {0}'.format(filename))


def make_list():
    """
    Me plpaying with datetime and whatnot.  It went along with some expirments I did with the functionality of the QPX api.
    """
    yearStart = 2018
    monthStart = 1
    dayStart = 1
    yearEnd = 2018
    monthEnd = 2
    dayEnd = 10
    startDate = datetime.date(yearStart, monthStart, dayStart)
    endDate = datetime.date(yearEnd, monthEnd, dayEnd)
    days = endDate - startDate
    iDay = startDate
    price_list = []
    date_list = []
    price_list_of_lists = []
    for i in range(0, days.days):
        temp_list = []
        p = Qpxreq()
        flight = Flight(date = str(iDay))
        p.req["request"]["slice"].append(flight.flight_req)
        g = p.send_req()
        date_list.append(iDay)
        price_list += g[0]['pricing'][0]['saleTotal']
        for n in range(len(g)):
            temp_list += g[n]['pricing'][0]['saleTotal']
        price_list_of_lists.append(temp_list[:])
        iDay += datetime.timedelta(1)




"""
The following comments are the format in which QPX wants their json request formated .
If you want to play with requests this is a good place to start.


{
  "request": {
    "passengers": {
      "kind": "qpxexpress#passengerCounts",
      "adultCount": integer,
      "childCount": integer,
      "infantInLapCount": integer,
      "infantInSeatCount": integer,
      "seniorCount": integer
    },
    "slice": [
      {
        "kind": "qpxexpress#sliceInput",
        "origin": string,
        "destination": string,
        "date": string,
        "maxStops": integer,
        "maxConnectionDuration": integer,
        "preferredCabin": string,
        "permittedDepartureTime": {
          "kind": "qpxexpress#timeOfDayRange",
          "earliestTime": string,
          "latestTime": string
        },
        "permittedCarrier": [
          string
        ],
        "alliance": string,
        "prohibitedCarrier": [
          string
        ]
      }
    ],
    "maxPrice": string,
    "saleCountry": string, (IATA Country Codes - http://www.fedex.com/mp/tracking/codes.html for a list or just google)
    "ticketingCountry": string,
    "refundable": boolean,
    "solutions": integer
  }
}
"""



#This is the minimum request you can do.

#{"request": {"passengers": {"kind": "qpxexpress#passengerCounts", "adultCount": self.adultCount}, "slice": [{"kind": "qpxexpress#sliceInput", "origin": self.origin, "destination": self.destination, "date": self.date}]}}


#req = {
#  "request": {
#    "passengers": {
#      "adultCount": 1,
#    },
#    "slice": [
#      {
#        "origin": 'LHR',
#        "destination": 'BOS',
#        "date": '2017-08-22',
#      },
#    ],
#  }
#}

#req = {
#  "request": {
#    "passengers": {
#      "adultCount": 1,
#    },
#    "slice": [
#      {
#        "origin": 'LHR',
#        "destination": 'BOS',
#        "date": '2017-08-22',
#      },
#        {
#        "origin": 'LHR',
#        "destination": 'BOS',
#        "date": '2017-08-22',
#      
#    ],
#  }
#}

# This was code that creates multiple flight requests over a calendar period.
#   The idea was that you could get multiple days of flight searches done in one request.
#   Sadly, it seems that I cannot pull the pricing information for individual flights with
#   this method, so there is no data added because the granularity increases with search size (womp)
#        yearStart = int(input('4-digit year in which to START search: '))
#        monthStart = int(input('2-digit month in which to START search: '))
#        dayStart = int(input('2-digit day on which to START search: '))
#        yearEnd = int(input('4-digit year in which to END search: '))
#        monthEnd = int(input('2-digit month in which to END search: '))
#        dayEnd = int(input('2-digit day on which to END search: '))
#        startDate = datetime.date(yearStart, monthStart, dayStart)
#        endDate = datetime.date(yearEnd, monthEnd, dayEnd)
#        days = endDate - startDate
#        iDay = startDate
#        for i in range(0, days.days):
#            flight = Flight(date = str(iDay))
#            self.req["request"]["slice"].append(flight.flight_req)
#            iDay += datetime.timedelta(1)
