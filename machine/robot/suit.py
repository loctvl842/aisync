import glob
import importlib
import os
import traceback
from inspect import getmembers
from typing import Any

from langchain.agents.tools import BaseTool

from core.logger import syslog

from .decorators import SuitAction, SuitHook, SuitWorkflow
from .engines.node import Node
from .utils import get_suit_name


class Suit:
    def __init__(self, path_to_suit):
        if not os.path.exists(path_to_suit) or not os.path.isdir(path_to_suit):
            raise ValueError(f"Path '{path_to_suit}' does not exist or is not a directory.")
        self._path = path_to_suit
        self._name = get_suit_name(path_to_suit)
        self._actions = {}
        self._hooks = {}
        self._tools = {}
        self._workflow = {}
        self._nodes = {}
        self._active = False
        self._path_to_doc = glob.glob(f"{path_to_suit}/documents/*")

    @staticmethod
    def _is_suit_action(member):
        return isinstance(member, SuitAction)

    @staticmethod
    def _is_suit_hook(member):
        return isinstance(member, SuitHook)

    @staticmethod
    def _is_suit_tool(member):
        return isinstance(member, BaseTool)
    
    @staticmethod
    def _is_suit_workflow(member):
        return isinstance(member, SuitWorkflow)
    
    @staticmethod
    def _is_node(member):
        return isinstance(member, Node)

    def _get_source_files(self):
        source_file_paths = os.path.join(self._path, "**/*.py")
        return glob.glob(source_file_paths, recursive=True)

    def _get_decorated_fn(self):
        source_files = self._get_source_files()
        actions = {}
        hooks = {}
        tools = {}
        workflow = {}
        nodes = {}

        for source_file in source_files:
            file_name = os.path.splitext(source_file)[0]
            module_name = file_name.replace(os.sep, ".")
            try:
                suit_module = importlib.import_module(module_name)
                # find actions
                new_actions = {
                    action_fn[0]: action_fn[1] for action_fn in getmembers(suit_module, self._is_suit_action)
                }
                duplicate_actions = set(actions.keys()) & set(new_actions.keys())
                if duplicate_actions:
                    syslog.warning(f"Duplicate action detected: {duplicate_actions}")
                # find hooks
                new_hooks = {hook_fn[0]: hook_fn[1] for hook_fn in getmembers(suit_module, self._is_suit_hook)}
                duplicate_hooks = set(hooks.keys()) & set(new_hooks.keys())
                if duplicate_hooks:
                    syslog.warning(f"Duplicate hook detected: {duplicate_hooks}")
                # find tools
                new_tools = {tool_fn[0]: tool_fn[1] for tool_fn in getmembers(suit_module, self._is_suit_tool)}
                duplicate_tools = set(tools.keys()) & set(new_tools.keys())
                if duplicate_tools:
                    syslog.warning(f"Duplicate tool detected: {duplicate_tools}")

                # find workflow
                new_workflow = {workflow_fn[0]: workflow_fn[1] for workflow_fn in getmembers(suit_module, self._is_suit_workflow)}
                duplicate_workflow = set(workflow.keys()) & set(new_workflow.keys())
                if duplicate_workflow:
                    syslog.warning(f"Duplicate workflow detected: {duplicate_workflow}")

                # find nodes
                new_nodes = {node_fn[0]: node_fn[1] for node_fn in getmembers(suit_module, self._is_node)}
                duplicate_nodes = set(nodes.keys()) & set(new_nodes.keys())
                if duplicate_nodes:
                    syslog.warning(f"Duplicate node detected: {duplicate_nodes}")
                
                actions.update(new_actions)
                hooks.update(new_hooks)
                tools.update(new_tools)
                workflow.update(new_workflow)
                nodes.update(new_nodes)
            except Exception as e:
                syslog.error(f"Failed to import {module_name}: {e}")

        return actions, hooks, tools, workflow, nodes

    def activate(self):
        self._actions, self._hooks, self._tools, self._workflow, self._nodes = self._get_decorated_fn()
        self._active = True

    def deactivate(self):
        self._hook = {}
        self._tools = {}
        self._actions = {}
        self._workflow = {}
        self._active = False

    def execute_action(self, action_name, *args, **kwargs) -> Any:
        if action_name in self._actions:
            return self._actions[action_name].call(*args, **kwargs)
        syslog.error(f"Action {action_name} not found")

    def execute_hook(self, hook_name: str, *args, **kwargs) -> Any:
        default = kwargs.get("default", None)
        if hook_name in self._hooks:
            try:
                syslog.debug(f"Executing plugin hook `{self.name}::{hook_name}`")
                return self._hooks[hook_name].call(*args, **kwargs)
            except Exception as e:
                syslog.error(f"Error when executing plugin hook `{self.name}::{hook_name}`: {e}")
                traceback.print_exc()
                return default
        syslog.error(f"Hook `{hook_name}` not found")
        return default
    
    def execute_workflow(self, *args, **kwargs) -> Any:
        default = kwargs.get("default", None)
        workflow_name = next(iter(self._workflow))
        try:
            syslog.debug(f"Executing plugin hook `{self.name}::{workflow_name}`")
            return self._workflow[workflow_name].call(*args, **kwargs)
        except Exception as e:
            syslog.error(f"Error when executing plugin hook `{self.name}::{workflow_name}`: {e}")
            traceback.print_exc()
            return default

    @property
    def name(self):
        return self._name

    @property
    def active(self):
        return self._active

    @property
    def actions(self):
        return self._actions

    @property
    def hooks(self):
        return self._hooks

    @property
    def tools(self):
        return self._tools
    
    @property
    def workflow(self):
        return self._workflow
    
    @property
    def nodes(self):
        return self._nodes
