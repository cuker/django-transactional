from handler import transactional_manager

class TransactionalMiddleware(object):
    """
    Transactional middleware. If this is enabled, each view function will be run
    with commit_on_response activated - that way a save() doesn't do a direct
    commit, the commit is done when a successful response is created. If an
    exception happens, then we roll back.
    """
    def process_request(self, request):
        """Enters transaction management"""
        transactional_manager.enter_transaction_management()
        transactional_manager.managed(True)

    def process_exception(self, request, exception):
        """Rolls back and leaves transaction management"""
        transactional_manager.leave_transaction_management()

    def process_response(self, request, response):
        """Commits and leaves transaction management."""
        if transactional_manager.is_managed():
            transactional_manager.leave_transaction_management()
        return response
