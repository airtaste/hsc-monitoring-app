from selenium.common import NoSuchElementException

from captcha.captcha_resolver import CaptchaResolver
from config.configuration import CAPTCHA_GUARD_MAX_RETRIES


def perform_with_captcha_guard(captcha_resolver: CaptchaResolver, retry_count: int, func: callable, **kwargs):
    if retry_count > CAPTCHA_GUARD_MAX_RETRIES:
        raise NoSuchElementException()

    if captcha_resolver.has_captcha():
        captcha_resolver.resolve_captcha()

    try:
        func(**kwargs)
    except NoSuchElementException:
        raise
    except Exception:
        perform_with_captcha_guard(captcha_resolver, retry_count + 1, func)
