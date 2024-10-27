# Telegram bot token, you could find it after bot creation via @BotFather
TELEGRAM_BOT_TOKEN_ID = 'YOUR_BOT_TOKEN_ID'
# Telegram chat_id (should be your chat_id numeric identifier to allow notifier send you a message)
CHAT_ID = None
# Allow list of telegram chat_ids, who can interact with bot. Only numeric values.
ALLOW_LIST = []
# Basically its HSC office identifier that persists inside system
HSC_OFFICE_ID = None
# Delay range for search attempt
DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS = (60, 120)
# Delay range for particular day monitoring attempt
DELAYS_BETWEEN_DAY_MONITORING_SECONDS = (3, 5)
# Delay before reservation starts
DELAY_BEFORE_RESERVATION_SECONDS = (1, 3)
# Time for authentication process, after exceeding this you would probably need to perform re-auth
AUTH_TIMER_THRESHOLD_SECONDS = 600
# Automatic re-auth time in hours, after exceeding this you would logout from system
REAUTH_THRESHOLD_HOURS = 5
# Count of retries for captcha solving
CAPTCHA_SOLVE_RETRY_THRESHOLD = 5
# Count of retries for slot approval
APPROVE_RESERVATION_RETRY_THRESHOLD = 20
# The start date for search. Could be optional. None by default.
START_FROM_DATE = None
# Two captcha service API key
TWOCAPTCHA_API_KEY = 'YOUR_TWO_CAPTCHA_API_KEY'
# HSC site key for recaptcha (could be found inside HTML document of the site, should be constant across all clients)
HSC_SITE_KEY = '6LcB0uQpAAAAALf4UuMsrkL3eYWGIcBrrVu__Y8T'
# Count of authentication retries
AUTH_RETRY_THRESHOLD = 5
# Flag to define if GUI for browser should be disabled (false by default)
HEADLESS_MODE = False
# Mode of authentication. Possible values is: BANK_ID, EUID.
AUTHENTICATOR_MODE = 'BANK_ID'
# Authentication key file path
EUID_KEY_PATH = 'euid/Key-6'
# Password for euid key (confidential information)
EUID_KEY_PASSWORD = ''
# Folder name for saved screenshots
SCREENSHOTS_FOLDER = 'screenshots'
# Folder name for downloaded files
BROWSER_DOWNLOADS_FOLDER = 'downloads'
# HSC office location that would be used during slot reservation (in action with map)
HSC_OFFICE_LOCATION = {
    'latitude': 50.442311,
    'longitude': 30.367196,
    'accuracy': 200
}
# Email for slot notification after approval
USER_EMAIL = 'YOUR_EMAIL_HERE'
