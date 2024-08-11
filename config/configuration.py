# Telegram bot token, you could find it after bot creation via @BotFather
TELEGRAM_BOT_TOKEN_ID = ''
# Telegram chat_id (should be your chat_id identifier to allow notifier send you a message
CHAT_ID = ''
# Basically its HSC office identifier that persists inside system
HSC_OFFICE_ID = 61
# Delay range for search attempt
DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS = (60, 120)
# Delay range for particular day monitoring attempt
DELAYS_BETWEEN_DAY_MONITORING_SECONDS = (3, 5)
# Time for authentication process, after exceeding this you would probably need to perform re-auth
AUTH_TIMER_THRESHOLD_SECONDS = 600
# Automatic re-auth time in hours, after exceeding this you would logout from system
REAUTH_THRESHOLD_HOURS = 3
# Count of retries for captcha solving
CAPTCHA_SOLVE_RETRY_THRESHOLD = 5
# Count of retries for slot approval
APPROVE_RESERVATION_RETRY_THRESHOLD = 20
# Two captcha service API key
TWOCAPTCHA_API_KEY = ''
# HSC site key for recaptcha (could be found inside HTML document of the site, should be constant across all clients)
HSC_SITE_KEY = '6LcB0uQpAAAAALf4UuMsrkL3eYWGIcBrrVu__Y8T'
# Count of authentication retries
AUTH_RETRY_THRESHOLD = 5
# Days delta to start searching from starting from today (e.g. 4 would mean that you will start searching from 'today + 4 days')
MONITORING_DATE_RANGE_START_FROM_DELTA = 3
# Days to define date range for monitoring slots on exam
MONITORING_DATE_RANGE_DAYS = 18
# Flag to define if GUI for browser should be disabled (false by default)
HEADLESS_MODE = False
# Mode of authentication. Possible values is: BANK_ID, EUID.
AUTHENTICATOR_MODE = 'EUID'
# Authentication key file path
EUID_KEY_PATH = "euid/Key-6"
# Password for euid key (confidential information)
EUID_KEY_PASSWORD = ''
# Folder name for saved screenshots
SCREENSHOTS_FOLDER = "screenshots"
# Folder name for downloaded files
BROWSER_DOWNLOADS_FOLDER = "downloads"
# HSC office location that would be used during slot reservation (in action with map)
HSC_OFFICE_LOCATION = {
    "latitude": 49.829620,
    "longitude": 23.941710,
    "accuracy": 200
}
