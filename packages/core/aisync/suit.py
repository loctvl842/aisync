import glob
import importlib
import os
import sys
import traceback
from inspect import getmembers
from pathlib import Path
from typing import Any

from aisync.decorators import Hook
from aisync.decorators.hook import SupportedHook
from aisync.engines.graph import Graph, Node
from aisync.log import log
from aisync.utils import get_project_root, get_suit_name


class Suit:
    def __init__(self, path_to_suit: str):
        self._path = Path(path_to_suit)
        if not self._path.exists():
            raise ValueError(f"Path '{path_to_suit}' does not exist or is not a directory.")
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
        hooks = {}
        nodes = {}
        graphs = {}

        project_path = get_project_root()

        if self._path.is_dir():
            pattern = os.path.join(self._path, "**/*.py")
            py_files = glob.glob(pattern, recursive=True)
        else:
            py_files = [str(self._path)]

        sys.path.insert(0, project_path)
        try:
            for py_file in py_files:
                abs_path = Path(py_file).resolve()
                relative_path = abs_path.relative_to(project_path)  # aisync/suits/mark_i/nodes.py
                file_stem = os.path.splitext(relative_path)[0]  # aisync/suits/mark_i/nodes
                module_path = file_stem.replace(os.sep, ".")
                try:
                    suit_module = importlib.import_module(module_path)

                    # find hooks
                    new_hooks = {hook_fn[0]: hook_fn[1] for hook_fn in getmembers(suit_module, self._is_hook)}
                    self.update_registry(hooks, new_hooks, "hook")

                    # find nodes
                    new_nodes = {node_fn[0]: node_fn[1] for node_fn in getmembers(suit_module, self._is_node)}
                    self.update_registry(nodes, new_nodes, "node")

                    # find graph
                    new_graphs = {graph_fn[0]: graph_fn[1] for graph_fn in getmembers(suit_module, self._is_graph)}
                    self.update_registry(graphs, new_graphs, "graph")

                except ModuleNotFoundError as e:
                    log.error(f"Failed to import '{module_path}': {e}")
                    raise e
                except Exception as e:
                    log.error(f"Failed to import {module_path}: {e}")
                    traceback.print_exc()
                    raise e
        except Exception as e:
            raise e
        finally:
            sys.path.pop(0)
        return hooks, nodes, graphs

    def update_registry(self, registry: dict, new_items: dict, item_type: str):
        """Update the registry with new items and check for duplicates."""
        duplicate_items = set(registry.keys()) & set(new_items.keys())
        if duplicate_items:
            log.warning(f"Duplicate {item_type} detected: {duplicate_items}")
        registry.update(new_items)

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
