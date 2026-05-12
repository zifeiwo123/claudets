"""Compatibility facade for the old pipeline entry.

The canonical experiment pipeline is autonomous_loop.py. The old workflow had
separate train-IC, cost, and report logic that could drift from the governed
research path, so this class delegates to the canonical entry instead.
"""


class AlphaEvolutionPipeline:
    def __init__(self):
        self.reports = []
        self.pool = None

    def run(self):
        from autonomous_loop import main

        return main()
