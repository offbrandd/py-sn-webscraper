from time import sleep
from datetime import datetime
import os
import numpy as np
import threading
import re

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import csv

csv_reader = csv.reader(open("data.csv", "r"))
# convert string to list
list_of_csv = list(csv_reader)
sn_column = 1
exp_date_column = 2

output = []
total = len(list_of_csv)
# csv for writing output data
output_file = open("output.csv", "w+", newline="")
output_file.truncate()  # clears file (probably better just create a new file for each execute, just in-case)


# allows us to write to a shared file from concurrent threads in a Thread-Safe manner
writeLock = threading.Lock()


def setup_chrome():
    site = "https://www.dell.com/support/home/en-us"
    # set the driver
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    # load this site
    driver.get(site)
    return driver

def checkDell(driver, sn):  # searching s/n argument on dell page, returns expiration date text
    wait = WebDriverWait(driver,5)
    driver.get("https://www.dell.com/support/search/en-us#q=" + sn)
    sleep(1)
    if "null" in driver.current_url:
        return "No warranty info available"
    else:
        try:
            return wait.until(EC.presence_of_element_located((By.XPATH,"//*[@class='warrantyExpiringLabel mb-0 ml-1 mr-1']",))).text
        except:
            try:
                wait.until(EC.presence_of_element_located((By.ID, "null-result-text")))
                return "Invalid SN"
            except:
                return "Could not find expiry label"
        
# given a list, iterate through and call checkDell(), modifying the list with the results
def checkList(driver, list):
    for row in list:
        result = checkDell(driver, row[sn_column])
        #searches for first occurence of a number in string, returns a Match object. This is all to remove the "expires", "expired", etc from the result
        m = re.search(r"\d", result)
        if m:  # if number found
            #saves string with anything before first digit sliced off
            row[exp_date_column] = result[m.start():]
        else:  # if no number found
            row[exp_date_column] = result  # saves result


def checkBatch(batch):  # batch is a list of chunks of data. this is so it will write to output file regularly instead of just at the end
    print("thread started checking")
    global output_file
    driver = setup_chrome()  # setup driver
    for chunk in batch:
        checkList(driver, chunk)
        writeLock.acquire()  # prevent other threads from writing to file
        output_file = open("output.csv", "a")  # opens file in append mode, so each thread can throw their data on without overwriting anything
        with output_file:
            write = csv.writer(output_file)
            write.writerows(chunk)
        writeLock.release()  # allow other threads to write to file
    driver.close()
    print("thread finished checking")



# make runable
if __name__ == "__main__":
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    num_agents = 6
    num_chunks = 25 #work around for issue with array_split() that is caused when number of sections argument is not a factor of length of list
    chunks = np.array_split(list_of_csv[1:], num_chunks)
    batches = np.array_split(chunks, num_agents)

    threads = []
    for batch in batches:
      threads.append(threading.Thread(target=checkBatch, args=(batch,)))
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()
    
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
