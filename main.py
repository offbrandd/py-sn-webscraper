from time import sleep
from datetime import datetime
import os

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

searching = False


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


def updateProgress(progress, total):
    os.system("clear")
    print(str(progress) + "/" + str(total) + "\n")
    percentage = progress / total
    bar_length = 50
    p = round(percentage * bar_length)
    s = "["
    for i in range(p):
        s += "#"
    for i in range(bar_length - p):
        s += "-"
    s += "]"
    print(s)


# make runable
if __name__ == "__main__":
    driver = setup_chrome()
    length = len(list_of_csv)

    # iterate through csv, calling checkDell
    i = 1
    while i < len(list_of_csv):
        updateProgress(i, length)
        list_of_csv[i][6] = checkDell(driver, list_of_csv[i][2])
        i += 1
    file = open("output.csv", "w+", newline="")

    with file:
        write = csv.writer(file)
        write.writerows(list_of_csv)
    print(list_of_csv)
    driver.quit()
