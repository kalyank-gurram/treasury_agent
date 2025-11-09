"""Plugin system for extensible Treasury Agent capabilities."""

from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any, Optional
from enum import Enum
import importlib
import os
from pathlib import Path

from ..domain.value_objects.treasury import EntityId
from ..graph.types import AgentState


class PluginType(Enum):
    """Types of plugins supported."""
    NODE = "node"           # LangGraph nodes
    FORECASTER = "forecaster"  # Forecasting algorithms
    DETECTOR = "detector"      # Anomaly detectors
    ANALYZER = "analyzer"      # Risk analyzers
    REPORTER = "reporter"      # Report generators


class PluginMetadata:
    """Metadata for a plugin."""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        plugin_type: PluginType,
        author: str = "",
        dependencies: Optional[List[str]] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.plugin_type = plugin_type
        self.author = author
        self.dependencies = dependencies or []


class Plugin(ABC):
    """Base plugin interface."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class NodePlugin(Plugin):
    """Base class for LangGraph node plugins."""
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """Execute the node logic."""
        pass
    
    @property
    @abstractmethod
    def intent_keywords(self) -> List[str]:
        """Keywords this node handles."""
        pass


class ForecasterPlugin(Plugin):
    """Base class for forecasting plugins."""
    
    @abstractmethod
    async def forecast(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int
    ) -> List[Dict[str, Any]]:
        """Generate forecast."""
        pass


class DetectorPlugin(Plugin):
    """Base class for anomaly detection plugins."""
    
    @abstractmethod
    async def detect_anomalies(
        self,
        data: List[Dict[str, Any]],
        entity_id: Optional[EntityId] = None
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in data."""
        pass


class PluginRegistry:
    """Central registry for managing plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugins_by_type: Dict[PluginType, List[Plugin]] = {
            plugin_type: [] for plugin_type in PluginType
        }
        self._initialized_plugins: set = set()
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin."""
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin {name} already registered")
        
        self._plugins[name] = plugin
        self._plugins_by_type[plugin.metadata.plugin_type].append(plugin)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        return self._plugins_by_type[plugin_type].copy()
    
    def list_plugins(self) -> List[Plugin]:
        """List all registered plugins."""
        return list(self._plugins.values())
    
    async def initialize_plugin(self, name: str, config: Dict[str, Any]) -> None:
        """Initialize a specific plugin."""
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin {name} not found")
        
        if name not in self._initialized_plugins:
            await plugin.initialize(config)
            self._initialized_plugins.add(name)
    
    async def initialize_all_plugins(self, config: Dict[str, Dict[str, Any]]) -> None:
        """Initialize all registered plugins."""
        for plugin in self._plugins.values():
            plugin_config = config.get(plugin.metadata.name, {})
            await self.initialize_plugin(plugin.metadata.name, plugin_config)
    
    async def cleanup_all_plugins(self) -> None:
        """Cleanup all initialized plugins."""
        for plugin in self._plugins.values():
            if plugin.metadata.name in self._initialized_plugins:
                await plugin.cleanup()
        self._initialized_plugins.clear()
    
    def auto_discover_plugins(self, plugin_dir: str) -> None:
        """Auto-discover plugins from a directory."""
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return
        
        for file_path in plugin_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue  # Skip private modules
            
            try:
                # Import the module
                module_name = f"treasury_agent.plugins.{file_path.stem}"
                module = importlib.import_module(module_name)
                
                # Look for plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Plugin) and 
                        attr != Plugin and
                        not attr.__name__.endswith('Plugin')):  # Skip base classes
                        
                        # Instantiate and register plugin
                        plugin_instance = attr()
                        self.register_plugin(plugin_instance)
                        
            except Exception as e:
                print(f"Failed to load plugin from {file_path}: {e}")


# Global plugin registry
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry