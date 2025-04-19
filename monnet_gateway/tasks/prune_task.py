from shared.app_context import AppContext

class PruneTask:
    """Clase para realizar tareas de limpieza periódica."""
    def __init__(self, ctx: AppContext):
        self.logger = ctx.get_logger()

    def run(self):
        """Ejecuta la tarea de limpieza."""
        self.logger.info("Running PruneTask...")
        # Aquí se implementaría la lógica de limpieza
        self.logger.info("PruneTask completed.")
