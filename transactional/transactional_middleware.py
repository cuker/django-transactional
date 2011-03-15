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
    
    
    def savepoint_enter(self, savepoint):
        sid = db_transaction.savepoint(using=self.using)
        savepoint['db_sid'] = sid
    
    def savepoint_rollback(self, savepoint):
        db_transaction.savepoint_rollback(savepoint['db_sid'], using=self.using)
    
    def savepoint_commit(self, savepoint):
        db_transaction.savepoint_commit(savepoint['db_sid'], using=self.using)
