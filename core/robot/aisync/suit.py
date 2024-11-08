import glob
import importlib
import os
import traceback
from inspect import getmembers
from typing import Any

from .decorators import Graph, Hook, Node
from .decorators.hook import SupportedHook
from .log import log
from .utils import get_suit_name


class Suit:
    def __init__(self, path_to_suit):
        if not os.path.exists(path_to_suit) or not os.path.isdir(path_to_suit):
            raise ValueError(f"Path '{path_to_suit}' does not exist or is not a directory.")
        self._path = path_to_suit
        self._name = get_suit_name(path_to_suit)
        self._hooks: dict[SupportedHook, Hook] = {}
        self._nodes: dict[str, Node] = {}
        self._graphs: dict[str, Graph] = {}

    @staticmethod
    def _is_hook(member):
        return isinstance(member, Hook)

    @staticmethod
    def _is_node(member):
        return isinstance(member, Node)

    @staticmethod
    def _is_graph(member):
        return isinstance(member, Graph)

    def _get_decorated_fn(self):
        source_files = self._get_source_files()
        hooks = {}
        nodes = {}
        graphs = {}
        for source_file in source_files:
            file_name = os.path.splitext(source_file)[0]
            module_name = file_name.replace(os.sep, ".")
            try:
                suit_module = importlib.import_module(module_name)

                # find hooks
                new_hooks = {hook_fn[0]: hook_fn[1] for hook_fn in getmembers(suit_module, self._is_hook)}
                duplicate_hooks = set(hooks.keys()) & set(new_hooks.keys())
                if duplicate_hooks:
                    log.warning(f"Duplicate hook detected: {duplicate_hooks}")
                hooks.update(new_hooks)

                # find nodes
                new_nodes = {node_fn[0]: node_fn[1] for node_fn in getmembers(suit_module, self._is_node)}
                duplicate_nodes = set(self._nodes.keys()) & set(new_nodes.keys())
                if duplicate_nodes:
                    log.warning(f"Duplicate node detected: {duplicate_nodes}")
                nodes.update(new_nodes)

                # find graph
                new_graphs = {graph_fn[0]: graph_fn[1] for graph_fn in getmembers(suit_module, self._is_graph)}
                duplicate_graphs = set(graphs.keys()) & set(new_graphs.keys())
                if duplicate_graphs:
                    log.warning(f"Duplicate graph detected: {duplicate_graphs}")
                graphs.update(new_graphs)

            except Exception as e:
                log.error(f"Failed to import {module_name}: {e}")
        return hooks, nodes, graphs

    def _get_source_files(self):
        source_file_paths = os.path.join(self._path, "**/*.py")
        return glob.glob(source_file_paths, recursive=True)

    def activate(self):
        self._hooks, self._nodes, self._graphs = self._get_decorated_fn()
        self._active = True

    def deactivate(self):
        self._hook = {}
        self._nodes = {}
        self._graphs = {}
        self._active = False

    def execute_hook(self, hook: SupportedHook, *args, default: Any = None, **kwargs) -> Any:
        """Execute a hook"""
        if hook in self._hooks:
            try:
                return self._hooks[hook].call(*args, **kwargs)
            except Exception as e:
                log.error(f"Error when executing plugin hook `{self.name}::{hook}`: {e}")
                traceback.print_exc()
                return default
        # syslog.warning(f"Hook `{hook}` not found")
        return default

    @property
    def name(self):
        return self._name

    @property
    def active(self):
        return self._active

    @property
    def hooks(self):
        return self._hooks

    @property
    def nodes(self):
        return self._nodes

    @property
    def graphs(self):
        return self._graphs
