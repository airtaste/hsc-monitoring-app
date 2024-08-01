from selenium.common import NoSuchElementException

from captcha.captcha_resolver import CaptchaResolver
from config.configuration import CAPTCHA_GUARD_MAX_RETRIES


def perform_with_captcha_guard(captcha_resolver: CaptchaResolver, retry_count: int, func: callable, **kwargs):
    if retry_count > CAPTCHA_GUARD_MAX_RETRIES:
        raise Exception(
            "Error during function execution. Seems like element cannot be found event after captcha solving."
        )

    if captcha_resolver.has_captcha():
        captcha_resolver.resolve_captcha()

    try:
        func(**kwargs)
    except NoSuchElementException:
        perform_with_captcha_guard(captcha_resolver, func, retry_count + 1)
