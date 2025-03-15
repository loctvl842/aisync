import asyncio
import glob
import json
import os
import shutil
import tempfile
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import aiofiles
from git import Repo
from pydantic import BaseModel

from aisync.log import LogEngine
from aisync.utils import get_registry_dir

if TYPE_CHECKING:
    from aisync.suit import Suit


class SuitMetadata(BaseModel):
    """Model for suit metadata"""

    name: str
    version: str
    description: str
    author: str
    github_url: Optional[str] = None
    dependencies: List[str] = []
    branch: str = "main"


class Armory:
    """A place where suits (or armor) are stored and maintained."""

    def __init__(self) -> None:
        """Initialize the Armory."""
        self.log = LogEngine(self.__class__.__name__)
        self.registry_dir = get_registry_dir()

        self.suits_dir = os.path.join(self.registry_dir, "suits")
        self.metadata_dir = os.path.join(self.registry_dir, "metadata")

        # Create necessary directories
        os.makedirs(self.suits_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        self.active_suits = []
        self.suits = self.find_suits()
        self.log.info(f"Initialized suit registry at {self.registry_dir}")

    def find_suits(self) -> dict[str, "Suit"]:
        """
        Find all suits in the specified path

        Example:
            >>> find_suits()
            {'mark_i': '/path/to/mark_i', 'mark_ii': '/path/to/mark_ii'}
        """

        assert Path(self.suits_dir).exists(), f"Path '{self.suits_dir}' does not exist."

        try:
            all_suit_paths: list[str] = [path for path in glob.glob(f"{self.suits_dir}/*") if os.path.isdir(path)]

            suits: dict[str, "Suit"] = {}
            for path_to_suit in all_suit_paths:
                suit = self.load_suit(path_to_suit)
                suits[suit.name] = suit
                self.log.info(f"Loaded suit: {suit.name}")
            return suits
        except Exception as e:
            self.log.error(f"Error loading suits: {e}")
            self.log.error(traceback.format_exc())
            return {}

    def load_suit(self, path_to_suit: str) -> "Suit":
        """
        Load a suit from the specified path
        """
        from .suit import Suit

        try:
            suit = Suit(path_to_suit)
            return suit
        except Exception as e:
            self.log.error(f"Failed to load suit: {e}")

    def activate(self, suit_name: str) -> "Suit":
        # Activate the suit
        self.suits[suit_name].activate()
        self.active_suits.append(suit_name)
        self.log.info(f"Activated suit: {suit_name}")
        return self.suits[suit_name]

    async def ainstall_from_github(self, github_url: str, branch: str = "main") -> None:
        """Install a suit from a GitHub repository.

        Args:
            github_url (str): The URL of the GitHub repository.
            branch (str, optional): The branch to install. Defaults to "main".
        """
        temp_dir = tempfile.mkdtemp()

        try:
            # Clone the repository
            self.log.info(f"Cloning repository {github_url} to {temp_dir}")
            Repo.clone_from(github_url, temp_dir)
            suit_json_path = os.path.join(temp_dir, "suit.json")
            if not os.path.exists(suit_json_path):
                raise ValueError("No `suit.json` file found in the repository.")

            async with aiofiles.open(suit_json_path, "r") as f:
                metadata_json = await f.read()

            metadata_dict = json.loads(metadata_json)
            metadata = SuitMetadata(**metadata_dict)
            metadata.github_url = github_url

            if metadata.name in self.suits:
                self.log.warning(f"Suit {metadata.name} already exists. Skipping installation.")
                await self.auninstall_suit(metadata.name)

            # Create the suit directory
            suit_dir = os.path.join(self.suits_dir, metadata.name)
            os.makedirs(suit_dir, exist_ok=True)

            # Copy the files to the suit directory
            for file in os.listdir(temp_dir):
                if file == ".git":
                    continue
                src = os.path.join(temp_dir, file)
                if os.path.isdir(src):
                    shutil.copytree(src, os.path.join(suit_dir, file))
                else:
                    shutil.copy2(src, os.path.join(suit_dir, file))

            if metadata.dependencies:
                await self.ainstall_dependencies(metadata.dependencies)

            # Save metadata and update suits dict
            await self._asave_suit_metadata(metadata)
            self.suits[metadata.name] = metadata

            self.log.info(f"Successfully installed suit: {metadata.name}")
            return metadata
        except Exception as e:
            self.log.error(f"Error cloning repository: {e}")
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    async def ainstall_dependencies(self, dependencies: List[str]):
        """Install dependencies asynchronously

        Args:
            dependencies: List of dependencies to install
        """
        if not dependencies:
            return

        self.log.info(f"Installing dependencies: {dependencies}")

        # Create process
        process = await asyncio.create_subprocess_exec(
            "uv",
            "pip",
            "install",
            *dependencies,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"Error installing dependencies: {error_msg}")

    async def auninstall_suit(self, name: str):
        """Uninstall a suit from the registry"""
        if name not in self.suits:
            self.log.warning(f"Suit {name} not found in the registry.")
            raise ValueError(f"Suit {name} not found in the registry.")

        suit_dir = os.path.join(self.suits_dir, name)
        if os.path.exists(suit_dir):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: shutil.rmtree(suit_dir))

        metadata_path = os.path.join(self.metadata_dir, f"{name}.json")

        # Remove metadata
        metadata_path = os.path.join(self.metadata_dir, f"{name}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)

        # Remove from suits dict
        del self.suits[name]
        self.log.info(f"Uninstalled suit: {name}")
        return True

    async def _asave_suit_metadata(self, metadata: SuitMetadata) -> None:
        """Save suit metadata to file asynchronously"""
        metadata_path = os.path.join(self.metadata_dir, f"{metadata.name}.json")

        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata.model_dump(), indent=2))
