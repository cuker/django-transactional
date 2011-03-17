import logging
import threading
from django.db import transaction as db_transaction

from session import TransactionSession

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

class BaseTransactionMiddleware(object):
    local = threading.local() #uses a shared context within the thread
    
    def set_handler(self, handler):
        self.handler = handler
    
    @property
    def session(self):
        return getattr(self.local, 'session', None)
    
    def enter(self):
        if not self.session:
            self.local.session = TransactionSession()
    
    def leave(self):
        pass
    
    def commit(self):
        for action in self.session.pop_save_point():
            self.perform_action(action)
    
    def rollback(self):
        for action in self.session.pop_save_point():
            self.rollback_action(action)
    
    def managed(self, flag):
        pass
    
    def savepoint_enter(self, savepoint):
        self.session.add_save_point(savepoint)
    
    def savepoint_rollback(self, savepoint):
        for action in self.session.pop_save_point(savepoint):
            self.rollback_action(action)
    
    def savepoint_commit(self, savepoint):
        for action in self.session.pop_save_point(savepoint):
            self.perform_action(action)
    
    def get_active_save_point(self):
        return self.session.tail()
    
    def perform_action(self, action):
        pass
    
    def rollback_action(self, action):
        pass
    
    def record_action(self, action):
        if self.handler.is_managed():
            self.session.record_action(action)
        else:
            self.perform_action(action)

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
        return super(LoggingTransactionMiddleware, self).commit()
    
    def rollback(self):
        self.logger.debug('rollback')
        return super(LoggingTransactionMiddleware, self).rollback()
    
    def managed(self, flag):
        self.logger.debug('Set managed: %s' % flag)
    
    def savepoint_enter(self, savepoint):
        self.logger.debug('Save point enter: %s' % savepoint)
        super(LoggingTransactionMiddleware, self).savepoint_enter(savepoint)
    
    def savepoint_rollback(self, savepoint):
        self.logger.debug('Save point rollback: %s' % savepoint)
        return super(LoggingTransactionMiddleware, self).savepoint_rollback(savepoint)
    
    def savepoint_commit(self, savepoint):
        self.logger.debug('Save point commit: %s' % savepoint)
        return super(LoggingTransactionMiddleware, self).savepoint_commit(savepoint)
    
    def perform_action(self, action):
        self.logger.info('Performed: %s' % action)
    
    def rollback_action(self, action):
        self.logger.info('Rollbacked: %s' % action)

