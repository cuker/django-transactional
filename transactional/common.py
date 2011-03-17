from handler import TransactionalManagerContext, TransactionalManager

transactional_manager = TransactionalManagerContext.get_active_context

def enter_transaction_management(managed=True):
    transactional_manager().enter_transaction_management()
    if managed:
        transactional_manager().managed(managed)

def leave_transaction_management():
    transactional_manager().leave_transaction_management()

def is_managed():
    return transactional_manager().is_managed()

def managed(flag=True):
    return transactional_manager().managed(flag)

def commit_unless_managed():
    transactional_manager().commit_unless_managed()

def rollback_unless_managed():
    transactional_manager().rollback_unless_managed()

def commit():
    transactional_manager().commit()

def rollback():
    transactional_manager().rollback()

def savepoint():
    """
    Creates a savepoint (if supported and required by the backend) inside the
    current transaction. Returns an identifier for the savepoint that will be
    used for the subsequent rollback or commit.
    """
    return transactional_manager().savepoint()

def savepoint_rollback(sid):
    """
    Rolls back the most recent savepoint (if one exists). Does nothing if
    savepoints are not supported.
    """
    transactional_manager().savepoint_rollback(sid)

def savepoint_commit(sid):
    """
    Commits the most recent savepoint (if one exists). Does nothing if
    savepoints are not supported.
    """
    transactional_manager().savepoint_commit(sid)

def record_action(path, action, treat_nonregistered_as_non_managed=True):
    ret = transactional_manager().record_action(path, action)
    if not ret and treat_nonregistered_as_non_managed:
        manager = TransactionalManager([path])
        manager.managed(False)
        ret = manager.record_action(path, action)
        assert ret
    return ret
