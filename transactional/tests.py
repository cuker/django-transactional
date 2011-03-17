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
            self.assertTrue(message in seen, '%s not in %s' % (message, seen))
    
    def assert_not_log(self, *messages):
        for message in messages:
            self.assertTrue(message not in self.handler.messages)
    
    def record_action(self, action):
        self.transactional_manager.record_action('transactional.transactional_middleware.LoggingTransactionMiddleware', action)

    def test_transactional_manager(self):
        self.transactional_manager.activate_context()
        self.transactional_manager.enter()
        self.transactional_manager.managed(True)
        self.assert_log('Entering transaction management')
        self.record_action('foo')
        middleware = self.transactional_manager.middleware['transactional.transactional_middleware.LoggingTransactionMiddleware']
        self.assertEqual(1, len(middleware.session.actions))
        self.transactional_manager.commit()
        self.assertEqual(0, len(middleware.session.actions))
        self.assert_log('Performed: foo', 'commit')
        self.transactional_manager.rollback()
        self.transactional_manager.is_managed()
        
        self.record_action('level 1')
        sp = self.transactional_manager.savepoint_enter()
        self.record_action('level 2')
        self.transactional_manager.savepoint_commit(sp)
        self.assert_not_log('Performed: level 1')
        self.assert_log('Performed: level 2')
        
        sp = self.transactional_manager.savepoint_enter()
        self.record_action('level 3')
        self.transactional_manager.savepoint_rollback(sp)
        self.assert_log('Rollbacked: level 3')
        self.assert_not_log('Performed: level 1')
        
        self.transactional_manager.commit_unless_managed()
        self.assert_not_log('Performed: level 1')
        self.transactional_manager.commit()
        self.assert_log('Performed: level 1')
        self.transactional_manager.rollback_unless_managed()
        
        from common import record_action, commit
        record_action('transactional.transactional_middleware.LoggingTransactionMiddleware', 'foo')
        self.assert_not_log('Performed: foo')
        commit()
        self.assert_log('Performed: foo')
        
        self.transactional_manager.leave()
        self.transactional_manager.deactivate_context()

