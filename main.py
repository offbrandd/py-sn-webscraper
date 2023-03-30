from time import sleep
from datetime import datetime

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv

csv_reader = csv.reader(open('data.csv', 'r'))
# convert string to list
list_of_csv = list(csv_reader)

searching = False


def setup_chrome():
    site = 'https://www.dell.com/support/home/en-us'
    # set the driver
    driver = webdriver.Chrome()
    # load this site
    driver.get(site)
    return driver


def checkDell(driver, sn):  # TODO return boolean status and date
    sleep(0.4)
    searching = True
    # wait until search box loaded in, select it, send serial number, press enter
    element = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.ID, "mh-search-input")))

    entered = False
    while not entered:
        try:
            entered = True
            element.clear()
            element.send_keys(sn)
            element.send_keys(Keys.ENTER)

        except:
            entered = False

    try:
        # wait until warranty check text ready
        element = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, "//*[@class='warrantyExpiringLabel mb-0 ml-1 mr-1']")))
        element_text = element.text
    except:
        return False, False

    # checks text and returns warranty status and bool representing whether or not check was successful
    if "Expired" in element_text:
        searching = False
        return False, True
    elif "Expires" in element_text or "ProSupport" in element_text:
        searching = False
        return True, True
    else:
        print("NO WARNRANTY FOUND??")
        searching = False
        return False, False


# make runable
if __name__ == '__main__':
    driver = setup_chrome()

    total_check = 0  # TEMP check how many assets we've checked
    start_time = datetime.now()

    # iterate through csv, calling checkDell
    i = 1

    while i < len(list_of_csv):
        if not searching:
            in_warranty, check_successful = checkDell(
                driver, list_of_csv[i][8])
            if check_successful:  # yay, save warranty status and date TODO: save warranty status and date
                print(str(i) + " " + str(in_warranty))
                i += 1
                total_check += 1

    end_time = datetime.now()

    print("# of assets: " + str(total_check) + "  start: " +
          str(start_time) + "  end: " + str(end_time))
    driver.quit()
