try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.4 fallback.

from handler import transactional_manager

#TODO allow specification of transactional middlewares

def autocommit():
    """
    Decorator that activates commit on save. This is Django's default behavior;
    this decorator is useful if you globally activated transaction management in
    your settings file and want the default behavior in some view functions.
    """
    def inner_autocommit(func):
        def _autocommit(*args, **kw):
            try:
                transactional_manager.enter_transaction_management(managed=False)
                transactional_manager.managed(False)
                return func(*args, **kw)
            finally:
                transactional_manager.leave_transaction_management()
        return wraps(func)(_autocommit)
    return lambda func: inner_autocommit(func)


def commit_on_success():
    """
    This decorator activates commit on response. This way, if the view function
    runs successfully, a commit is made; if the viewfunc produces an exception,
    a rollback is made. This is one of the most common ways to do transaction
    control in Web apps.
    """
    def inner_commit_on_success(func):
        def _commit_on_success(*args, **kw):
            try:
                transactional_manager.enter_transaction_management()
                transactional_manager.managed(True)
                try:
                    res = func(*args, **kw)
                except:
                    # All exceptions must be handled here (even string ones).
                    transactional_manager.rollback()
                    raise
                else:
                    try:
                        transactional_manager.commit()
                    except:
                        transactional_manager.rollback()
                        raise
                return res
            finally:
                transactional_manager.leave_transaction_management()
        return wraps(func)(_commit_on_success)
    return lambda func: inner_commit_on_success(func)

def commit_manually():
    """
    Decorator that activates manual transaction control. It just disables
    automatic transaction control and doesn't do any commit/rollback of its
    own -- it's up to the user to call the commit and rollback functions
    themselves.
    """
    def inner_commit_manually(func):
        def _commit_manually(*args, **kw):
            try:
                transactional_manager.enter_transaction_management()
                transactional_manager.managed(True)
                return func(*args, **kw)
            finally:
                transactional_manager.leave_transaction_management()

        return wraps(func)(_commit_manually)
    return lambda func: inner_commit_manually(func)

