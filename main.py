from time import sleep
from datetime import datetime
import os
import numpy as np
import threading

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
num_checked = 0; #used to track progress and update progress bar
output_file = open("output.csv", "w+", newline="") #csv for writing output data
output_file.truncate() #clears file


lock = threading.Lock() #allows us to write to a shared file from concurrent threads in a Thread-Safe manner


def setup_chrome():
    site = "https://www.dell.com/support/home/en-us"
    # set the driver
    # driver = webdriver.Chrome()
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    # load this site
    driver.get(site)
    return driver


def checkDell(
    driver, sn
):  # searching s/n argument on dell page, returns expiration date text
    wait = WebDriverWait(driver, 10)
    try:
        element = wait.until(
            EC.presence_of_element_located((By.ID, "mh-search-input"))
        )  # wait until element is present in page (not necessarily visible)
        element.clear()
        element.send_keys(sn)
    except:
        return "COULD NOT FIND SEARCH BAR"

    try:
        wait.until(
            EC.text_to_be_present_in_element_value((By.ID, "mh-search-input"), sn)
        )
        element.send_keys(Keys.ENTER)
    except:
        return "COULD NOT SEARCH"

    try:
        element = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@class='warrantyExpiringLabel mb-0 ml-1 mr-1']",
                )
            )
        )
        return element.text
    except:
        return "SN LOOKUP FAILURE"


def addProgress():
    global num_checked
    num_checked += 1
    #os.system("clear")
    print(str(num_checked) + "/" + str(total) + "\n")
    percentage = num_checked / total
    bar_length = 50
    p = round(percentage * bar_length)
    s = "["
    for i in range(p):
        s += "#"
    for i in range(bar_length - p):
        s += "-"
    s += "]"
    print(s)


def checkList(driver, list):# given a list, iterate through and call checkDell(), modifying the list with the results
    length = len(list)
    i = 0
    if list[0][2] == "Service Tag":
        i = 1
    while i < length:
        list[i][6] = checkDell(driver, list[i][2])
        addProgress()
        i += 1

def checkBatch(batch): #batch is a list of chunks of data. this is so it will write to output file regularly instead of just at the end
    global output_file
    driver = setup_chrome() #setup driver
    for chunk in batch:
        print("chunk size " + str(len(chunk)))
        checkList(driver, chunk)
        print("acquiring lock")
        lock.acquire() #prevent other threads from writing to file
        output_file = open("output.csv", "a") #opens file in append mode
        with output_file:
            print("writing")
            write = csv.writer(output_file)
            write.writerows(chunk)
        lock.release() #allow other threads to write to file
    driver.close()

# make runable
if __name__ == "__main__":
    num_agents = 8
    num_chunks = 336
    chunks = np.array_split(list_of_csv, num_chunks)
    batches = np.array_split(chunks, num_agents)

    threads = []
    for batch in batches:
        threads.append(threading.Thread(target=checkBatch, args=(batch,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
