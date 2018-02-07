import os
import progressbar
try:
    from mpprogress import mpprogress
    mpprogress_imported = True
except ImportError:
    mpprogress_imported = False

Progress_Mode = 'console'

class MyProgressBase:
    def __init__(self, min_value=0, max_value=0):
        pass
    def update(self, count):
        pass
    def finish(self):
        pass

class ConsoleProgress(MyProgressBase):
    def __init__(self, min_value=0, max_value=None):
        self.progress = progressbar.ProgressBar(min_value=min_value, max_value=max_value)
    def update(self, count):
        self.progress.update(count)
    def finish(self):
        self.progress.finish()

def get_recommended_mode():
    if "PROGRESS_NAME" in os.environ:
        return 'multiprocess'
    return 'console'

def make_progress(min_value=0, max_value=None):
    if Progress_Mode == 'console':
        return ConsoleProgress(min_value=min_value, max_value=max_value)
    elif mpprogress_imported and Progress_Mode == 'multiprocess' and os.getenv("PROGRESS_NAME"):
        return mpprogress.MultiprocessedProgress(os.getenv("PROGRESS_NAME"), min_value=min_value, max_value=max_value)
    else:
        return MyProgressBase(min_value=min_value, max_value=max_value)