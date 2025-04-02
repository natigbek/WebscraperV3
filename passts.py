from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import gspread
from google.oauth2.service_account import Credentials
import time
import logging
from credentials import AGOL_USERNAME, AGOL_PASSWORD
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AGOLScraper:
    def __init__(self, credentials_path: str, sheet_name: str):
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.sheet = self._initialize_sheets()
        self.driver = None

    def _initialize_sheets(self):
        """Initialize Google Sheets connection."""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scope
            )
            client = gspread.authorize(creds)
            sheet = client.open(self.sheet_name).sheet1
            logger.info("Successfully connected to Google Sheets")
            return sheet
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise

    def _setup_webdriver(self):
        """Initialize and configure webdriver."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
    
    def _login(self, username: str, password: str):
        """Handle the login process."""
        try:
            # Navigate to login page
            self.driver.get("https://vanderbilt.maps.arcgis.com/home/signin.html")
            time.sleep(2)

            # Click Vanderbilt login button
            vanderbilt_login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".js-entpanel"))
            )
            vanderbilt_login_button.click()
            logger.info("Clicked Vanderbilt login button")
            time.sleep(3)

            # Handle username input
            input_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            self.driver.execute_script(
                "arguments[0].focus(); arguments[0].value = arguments[1];", 
                input_field, 
                username
            )
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", 
                input_field
            )
            logger.info("Entered username")
            
            # Click Next using multiple methods
            self._try_click_button("postButton", "ping-button normal allow", "Next")
            time.sleep(5)

            # Handle password input
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            self.driver.execute_script(
                "arguments[0].focus(); arguments[0].value = arguments[1];", 
                password_field, 
                password
            )
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", 
                password_field
            )
            logger.info("Entered password")

            # Click Submit using multiple methods
            self._try_click_button("postButton", "ping-button normal allow", "Submit")
            time.sleep(5)

            # Handle Duo device trust prompt
            logger.info("Waiting for device trust prompt (60 seconds)...")
            try:
                dont_trust_button = WebDriverWait(self.driver, 60).until(
                    EC.element_to_be_clickable((By.ID, "dont-trust-browser-button"))
                )
                dont_trust_button.click()
                logger.info("Clicked 'No, other people use this device' button")
                time.sleep(2)
            except TimeoutException:
                logger.warning("Device trust button not found or timed out")

            # Navigate to content
            self._navigate_to_content()

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.driver.save_screenshot("login_error.png")
            raise

    def _try_click_button(self, button_id: str, button_class: str, button_text: str):
        """Try multiple methods to click a button."""
        clicked = False
        
        # Method 1: By ID
        try:
            button_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, button_id))
            )
            button = button_div.find_element(By.TAG_NAME, "a")
            button.click()
            clicked = True
            logger.info(f"Clicked {button_text} button by ID")
        except Exception:
            pass

        # Method 2: JavaScript
        if not clicked:
            try:
                self.driver.execute_script("postOk();")
                clicked = True
                logger.info(f"Clicked {button_text} button by JavaScript")
            except Exception:
                pass

        # Method 3: CSS Selector
        if not clicked:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"a.{button_class}"))
                )
                button.click()
                clicked = True
                logger.info(f"Clicked {button_text} button by CSS selector")
            except Exception:
                pass

        # Method 4: Text content
        if not clicked:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{button_text}')]"))
                )
                button.click()
                logger.info(f"Clicked {button_text} button by text content")
            except Exception:
                logger.warning(f"Could not click {button_text} button")

    def _navigate_to_content(self):
        """Navigate to the content page."""
        try:
            # Click Content button
            content_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "esri-header-menus-link-desktop-0-5"))
            )
            content_button.click()
            logger.info("Clicked Content button")
            time.sleep(5)

            # Click Org button
            org_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "calcite-menu-item[data-id='org']"))
            )
            org_button.click()
            logger.info("Clicked Org button")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Failed to navigate to content: {e}")
            raise
        
    def _click_preview_button(self,counter= 1):
        """Click the Preview button on the first row using shadow DOM traversal."""
        try:
            # Adjust the XPath to wait for the row based on the counter
                # Try a more aggressive approach - find any button with 'Preview' text
            alt_script = f"""
                    const rows = document.querySelectorAll('arcgis-item-browser-table-row');
                    let i = {counter};
                    // Start the loop from index 1 to skip the first row
                    if (i < rows.length) {{
                        const row = rows[i];
                        
                        if (!row.shadowRoot) return "Row has no shadow root";
                        
                        const buttons = row.shadowRoot.querySelectorAll('button');
                        for (let btn of buttons) {{
                            if (btn.textContent.trim() === 'Preview') {{
                                btn.click();
                                return "Found and clicked Preview button";
                            }}
                        }}
                    }}
                    return "No Preview button found in any row";
                """
                
            alt_result = self.driver.execute_script(alt_script)
            logger.info(f"Alternative shadow DOM script result: {alt_result}")
                
            if "found and clicked" in alt_result.lower():
                    logger.info("Successfully clicked Preview button with alternative method")
                    time.sleep(3)
                    return True
            else:
                    logger.error("All attempts to click Preview button failed")
                    return False    
                
        except Exception as e:
            logger.error(f"Error in _click_preview_button: {e}")
            return False

    def _get_element_text_through_shadow(self, script):
        """Execute JavaScript to traverse shadow DOM and get text."""
        try:
            result = self.driver.execute_script(script)
            return result.strip() if result else None
        except Exception as e:
            logger.error(f"Error executing shadow DOM script: {e}")
            return None

    def _extract_row_data(self):
        """Extract data using JavaScript shadow DOM traversal."""
        try:
            # Wait for the base row element
            base_xpath = "//arcgis-item-browser-table-row[1]"
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, base_xpath))
            )
            time.sleep(2)  # Add small delay to ensure shadow DOM is fully loaded
            
            # JavaScript scripts for each field
            scripts = {
                'title': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;

                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;

                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;

                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;

                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item:nth-of-type(1)');
                    if (!flowItem) return null;

                    // Finally, find the h3 element within the first div
                    const heading = flowItem.querySelector('div:nth-of-type(1) h3');
                    return result = heading ? heading.textContent.trim() : null;
                """,
                'ID': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;

                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;

                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;

                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;

                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item');
                    if (!flowItem) return null;

                    // Navigate to the accordion
                    const accordion = flowItem.querySelector('calcite-accordion');
                    if (!accordion) return null;

                    // Find the specific accordion item (the fifth one, as you mentioned item[4])
                    const accordionItem = accordion.querySelector('calcite-accordion-item:nth-of-type(4)');
                    if (!accordionItem) return null;

                    // Find the browser preview copy component
                    const browserPreviewCopy = accordionItem.querySelector('arcgis-item-browser-preview-copy');
                    if (!browserPreviewCopy) return null;

                    // Access its shadow DOM
                    const shadow2 = browserPreviewCopy.shadowRoot;
                    if (!shadow2) return null;

                    // Find the calcite-label
                    const calciteLabel = shadow2.querySelector('calcite-label');
                    if (!calciteLabel) return null;

                    // Find the calcite-input
                    const calciteInput = calciteLabel.querySelector('calcite-input');
                    if (!calciteInput) return null;

                    // Access the input's shadow DOM
                    const inputShadow = calciteInput.shadowRoot;
                    if (!inputShadow) return null;

                    // Find the input element
                    const inputElement = inputShadow.querySelector('input[aria-label="ID"]');
                    
                    // Return the value, trimming any whitespace
                    return inputElement ? inputElement.value.trim() : null;
                """,

                'type': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;

                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;

                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;

                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;

                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item:nth-of-type(1)');
                    if (!flowItem) return null;

                    // Find the item type component within the first div
                    const itemType = flowItem.querySelector('div:nth-of-type(1) arcgis-item-type');
                    if (!itemType) return null;

                    // Access its shadow DOM
                    const shadow2 = itemType.shadowRoot;
                    if (!shadow2) return null;

                    // Finally, find the text span
                    const typeSpan = shadow2.querySelector('span');
                    return result = typeSpan ? typeSpan.textContent.trim() : null;
                """,
                
                'last_updated': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;
                    
                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;
                    
                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;
                    
                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;
                    
                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item');
                    if (!flowItem) return null;
                    
                    // Navigate to the accordion
                    const accordion = flowItem.querySelector('calcite-accordion');
                    if (!accordion) return null;
                    
                    // Find the specific accordion item (the second one)
                    const accordionItem = accordion.querySelector('calcite-accordion-item:nth-of-type(2)');
                    if (!accordionItem) return null;

                    const paragraph = accordionItem.querySelector('div p:nth-of-type(2)');
                    return result = paragraph ? paragraph.textContent.trim() : null;
                """,

                'Owner': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;
                    
                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;
                    
                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;
                    
                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;
                    
                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item');
                    if (!flowItem) return null;
                    
                    // Navigate to the accordion
                    const accordion = flowItem.querySelector('calcite-accordion');
                    if (!accordion) return null;
                    
                    // Find the specific accordion item (the second one)
                    const accordionItem = accordion.querySelector('calcite-accordion-item:nth-of-type(2)');
                    if (!accordionItem) return null;

                    // Find the user popup component
                    const userPopup = accordionItem.querySelector('arcgis-user-popup');
                    if (!userPopup) return null;

                    // Access its shadow DOM
                    const shadow2 = userPopup.shadowRoot;
                    if (!shadow2) return null;

                    // Find the button within the user popup
                    const button = shadow2.querySelector('button');
                    if (!button) return null;

                    // Navigate to the slot within the button
                    const slot = button.querySelector('slot');
                    if (!slot) return null;

                    // Find the user avatar component within the slot
                    const userAvatar = slot.querySelector('arcgis-user-avatar');
                    if (!userAvatar) return null;

                    // Access its shadow DOM
                    const shadow3 = userAvatar.shadowRoot;
                    if (!shadow3) return null;

                    // Finally, find the span within the user avatar component
                    const avatarSpan = shadow3.querySelector('span span');
                    return result = avatarSpan ? avatarSpan.textContent.trim() : null;
                """,

                'Sharing': """
                    // Start at the browser component
                    const browsers = document.querySelector('arcgis-browser, arcgis-item-browser');
                    if (!browsers) return null;
                    
                    // Access its shadow DOM
                    const browser = browsers.shadowRoot;
                    if (!browser) return null;

                    // Find the preview component
                    const preview = browser.querySelector('arcgis-item-browser-preview');
                    if (!preview) return null;
                    
                    // Access its shadow DOM
                    const shadow1 = preview.shadowRoot;
                    if (!shadow1) return null;
                    
                    // Navigate to the calcite-flow component
                    const calciteFlow = shadow1.querySelector('calcite-flow');
                    if (!calciteFlow) return null;
                    
                    // Find the first flow item
                    const flowItem = calciteFlow.querySelector('calcite-flow-item');
                    if (!flowItem) return null;
                    
                    // Navigate to the accordion
                    const accordion = flowItem.querySelector('calcite-accordion');
                    if (!accordion) return null;
                    
                    // Find the specific accordion item (the second one)
                    const accordionItem = accordion.querySelector('calcite-accordion-item:nth-of-type(2)');
                    if (!accordionItem) return null;
                    
                    // Find the share summary component
                    const shareSummary = accordionItem.querySelector('arcgis-item-share-summary');
                    if (!shareSummary) return null;
                    
                    // Access its shadow DOM
                    const shadow2 = shareSummary.shadowRoot;
                    if (!shadow2) return null;
                    
                    // Finally, find the text span
                    const locationSpan = shadow2.querySelector('div span.text');
                    const result = locationSpan ? locationSpan.textContent.trim() : null;
                    // Return "Public" if the result is "Everyone (public)"
                    return result === "Everyone (public)" ? "Public" : result;               
                """
            }

            # Extract data
            data = {}
            for field, script in scripts.items():
                try:
                    value = self._get_element_text_through_shadow(script)
                    if value:
                        data[field] = value
                        logger.info(f"Found {field}: {value}")
                    else:
                        logger.error(f"No value found for {field}")
                        data[field] = None
                except Exception as e:
                    logger.error(f"Error extracting {field}: {e}")
                    data[field] = None

            # Create row data array
            row_data = [
                data.get('title'),
                data.get('ID'),
                data.get('type'),
                data.get('Owner'),
                data.get('Sharing'),
                data.get('last_updated')
            ]

            logger.info(f"Extracted row data: {row_data}")
            return row_data

        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            self.driver.save_screenshot(f"extraction_error_{time.time()}.png")
            return None

    def run(self, username: str, password: str):
        """Main method to run the scraper."""
        try:
            self._setup_webdriver()
            self._login(username, password)
            time.sleep(35)
            for i in range(59, -1, -1):
                self._click_preview_button(i)
                # Wait for content to load
                time.sleep(5)
                
                # Extract data from the first row
                logger.info("Processing first row")
                row_data = self._extract_row_data()
                
                if row_data:
                    logger.info("Attempting to save to Google Sheets")
                    try:
                        self.sheet.append_row(row_data)
                        logger.info("Successfully saved to Google Sheets")
                    except Exception as e:
                        logger.error(f"Failed to save to Google Sheets: {e}")
            
        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            self.driver.save_screenshot("error.png")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = AGOLScraper(
        credentials_path='webscrapper-451218-e78f0e8c5073.json',
        sheet_name="AGOL Inventory(t)"
    )
    scraper.run(
        username=AGOL_USERNAME,
        password=AGOL_PASSWORD
    )