# WebscraperV3
Setting up the Credentials File
To use the web scraper, you'll need to create a credentials file and provide your username and password. The credentials file should be named credentials.py and should contain the following variables:

Copy code

USERNAME = "your_username"
PASSWORD = "your_password"
Replace your_username and your_password with your actual login credentials.

Running the Web Scraper
Ensure you have the necessary dependencies installed, such as Selenium and the appropriate web driver for your browser.
Run the main script of the web scraper.
The script will automatically log you in to the website using the credentials provided in the credentials.py file.
After logging in, you'll need to complete the Duo authentication process manually.
The script will then navigate to the first page and if you want to adjust the number of rows you wish to transcribe then just change the for loop numbers.
By default, it will transcribe 60(59,-1,-1) rows (a whole page).
If you need to transcribe a specific page, you can adjust the timer before the main loop to give yourself time to navigate to the desired page once you reach the organization tab.
The results of the web scraping will be saved to the Google Sheets "Algo Inventory (T)" sheet.
