import logging
import threading
from django.db import transaction as db_transaction

class DatabaseTransactionMiddleware(object):
    def __init__(self, using=None):
        self.using = using
    
    def enter(self):
        db_transaction.enter_transaction_management(using=self.using)
    
    def leave(self):
        if db_transaction.is_dirty():
            db_transaction.rollback()
        db_transaction.leave_transaction_management(using=self.using)
    
    def commit(self):
        db_transaction.commit(using=self.using)
    
    def rollback(self):
        db_transaction.rollback(using=self.using)
    
    def managed(self, flag):
        db_transaction.managed(flag)
    
    
    def savepoint_enter(self, savepoint):
        sid = db_transaction.savepoint(using=self.using)
        savepoint['db_sid'] = sid
    
    def savepoint_rollback(self, savepoint):
        db_transaction.savepoint_rollback(savepoint['db_sid'], using=self.using)
    
    def savepoint_commit(self, savepoint):
        db_transaction.savepoint_commit(savepoint['db_sid'], using=self.using)

class TransactionSavePoint(object):
    def __init__(self, parent=None, info=None):
        self.actions = list()
        self.child = None
        self.parent = parent
        self.info = info
    
    def record_action(self, obj):
        self.actions.append(obj)
        if self.child:
            self.child.record_action(obj)
    
    def flush(self):
        actions = self.actions
        self.actions = list()
        if self.child:
            self.child.flush()
        return actions
    
    def find_save_point(self, info):
        if self.info == info:
            return self
        if self.child:
            return self.child.find_save_point(info)
    
    def tail(self):
        if self.child:
            return self.child.tail()
        return self
    
    def unlink(self):
        if self.parent:
            self.parent.child = None

class TransactionSession(object):
    def __init__(self, save_point_class=TransactionSavePoint):
        self.save_point_class = save_point_class
        self.root_save_point = self.save_point_class()
    
    def add_save_point(self, info=None):
        tail = self.root_save_point.tail()
        child = self.save_point_class(parent=tail, info=info)
        tail.child = child
        return child
    
    def pop_save_point(self, info=None):
        if info is None:
            self.root_save_point.child = None
            return self.root_save_point.flush()
        result = self.root_save_point.find_save_point(info)
        result.unlink()
        return result.flush()
    
    def tail(self):
        return self.root_save_point.tail()

class BaseTransactionMiddleware(object):
    def __init__(self):
        self.local = threading.local()
    
    @property
    def session(self):
        return getattr(self.local, 'session', None)
    
    def enter(self):
        self.local.session = TransactionSession()
    
    def leave(self):
        pass
    
    def commit(self):
        return self.session.pop_save_point()
    
    def rollback(self):
        return self.session.pop_save_point()
    
    def managed(self, flag):
        pass
    
    def savepoint_enter(self, savepoint):
        self.session.add_save_point(savepoint)
    
    def savepoint_rollback(self, savepoint):
        return self.session.pop_save_point(savepoint)
    
    def savepoint_commit(self, savepoint):
        return self.session.pop_save_point(savepoint)
    
    def get_active_save_point(self):
        return self.session.tail()

class LoggingTransactionMiddleware(BaseTransactionMiddleware):
    def __init__(self, logger=None):
        if logger is None:
            logger = logging
        self.logger = logger
        super(LoggingTransactionMiddleware, self).__init__()
    
    def enter(self):
        self.logger.debug('Entering transaction management')
        super(LoggingTransactionMiddleware, self).enter()
    
    def leave(self):
        self.logger.debug('Leaving transaction management')
        super(LoggingTransactionMiddleware, self).leave()
    
    def commit(self):
        self.logger.debug('commit')
        for item in super(LoggingTransactionMiddleware, self).commit():
            self.logger.info(str(item))
    
    def rollback(self):
        self.logger.debug('rollback')
        for item in super(LoggingTransactionMiddleware, self).rollback():
            self.logger.info(str(item))
    
    def managed(self, flag):
        self.logger.debug('Set managed: %s' % flag)
    
    def savepoint_enter(self, savepoint):
        self.logger.debug('Save point enter: %s' % savepoint)
        super(LoggingTransactionMiddleware, self).savepoint_enter(savepoint)
    
    def savepoint_rollback(self, savepoint):
        self.logger.debug('Save point rollback: %s' % savepoint)
        for item in super(LoggingTransactionMiddleware, self).savepoint_rollback(savepoint):
            self.logger.info(str(item))
    
    def savepoint_commit(self, savepoint):
        self.logger.debug('Save point commit: %s' % savepoint)
        for item in super(LoggingTransactionMiddleware, self).savepoint_commit(savepoint):
            self.logger.info(str(item))

