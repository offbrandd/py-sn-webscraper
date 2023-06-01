from time import sleep
from datetime import datetime
import os
import numpy as np
import threading
import re

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import csv

csv_reader = csv.reader(open("data.csv", "r"))
# convert string to list
list_of_csv = list(csv_reader)
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
    wait = WebDriverWait(driver, 20)
    try:
        element = wait.until(EC.presence_of_element_located((By.ID, "mh-search-input")))  # wait until element is present in page (not necessarily visible)
        driver.find_element(By.ID, "mh-search-input").send_keys(sn) #send string arugment SN into search box
        wait.until(EC.text_to_be_present_in_element_value((By.ID, "mh-search-input"), sn)) #double check SN is actually in search box
        driver.find_element(By.ID, "mh-search-input").send_keys(Keys.ENTER) #press enter to search
        wait.until(EC.text_to_be_present_in_element_value((By.ID, "mh-search-input"), "")) #on this site, search box contents are emptied when search is performed. check box is empty as means of verifying page has loaded. this probably isn't necessary
        loading = True
        while loading: #wait.until logic not prevent thread from continuing until a certain state is met, attempts to account for pages that result from invalid serial numbers (doesn't currently work)
            try:
                wait.until(EC.text_to_be_present_in_element((By.XPATH,"//*[@class='service-tag mb-0 d-none d-lg-block']",), sn))
            except:
                try:
                    wait.until(EC.text_to_be_present_in_element((By.XPATH,"//*[@class='dds__mb-2 dds__mb-md-0 Gray800']",), "Article Number: 000196860"))
                    return "SERVICE TAG ERROR"
                except:
                    try:
                        wait.until(EC.presence_of_element_located((By.ID, "spanValMsgEntryError")))
                    except:
                        print("cant find the thing")
                        continue
            loading = False
        element = wait.until(EC.presence_of_element_located((By.XPATH,"//*[@class='warrantyExpiringLabel mb-0 ml-1 mr-1']",))) #verify the text we want is present
        return wait.until(EC.presence_of_element_located((By.XPATH,"//*[@class='warrantyExpiringLabel mb-0 ml-1 mr-1']",))).text
    except Exception as er:
        return "SEARCH ERROR"

# given a list, iterate through and call checkDell(), modifying the list with the results
def checkList(driver, list):
    for row in list[1:]:
        # column 2 is the serial number column in the dataset
        result = checkDell(driver, row[2])

        #searches for first occurence of a number in string, returns a Match object. This is all to remove the "expires", "expired", etc from the result
        m = re.search(r"\d", result)
        if m:  # if number found
            #saves string with anything before first digit sliced off
            row[6] = result[m.start():]
        else:  # if no number found
            row[6] = checkDell(driver, row[2])  # saves result


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
    num_agents = 5
    num_chunks = 13
    chunks = np.array_split(list_of_csv, num_chunks)
    batches = np.array_split(chunks, num_agents)

    threads = []
    for batch in batches:
      threads.append(threading.Thread(target=checkBatch, args=(batch,)))
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()
