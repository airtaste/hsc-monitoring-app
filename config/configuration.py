# Telegram bot token, you could find it after bot creation via @BotFather
TELEGRAM_BOT_TOKEN_ID = ''
# Telegram chat_id (should be your chat_id identifier to allow notifier send you a message
CHAT_ID = ''
# Basically its HSC office identifier that persists inside system
HSC_OFFICE_ID_LVIV = 61
# Delay range for search attempt
DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS = (240, 600)
# Delay range for particular day monitoring attempt
DELAYS_BETWEEN_DAY_MONITORING_SECONDS = (5, 10)
# Time for authentication process, after exceeding this you would probably need to perform re-auth
AUTH_TIMER_THRESHOLD_SECONDS = 600
# Automatic re-auth time in seconds, after exceeding this you would logout from system
REAUTH_TIME_WINDOW_SECONDS = 14400
CAPTCHA_GUARD_MAX_RETRIES = 5
CAPTCHA_SOLVE_RETRY_THRESHOLD = 10
