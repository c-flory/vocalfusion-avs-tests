import unittest
import sys
import os
from selenium import webdriver
from selenium.webdriver.common import keys, action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import datetime as dt
import time
import argparse
from getpass import getpass
import calendar

def day_index(element):
	if "Monday" in element:
		return 1
	if "Tuesday" in element:
		return 2
	if "Wednesday" in element:
		return 3
	if "Thursday" in element:
		return 4
	if "Friday" in element:
		return 5
	if "Saturday" in element:
		return 6
	if "Sunday" in element:
		return 7
	
def text_to_time(words):
	time = None
	start_index = 2
	today = dt.datetime.now()
	name_to_int = dict(zip(list(calendar.day_name), range(1,8)))
	if words[0] == "Today":
		date_str = today.strftime("%y:%m:%d")
	elif words[0] == "Yesterday":
		yesterday = today - dt.timedelta(days=1)
		date_str = yesterday.strftime("%y:%m:%d")
	elif words[0] == "Last":
		today_weekday = today.isoweekday()
		test_weekday = day_index(words)
		if today_weekday > test_weekday:
			date = today - dt.timedelta(days=today_weekday-test_weekday)
		else:		
			date = today - dt.timedelta(days=7-(test_weekday-today_weekday))
		date_str = date.strftime("%y:%m:%d")
		start_index += 1
	else:
		# Too old, no time
		return None

	date_str += " {} {}".format(words[start_index], words[start_index +1])
	return dt.datetime.strptime(date_str, "%y:%m:%d %I:%M %p")

def input_to_time(input_str):
	return dt.datetime.strptime(input_str, "%y:%m:%d %I:%M %p")

def find_element(i, args):
# Find the correct scroll point to find amazon_timestamp to start from
	while(1):
		argument_time = ' '.join(str(x) for x in args.time)
		argument_time = input_to_time(argument_time)
		getelements = driver.find_elements_by_class_name("sub-text")
		time.sleep(0.5)
		for elements in getelements:
			words = elements.get_attribute('textContent')
			words = words.split(" ")
			amazon_timestamp = text_to_time(words)
			if amazon_timestamp == None:
				driver.quit()
				sys.exit("Input time is too old, cannot retrieve")
			else:
				if argument_time >= amazon_timestamp:
					return
		action.send_keys(Keys.PAGE_DOWN).perform()
		time.sleep(0.5)
		i += 1

def get_element(i, args):
	amazon_timelist = []
	amazon_responselist = []
	time_argument = ' '.join(str(x) for x in args.time)
	time_argument = input_to_time(time_argument)
	if args.end is not 0:
		end_argument = ' '.join(str(x) for x in args.end)
		end_argument = input_to_time(end_argument)
	while i > 0:
		action.send_keys(Keys.PAGE_DOWN).perform()
		time.sleep(0.2)
		i = i - 1
	getelements = driver.find_elements_by_class_name("d-list-highlight-hover")
	for elements in getelements:
		out = elements.get_attribute('textContent')
		out = out.split('\n')
		out = [x.strip(' ') for x in out]
		out = filter(None, out)
		zip(out[0::2], out[1::2])
		for x in out[0::2]:
			amazon_responselist.append(x)
		for x in out[1::2]:
			words = x.split(" ")
			timeoutput = text_to_time(words)
			if timeoutput is None:
				break
			if time_argument >= timeoutput: # Must be exact
				break
			if (args.end is 0) or (timeoutput <= end_argument):
				formatted_output = (timeoutput.strftime("%y:%m:%d %I:%M %p"))
				amazon_timelist.append(formatted_output)
	out = zip(amazon_timelist, amazon_responselist)
	for (a,b) in out:
		print a, b
	result = ([b for a,b in out])
	print "number of wakes: {}".format(len(amazon_timelist))
	print "number of alexa: {}".format(result.count("alexa"))
	if args.count:
		count_input = ' '.join(str(x) for x in args.count)
		print "number of {}: {}".format(count_input, result.count(count_input))

if __name__ == '__main__':

# Input time, email and password. Needs to be altered to add chunk of time to search for and not necessarily exact amazon_timestamp.
	argparser = argparse.ArgumentParser()
	argparser.add_argument('time', nargs='+', help='Use format year:month:day 00:00 (12hr) AM/PM')
	argparser.add_argument('--username', help='Type in full email address associated with Amazon')
	argparser.add_argument('--end', default=0, nargs='+', help='Use format year:month:day 00:00 (12hr) AM/PM')
	argparser.add_argument('--count', type=str, nargs='+', help='Type in the exact response you want to count, e.g. Text not available. Click to play recording.')
	argparser.add_argument('--error', help='If error:missing or invalid entry.level then Chrome Driver is out of date. Go to https://chromedriver.storage.googleapis.com/index.html?path=2.34/ and download latest driver and replace in usr/local/bin/')
	args=argparser.parse_args()
	password = getpass()

	driver = webdriver.Chrome()
	action = action_chains.ActionChains(driver)

	driver.get("https://layla.amazon.co.uk/spa/index.html#settings")

	username_field = driver.find_element_by_id("ap_email")
	password_field = driver.find_element_by_id("ap_password")

	username_field.send_keys("{}".format(args.username))
	password_field.send_keys("{}".format(password))
	driver.find_element_by_id("signInSubmit").click()
	try:
		element = WebDriverWait(driver, 60).until(
			EC.visibility_of_element_located((By.XPATH, "//dd[@id='iSettings']")))
	except TimeoutException:
		print "Loading timed out"
		driver.quit()
		sys.exit()
# In Safari the Home button needs to be clicked, so nother element and wait need to be included.
	time.sleep(4)
	driver.find_element_by_xpath("//dd[@id='iSettings']").click()
	try:
		element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//a[@data-automation-id='dialog-history']")))
	except TimeoutException:
		print "Loading timed out"
		driver.quit()
		sys.exit()
	driver.find_element_by_xpath("//a[@data-automation-id='dialog-history']").click()

	i = 0

	find_element(i, args)
	get_element(i, args)
	driver.quit()