"""Explicit copper edits with caller-controlled rollback and no silent rip-up."""
from .router import uid

class CopperTransaction:
    """In-memory transaction; commit only after native DRC/connectivity validation.

Keep this object alive until commit/rollback so SWIG owns removed objects safely.
Does not move footprints, change nets, weaken design rules, or touch files.
"""
    def __init__(self, board):
        self.board=board
        self.before={uid(t):t for t in board.GetTracks()}
        self.removed=[]
        self.committed=False

    def remove(self, items):
        for item in list(items):
            if uid(item) not in self.before: raise ValueError('Only pre-transaction copper may be removed')
            if item.IsLocked(): raise ValueError('Refusing to rip up locked copper')
        for item in list(items):
            self.board.Remove(item);self.removed.append(item)

    def remove_nets(self, nets):
        self.remove([t for t in self.board.GetTracks() if t.GetNetname() in nets])

    def commit(self): self.committed=True

    def rollback(self):
        for t in list(self.board.GetTracks()):
            if uid(t) not in self.before: self.board.Remove(t)
        current={uid(t) for t in self.board.GetTracks()}
        for t in self.removed:
            if uid(t) not in current: self.board.Add(t)
        self.board.BuildConnectivity()

    def __enter__(self): return self
    def __exit__(self, typ, value, traceback):
        if typ is not None or not self.committed: self.rollback()
