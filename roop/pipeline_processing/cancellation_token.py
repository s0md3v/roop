class CancellationToken:
    """Cancellation token"""

    def __init__(self):
        self.paused = False
        self.cancelled = False

    def pause(self):
        """Set pause"""
        self.paused = True

    def resume(self):
        """Resume"""
        self.paused = False

    def cancel(self):
        """Set cancelled"""
        self.cancelled = True