# py-sn-webscraper
A Python web scraper that automates the process of checking a list of serial numbers against Dell's warranty page. The script is designed to run slowly to avoid overloading the target site with requests.

How it Works
The script uses the Selenium library to:
  1. Loop through a list of serial numbers from a spreadsheet.
  
  2. Navigate to Dell's Warranty Check page.
  
  3. Input each serial number and submit the search.
  
  4. Extract and print the warranty results.

The ultimate goal of this project was to expand the functionality to include other Original Equipment Manufacturer (OEM) websites and save the collected data to a spreadsheet.

⚠️ **Ethics Note**
  Please be aware that web scraping, even at a low volume, may violate the Terms of Service (TOS) of certain websites. This repository is intended for personal development and educational purposes. It is not recommended to use this script without express permission from the target site owner.
