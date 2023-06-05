class CancellationToken:
    """Cancellation token"""

    def __init__(self):
        self.cancelled = False

    def cancel(self):
        """Set cancelled"""
        self.cancelled = True