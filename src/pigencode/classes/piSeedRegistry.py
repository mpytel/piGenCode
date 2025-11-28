"""
Registry pattern for piSeed type handlers and command handlers.
Replaces exec() calls with a cleaner, more maintainable approach.
"""

from typing import Dict, Any, Protocol
from ..defs.logIt import printIt, label


class PiSeedHandler(Protocol):
    """Protocol defining the interface for piSeed handlers"""
    def __call__(self, germ_seeds_instance) -> None:
        """Process a piSeed using the germSeeds instance"""
        ...


class CommandHandler(Protocol):
    """Protocol defining the interface for command handlers"""
    def __call__(self, arg_parse) -> None:
        """Execute a command using the argParse instance"""
        ...


class PiSeedTypeRegistry:
    """Registry for piSeed type handlers"""

    def __init__(self):
        self._handlers: Dict[str, PiSeedHandler] = {}
        self._register_default_handlers()

    def register(self, seed_type: str, handler: PiSeedHandler) -> None:
        """Register a handler for a specific piSeed type"""
        self._handlers[seed_type] = handler
        # printIt(f"Registered handler for piSeed type: {seed_type}", label.DEBUG)

    def get_handler(self, seed_type: str) -> PiSeedHandler:
        """Get the handler for a specific piSeed type"""
        handler = self._handlers.get(seed_type)
        if handler is None:
            raise ValueError(f"No handler registered for piSeed type: {seed_type}")
        return handler

    def has_handler(self, seed_type: str) -> bool:
        """Check if a handler is registered for a piSeed type"""
        return seed_type in self._handlers

    def list_handlers(self) -> list[str]:
        """List all registered piSeed types"""
        return list(self._handlers.keys())

    def process_seed(self, germ_seeds_instance, seed_type: str) -> None:
        """Process a piSeed using the appropriate handler"""
        try:
            handler = self.get_handler(seed_type)
            handler(germ_seeds_instance)
        except ValueError as e:
            printIt(f"Handler error: {e}", label.ERROR)
            raise
        except Exception as e:
            printIt(f"Error processing piSeed type '{seed_type}': {e}", label.ERROR)
            raise

    def _register_default_handlers(self) -> None:
        """Register default handlers for built-in piSeed types"""
        # These will be registered when the PiGermSeeds class is imported
        # to avoid circular imports
        pass


class CommandRegistry:
    """Registry for command handlers"""

    def __init__(self):
        self._handlers: Dict[str, CommandHandler] = {}
        self._command_modules: Dict[str, str] = {}

    def register(self, command_name: str, handler: CommandHandler, module_path: str = '') -> None:
        """Register a handler for a specific command"""
        self._handlers[command_name] = handler
        if module_path:
            self._command_modules[command_name] = module_path
        printIt(f"Registered handler for command: {command_name}", label.DEBUG)

    def register_lazy(self, command_name: str, module_path: str) -> None:
        """Register a command for lazy loading"""
        self._command_modules[command_name] = module_path
        # printIt(f"Registered lazy handler for command: {command_name}", label.DEBUG)

    def get_handler(self, command_name: str) -> CommandHandler:
        """Get the handler for a specific command, loading if necessary"""
        # Check if handler is already loaded
        if command_name in self._handlers:
            return self._handlers[command_name]

        # Try to load handler lazily
        if command_name in self._command_modules:
            module_path = self._command_modules[command_name]
            try:
                # Dynamic import of the command module
                import importlib
                # Get the parent package name dynamically
                parent_package = __name__.rsplit('.', 1)[0]  # Get 'src.pigencode'
                module = importlib.import_module(f"{parent_package}.commands.{command_name}")
                handler = getattr(module, command_name)
                self._handlers[command_name] = handler
                return handler
            except (ImportError, AttributeError) as e:
                #printIt(f"Failed to load command '{command_name}' from '{module_path}': {e}", label.ERROR)
                raise ValueError(f"Could not load handler for command: {command_name}")

        raise ValueError(f"No handler registered for command: {command_name}")

    def has_handler(self, command_name: str) -> bool:
        """Check if a handler is registered for a command"""
        return command_name in self._handlers or command_name in self._command_modules

    def list_commands(self) -> list[str]:
        """List all registered commands"""
        all_commands = set(self._handlers.keys()) | set(self._command_modules.keys())
        return list(all_commands)

    def execute_command(self, command_name: str, arg_parse) -> None:
        """Execute a command using the appropriate handler"""
        try:
            handler = self.get_handler(command_name)
            handler(arg_parse)
        except ValueError as e:
            #printIt(f"Command error: {e}", label.ERROR)
            raise
        except Exception as e:
            printIt(f"Error executing command '{command_name}': {e}", label.ERROR)
            raise


# Global registry instances
pi_seed_registry = PiSeedTypeRegistry()
command_registry = CommandRegistry()


def register_pi_seed_handler(seed_type: str):
    """Decorator to register a piSeed handler"""
    def decorator(handler_func: PiSeedHandler) -> PiSeedHandler:
        pi_seed_registry.register(seed_type, handler_func)
        return handler_func
    return decorator


def register_command_handler(command_name: str, module_path: str = ''):
    """Decorator to register a command handler"""
    def decorator(handler_func: CommandHandler) -> CommandHandler:
        command_registry.register(command_name, handler_func, module_path)
        return handler_func
    return decorator
