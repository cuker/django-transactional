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
