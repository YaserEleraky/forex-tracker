class ForexError(Exception):
    """
    قاعدة لجميع استثناءات تطبيق Forex Tracker.
    Base class for all exceptions in the Forex Tracker application.
    """

    pass


class ConfigError(ForexError):
    """
    استثناء يحدث عند وجود مشكلة في تهيئة الإعدادات.
    Exception raised when there is an issue with configuration initialization.
    """

    pass


class StorageError(ForexError):
    """
    استثناء يحدث عند وجود مشكلة في تخزين البيانات.
    Exception raised when there is an issue with data storage.
    """

    pass


class APIError(ForexError):
    """
    استثناء يحدث عند وجود مشكلة في تهيئة الواجهة البرمجية.
    Exception raised when there is an issue with API initialization.
    """

    pass


class ValidationError(ForexError):
    """
    استثناء يحدث عند وجود خطأ في التحقق من صحة البيانات.
    Exception raised when there is a data validation error.
    """

    pass


class NetworkError(ForexError):
    """
    استثناء يحدث عند وجود مشكلة في الشبكة أو الاتصال.
    Exception raised when there is a network or connection issue.
    """

    pass
