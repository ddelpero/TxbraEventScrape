from lxml import html
from collections import OrderedDict
import requests
import icalendar
from datetime import date, timedelta
import os

class TxbraEventScrape():

   def __init__(self):
      self.url = 'http://www.txbra.org/events'
      self.href = 'event.asp'
      self.calendarDirectory = 'ics/'
      self.calendars = dict()
      self.calendars['all'] = icalendar.Calendar()
      self.calendars['road'] = icalendar.Calendar()
      self.calendars['cx'] = icalendar.Calendar()


   def writecalendars(self):
      for k,v in self.calendars.iteritems():
         print "Writing calendar", k
         f = open(os.path.join(self.calendarDirectory, 'txbra_' + k + '.ics'), 'wb')
         f.write(v.to_ical())
         f.close()


   def addEvent(self, eventType, event,):
      self.calendars['all'].add_component(event)
      if eventType == 'Cyclo-cross':
         self.calendars['cx'].add_component(event)
      else:
         self.calendars['road'].add_component(event)


   def buildEvent(self, startDate, endDate, details):
      #print details
      print details['Event Type'], details['Event Name'], startDate, endDate
      event = icalendar.Event()
      event.add('dtstart', startDate)
      event.add('dtend', endDate)
      event.add('summary', details['Event Name'])
      event.add('status', details['Event Status'])
      event.add('location', details['Event Location'])
      event.add('url', details['Registration Website'])

      description = "TXBRA Event: " + details['TXBRA Event'] + os.linesep
      description += "Registration Website: " + details['Registration Website'] + os.linesep
      description += 'Event Type: ' + details['Event Type'] + os.linesep
      description += 'Event Status: '+ details['Event Status'] + os.linesep
      description += 'Event Flyer: ' + details['Event Flyer'] + os.linesep
      description += 'Contact Name: ' + details['Contact Name'] + os.linesep
      description += 'Email Address: ' + details['Email Address'] + os.linesep
      description += 'Event Website: ' + details['Event Website'] + os.linesep
      description += 'Texas Cup Tier: ' + details['Texas Cup Tier'] + os.linesep
      description += 'Texas Cup Event: ' + details['Texas Cup Event'] + os.linesep
      event.add('description', description)
      return event


   def getURL(self, race_event):
      return self.url+ "/" + race_event


   def scrape(self):
      page = requests.get(self.url)
      tree = html.fromstring(page.content)
      events = filter(lambda link: link.find(self.href)>=0, tree.xpath('//a/@href'))
      # the event page has a line for each day. Filter the list to only have unique events
      events = list(OrderedDict.fromkeys(events)) 
      #print events

      for race_event in events:
         #print URL + race_event
         page = requests.get(self.getURL(race_event))
         tree = html.fromstring(page.content)
         # build key/pair dictionary of event page
         details = dict()
         for t in tree.xpath('//tr'):
           if len(t.xpath('td//text()')) == 1:
             details[t.xpath('td//text()')[0]] = ''
           if len(t.xpath('td//text()')) > 1:
             details[t.xpath('td//text()')[0]] = t.xpath('td//text()')[1]
         #print details
         
         details['TXBRA Event'] = self.getURL(race_event)
         # Event dates is a list of dates. If we have consecutive days, create a multi-day event
         # if we have non-consecutive days, create an individual event for each date
         event_dates = details['Event Dates'].split(',')
         if len(event_dates):
            # the string date isn't zero padded. Maybe there's a better way to automatically zero pad the numbers
            # otherwise, split the date string
            dtstart = event_dates[0].split('/')
            dtend = event_dates[len(event_dates)-1].split('/')

            #Our start delta is going to be start date + the number of days - 1 to offest for the list length
            dtStartDelta = date(int(dtstart[2]),int(dtstart[0]),int(dtstart[1]))+timedelta(days=len(event_dates)-1)
            dtEndDelta = date(int(dtend[2]),int(dtend[0]),int(dtend[1]))
            # print details['Event Type'], dtStartDelta, dtEndDelta, len(event_dates)
            if dtStartDelta == dtEndDelta: # we have consecutive days, so we want to create a multi-day event
               dtstart = event_dates[0].split('/')
               dtend = event_dates[len(event_dates)-1].split('/')
               start = date(int(dtstart[2]),int(dtstart[0]),int(dtstart[1]))
               #to create an all day event, the end date needs to be midnight the next day
               end = date(int(dtend[2]),int(dtend[0]),int(dtend[1]))+timedelta(days=1) 
               event = self.buildEvent(start, end, details)
               self.addEvent(details['Event Type'], event)
            else: #we a recurring event, so we want to create a single event for each day
               for day in event_dates:
                  dtstart = day.split('/')
                  start = date(int(dtstart[2]),int(dtstart[0]),int(dtstart[1]))
                  #to create an all day event, the end date needs to be midnight the next day
                  #these probably aren't all day events, but there's nothing on the page that indicates start time
                  end = start+timedelta(days=1)
                  if start >= date.today():
                     event = self.buildEvent(start, end, details)
                     self.addEvent(details['Event Type'], event) 
      return self

if __name__ == "__main__":
   TxbraEventScrape().scrape().writecalendars()