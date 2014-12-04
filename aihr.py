#!/usr/bin/env python3
from bs4 import BeautifulSoup
from datetime import datetime
from collections import OrderedDict
from datetime import datetime
from itertools import chain
from random import choice
from time import sleep
import urllib.request
import csv
import re
import logging


# Set up log
logging.basicConfig(filename='aihr.log', level=logging.INFO,
                    format='%(levelname)s %(asctime)s: %(message)s')


def parse_ngo(html_file, ngo_id):
  soup = BeautifulSoup(html_file)

  # Each line in the NGO details page is wrapped in a ligne-infos class, with two labels inside with the key/value data
  ngo_details_raw = soup.select('.maxdetails .ligne-infos')
  ngo_details = OrderedDict()

  for line in ngo_details_raw:
    parts = line.select('label')  # Isolate the label tags

    if len(parts) == 2:  # Make sure the labels come in pairs
      # Key needs lots of cleaning
      ngo_key = re.sub('[:,]', '', str(parts[0].text)).replace('الهاتف/الفاكس', 'phone').strip().replace(' ', '_').lower()

      # Using the .text generator doesn't work with nested tags, so using it
      # on the values returns a bunch of Nones. Also, many entries can have
      # multiple things (like phone numbers, e-mails, etc).

      # To get around that, this uses the .contents generator, which seems to
      # strip all tags except br. This will loop through the contents of each
      # tag, remove all forms of the br tag, clean it up, and then join
      # multiple entries with a comma. Complicated.
      ngo_values = [re.sub('</* *br */*>', '', str(value)).strip() for value in parts[1].contents]
      ngo_value = ', '.join([ngo_value for ngo_value in ngo_values if ngo_value != ''])

      # Save everything to a dictionary
      ngo_details['ngo_id'] = ngo_id
      ngo_details['date_added'] = datetime.now()
      ngo_details[ngo_key] = ngo_value

  return(ngo_details)


# NGO IDs to loop through
ngo_ids = range(4, 6 + 1)

#-------------------------------
# Courtesy scraping parameters
#-------------------------------
wait_time = range(5, 15)
user_agents = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'
]


#----------------------------------
# Loop through IDs and parse NGOs
#----------------------------------
# Initialize list for parsed NGOs
ngos = []

# Do the actual parsing
for ngo_id in ngo_ids:
  wait = choice(wait_time)
  agent = choice(user_agents)

  # Log what will happen
  logging.info("Downloading {0} as {1}".format(ngo_id, agent))

  # Download info from NGO page
  url = "http://www.aihr-resourcescenter.org/search_ong/single_result.php?lang=fr&id={}".format(ngo_id)
  response = urllib.request.Request(url, headers={'User-Agent': agent})
  handler = urllib.request.urlopen(response).read()

  # Parse page
  parsed = parse_ngo(handler, ngo_id)

  # Save information to global list
  if 'arabic_name' in parsed:
    ngos.append(parsed)
    logging.info("Saved {0}".format(parsed['arabic_name']))
  else:
    logging.info("No NGO with id {0}".format(ngo_id))

  logging.info("Waiting for {0} seconds before moving on\n".format(wait))
  sleep(wait)


#--------------
# Save to CSV
#--------------
# Get a list of all possible dictionary keys for column headers
all_headers = [list(row.keys()) for row in ngos]

# Flatten list and remove duplicates (while maintaining order!)
# This is slow for huge lists, but this is not a huge list, so who cares
# 
# Converts:
#   [['name', 'phone', 'email'], ['name', 'fax', 'email']]
# to: 
#   ['name', 'phone', 'email', 'fax']
headers = []
for x in chain.from_iterable(all_headers):
  if x not in headers:
    headers.append(x)

# Write NGO dictionary to a CSV file
with open('aihr.csv','w') as f:
  dw = csv.DictWriter(f, fieldnames=headers)
  dw.writeheader()
  dw.writerows(ngos)
