import logging
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

class LoggingTransactionMiddleware(object):
    def __init__(self, logger=None):
        if not logger:
            logger = logging
        self.logger = logger
    
    def enter(self):
        self.logger.debug('Entering transaction management')
    
    def leave(self):
        self.logger.debug('Leaving transaction management')
    
    def commit(self):
        self.logger.debug('commit')
    
    def rollback(self):
        self.logger.debug('rollback')
    
    def managed(self, flag):
        self.logger.debug('Set managed: %s' % flag)
    
    def savepoint_enter(self, savepoint):
        self.logger.debug('Save point enter: %s' % savepoint)
    
    def savepoint_rollback(self, savepoint):
        self.logger.debug('Save point rollback: %s' % savepoint)
    
    def savepoint_commit(self, savepoint):
        self.logger.debug('Save point commit: %s' % savepoint)
