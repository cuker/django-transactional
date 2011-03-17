import logging

from django.test import TestCase

from handler import TransactionalManager

class DummyHandler(logging.Handler):
    def __init__(self):
        self.messages = list()
        logging.Handler.__init__(self)
    
    def emit(self, record):
        self.messages.append(record.getMessage())

class TransactionalTest(TestCase):
    def setUp(self):
        logger = logging.getLogger('transactional_test')
        logger.setLevel(logging.DEBUG)
        self.handler = DummyHandler()
        logger.addHandler(self.handler)
        assert logger.isEnabledFor(logging.DEBUG)
        self.transactional_manager = TransactionalManager(['transactional.transactional_middleware.DatabaseTransactionMiddleware',
                                                           ('transactional.transactional_middleware.LoggingTransactionMiddleware', [logger], {})])

    def assert_log(self, *messages):
        seen = self.handler.messages
        self.handler.messages = list()
        for message in messages:
            self.assertTrue(message in seen)

    def test_transactional_manager(self):
        self.transactional_manager.enter()
        self.assert_log('Entering transaction management')
        save_point = self.transactional_manager.get_active_save_point('transactional.transactional_middleware.LoggingTransactionMiddleware')
        save_point.record_action('foo')
        self.assertEqual(1, len(save_point.actions))
        self.transactional_manager.commit()
        self.assertEqual(0, len(save_point.actions))
        self.assert_log('foo', 'commit')
        self.transactional_manager.rollback()
        self.transactional_manager.is_managed()
        
        sp = self.transactional_manager.savepoint_enter()
        self.transactional_manager.savepoint_commit(sp)
        
        sp = self.transactional_manager.savepoint_enter()
        self.transactional_manager.savepoint_rollback(sp)
        
        self.transactional_manager.commit_unless_managed()
        self.transactional_manager.rollback_unless_managed()
        
        self.transactional_manager.leave()
