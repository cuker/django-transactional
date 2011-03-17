import threading
import random

from django.core import exceptions
from django.utils.importlib import import_module
from django.utils.datastructures import SortedDict

import settings

def initialize_middleware(paths=None):
    middlewares = SortedDict()
    if paths is None:
        paths = settings.TRANSACTIONAL_MIDDLEWARE
    for middleware_path in paths:
        kwargs = {}
        args = []
        if isinstance(middleware_path, (tuple, list)):
            middleware_path, args, kwargs = middleware_path
        try:
            dot = middleware_path.rindex('.')
        except ValueError:
            raise exceptions.ImproperlyConfigured('%s isn\'t a middleware module' % middleware_path)
        mw_module, mw_classname = middleware_path[:dot], middleware_path[dot+1:]
        try:
            mod = import_module(mw_module)
        except ImportError, e:
            raise exceptions.ImproperlyConfigured('Error importing middleware %s: "%s"' % (mw_module, e))
        try:
            mw_class = getattr(mod, mw_classname)
        except AttributeError:
            raise exceptions.ImproperlyConfigured('Middleware module "%s" does not define a "%s" class' % (mw_module, mw_classname))

        if callable(mw_class):
            try:
                mw_instance = mw_class(*args, **kwargs)
            except exceptions.MiddlewareNotUsed:
                continue
        else:
            mw_instance = mw_class
        middlewares[middleware_path] = mw_instance
    return middlewares

class TransactionalManager(object):
    def __init__(self, paths=None):
        self.middleware = initialize_middleware(paths)
        self.local = threading.local()
    
    def _proxy_call(self, attr, *args, **kwargs):
        for middleware in self.middleware.itervalues():
            if hasattr(middleware, attr):
                getattr(middleware, attr)(*args, **kwargs)
    
    def get_savepoints(self):
        return getattr(self.local, 'savepoints', [])
    
    def enter(self, flag=False):
        self._proxy_call('enter')
        self.managed(flag)
    
    def leave(self):
        self._proxy_call('leave')
    
    def commit(self):
        self._proxy_call('commit')
    
    def rollback(self):
        self._proxy_call('rollback')
    
    def is_managed(self):
        """
        Checks whether the transaction manager is in manual or in auto state.
        """
        return getattr(self.local, 'managed', False)
    
    def managed(self, value):
        self.local.managed = value
        self._proxy_call('managed', value)
    
    def savepoint_enter(self):
        if not hasattr(self.local, 'savepoints'):
            self.local.savepoints = list()
        savepoint = {'_id': random.random()}
        self.local.savepoints.append(savepoint)
        self._proxy_call('savepoint_enter', savepoint)
        return savepoint
    
    def savepoint_rollback(self, savepoint):
        self._proxy_call('savepoint_exit', savepoint)
    
    def savepoint_commit(self, savepoint):
        self._proxy_call('savepoint_commit', savepoint)
    
    def commit_unless_managed(self):
        """
        Commits changes if the system is not in managed transaction mode.
        """
        if not self.is_managed():
            self.commit()
    
    def rollback_unless_managed(self):
        """
        Rolls back changes if the system is not in managed transaction mode.
        """
        if not self.is_managed():
            self.rollback()
    
    def get_active_save_point(self, path):
        return self.middleware[path].get_active_save_point()

transactional_manager = TransactionalManager()


def enter_transaction_management(managed=True):
    transactional_manager.enter_transaction_management()
    if managed:
        transactional_manager.managed(managed)

def leave_transaction_management():
    transactional_manager.leave_transaction_management()

def is_managed():
    return transactional_manager.is_managed()

def managed(flag=True):
    return transactional_manager.managed(flag)

def commit_unless_managed():
    transactional_manager.commit_unless_managed()

def rollback_unless_managed():
    transactional_manager.rollback_unless_managed()

def commit():
    transactional_manager.commit()

def rollback():
    transactional_manager.rollback()

def savepoint():
    """
    Creates a savepoint (if supported and required by the backend) inside the
    current transaction. Returns an identifier for the savepoint that will be
    used for the subsequent rollback or commit.
    """
    return transactional_manager.savepoint()

def savepoint_rollback(sid):
    """
    Rolls back the most recent savepoint (if one exists). Does nothing if
    savepoints are not supported.
    """
    transactional_manager.savepoint_rollback(sid)

def savepoint_commit(sid):
    """
    Commits the most recent savepoint (if one exists). Does nothing if
    savepoints are not supported.
    """
    transactional_manager.savepoint_commit(sid)


