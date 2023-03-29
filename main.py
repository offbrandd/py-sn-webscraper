from time import sleep
from datetime import datetime

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv

# Return a reader object which will
# iterate over lines in the given csvfile
csv_reader = csv.reader(open('data.csv', 'r'))

# convert string to list
list_of_csv = list(csv_reader)


def setup_chrome():
    site = 'https://www.dell.com/support/home/en-us'
    # set the driver
    driver = webdriver.Chrome()

    # load this site
    driver.get(site)
    return driver


def checkDell(driver, sn):  # TODO return boolean status and date
    sleep(1)
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
        return False, True
    elif "Expires" in element_text:  # TODO include prosupport
        return True, True


# make runable
if __name__ == '__main__':
    driver = setup_chrome()

    total_check = 0  # TEMP check how many assets we've checked
    start_time = datetime.now()

    # iterate through csv, calling checkDell
    i = 1
    # selenium will occaisionally outpace itself and input a second serial number into search box
    # catch this by checking for search failure. If search fails, interator does not increase and loop continues at same line
    # fail_count tracks failures per line. if search failures multiple times, improper serial number data likely present
    fail_count = 0
    while i < len(list_of_csv):
        in_warranty, check_successful = checkDell(driver, list_of_csv[i][8])
        if check_successful:  # yay, save warranty status and date TODO: save warranty status and date
            print(str(i) + " " + str(in_warranty))
            i += 1
            fail_count = 0
            total_check += 1
        elif fail_count < 3:  # notate failure, try again
            fail_count += 1
        else:  # too many failures, skip entry
            fail_count = 0
            i += 1
            total_check += 1

    end_time = datetime.now()

    print("# of assets: " + str(total_check) + "  start: " +
          str(start_time) + "  end: " + str(end_time))
    driver.quit()
