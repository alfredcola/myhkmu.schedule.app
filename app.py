from flask import Flask, request, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)

# Simple HTML form template
LOGIN_FORM = '''
<!DOCTYPE html>
<html>
<head><title>HKMU Schedule Fetcher</title></head>
<body>
    <h1>HKMU Class Schedule</h1>
    <form method="POST">
        Username: <input type="text" name="username" required><br><br>
        Password: <input type="password" name="password" required><br><br>
        <input type="submit" value="Fetch Schedule">
    </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Your original Selenium setup (headless)
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)  # Ensure chromedriver.exe is in PATH or same dir

        try:
            # Login URL
            login_url = 'https://auth.hkmu.edu.hk/nidp/idff/sso?id=7&sid=0&option=credential&sid=0&target=https%3A%2F%2Fvip91prd.hkmu.edu.hk%2Fpsp%2Fp91prd%2F%3Fcmd%3Dlogin%26languageCd%3DENG'
            driver.get(login_url)
            time.sleep(0.5)

            # Fill form with user inputs
            driver.find_element(By.NAME, 'Ecom_User_ID').send_keys(username)
            driver.find_element(By.NAME, 'Ecom_Password').send_keys(password)
            driver.find_element(By.NAME, 'loginButton2').click()
            time.sleep(1)

            if 'errorCode' in driver.current_url:
                return "Login failed. Check credentials.", 401

            # Navigate to portal
            portal_url = 'https://vip91prd.hkmu.edu.hk/psp/p91prd/EMPLOYEE/EMPL/h/?tab=DEFAULT'
            driver.get(portal_url)
            time.sleep(1)

            # Click program link
            program_link = driver.find_element(By.XPATH, "//div[@class='PSEDITBOXLABEL']/a")
            program_link.click()
            time.sleep(1)

            # Open Classes & Enrolment dropdown
            enrolment_toggle = driver.find_element(By.XPATH, '//a[contains(@class, "nav-link dropdown-toggle") and contains(., "Classes & Enrolment")]')
            driver.execute_script("arguments[0].click();", enrolment_toggle)
            time.sleep(0.5)

            # Click Class Schedule (handle new tab)
            schedule_link = driver.find_element(By.XPATH, '//a[contains(@href, "SSR_SSENRL_LIST.GBL") and contains(., "Class Schedule")]')
            current_handle = driver.current_window_handle
            driver.execute_script("arguments[0].click();", schedule_link)
            time.sleep(0.5)

            all_handles = driver.window_handles
            if len(all_handles) > 1:
                new_handle = [h for h in all_handles if h != current_handle][0]
                driver.switch_to.window(new_handle)
                time.sleep(1)

            # Select latest term (2600) and continue
            latest_term_radio = driver.find_element(By.ID, "SSR_DUMMY_RECV1$sels$1$$0")
            driver.execute_script("arguments[0].click();", latest_term_radio)
            time.sleep(0.5)

            continue_button = driver.find_element(By.ID, "DERIVED_SSS_SCT_SSR_PB_GO")
            driver.execute_script("arguments[0].click();", continue_button)
            time.sleep(1)

            # Return the schedule HTML directly
            schedule_html = driver.page_source
            driver.quit()
            return schedule_html, 200, {'Content-Type': 'text/html'}

        except Exception as e:
            driver.quit()
            return f"Error: {str(e)}<br><a href='/'>Back</a>", 500

    return render_template_string(LOGIN_FORM)

if __name__ == '__main__':
    app.run(debug=True)
