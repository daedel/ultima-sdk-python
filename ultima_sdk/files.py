"""
Files module - Manages Ultima Online client data file paths.
Handles file discovery, path management, and file availability checking.
"""

import os
import platform
import warnings
from typing import Dict, Optional, List, Callable
from pathlib import Path
from .exceptions import FileAccessException


class Files:
    """Static utility class for managing Ultima Online data file paths."""

    # List of all known Ultima Online data files
    UO_FILES = [
        "anim.idx", "anim.mul", "anim2.idx", "anim2.mul", "anim3.idx", "anim3.mul",
        "anim4.idx", "anim4.mul", "anim5.idx", "anim5.mul", "animdata.mul",
        "art.mul", "artidx.mul", "artlegacymul.uop",
        "body.def", "bodyconv.def", "client.exe",
        "cliloc.custom1", "cliloc.custom2", "cliloc.deu", "cliloc.enu",
        "equipconv.def",
        "facet00.mul", "facet01.mul", "facet02.mul", "facet03.mul", "facet04.mul", "facet05.mul",
        "fonts.mul",
        "gump.def", "gumpart.mul", "gumpidx.mul", "gumpartlegacymul.uop",
        "hues.mul", "light.mul", "lightidx.mul",
        "map0.mul", "map1.mul", "map2.mul", "map3.mul", "map4.mul", "map5.mul",
        "map6.mul", "map7.mul", "map8.mul", "map9.mul", "map10.mul",
        "map0legacymul.uop", "map1legacymul.uop", "map2legacymul.uop", "map3legacymul.uop",
        "map4legacymul.uop", "map5legacymul.uop", "map6legacymul.uop", "map7legacymul.uop",
        "map8legacymul.uop", "map9legacymul.uop", "map10legacymul.uop",
        "mapdif0.mul", "mapdif1.mul", "mapdif2.mul", "mapdif3.mul", "mapdif4.mul",
        "mapdifl0.mul", "mapdifl1.mul", "mapdifl2.mul", "mapdifl3.mul", "mapdifl4.mul",
        "mobtypes.txt",
        "multi.idx", "multi.mul", "multimap.rle",
        "radarcol.mul",
        "skillgrp.mul",
        "skills.idx", "skills.mul",
        "sound.def", "sound.mul", "soundidx.mul", "soundlegacymul.uop",
        "speech.mul",
        "stadif0.mul", "stadif1.mul", "stadif2.mul", "stadif3.mul", "stadif4.mul",
        "stadifi0.mul", "stadifi1.mul", "stadifi2.mul", "stadifi3.mul", "stadifi4.mul",
        "stadifl0.mul", "stadifl1.mul", "stadifl2.mul", "stadifl3.mul", "stadifl4.mul",
        "staidx0.mul", "staidx1.mul", "staidx2.mul", "staidx3.mul", "staidx4.mul",
        "staidx5.mul", "staidx6.mul", "staidx7.mul", "staidx8.mul", "staidx9.mul", "staidx10.mul",
        "statics0.mul", "statics1.mul", "statics2.mul", "statics3.mul", "statics4.mul", "statics5.mul",
        "statics6.mul", "statics7.mul", "statics8.mul", "statics9.mul", "statics10.mul",
        "texidx.mul", "texmaps.mul",
        "tiledata.mul",
        "unifont.mul", "unifont1.mul", "unifont2.mul", "unifont3.mul", "unifont4.mul",
        "unifont5.mul", "unifont6.mul", "unifont7.mul", "unifont8.mul", "unifont9.mul",
        "unifont10.mul", "unifont11.mul", "unifont12.mul",
        "uotd.exe", "verdata.mul"
    ]

    # Registry keys to check (Windows only)
    KNOWN_REG_KEYS = [
        r"Origin Worlds Online\Ultima Online\1.0",
        r"Origin Worlds Online\Ultima Online Third Dawn\1.0",
        r"EA GAMES\Ultima Online Samurai Empire",
        r"EA GAMES\Ultima Online Samurai Empire\1.0",
        r"EA Games\Ultima Online: Mondain's Legacy",
        r"EA Games\Ultima Online: Mondain's Legacy\1.0",
        r"Electronic Arts\EA Games\Ultima Online Stygian Abyss Classic",
        r"Electronic Arts\EA Games\Ultima Online Classic",
        r"Electronic Arts\Ultima Online Classic",
    ]

    KNOWN_REG_PATH_KEYS = ["ExePath", "Install Dir", "InstallDir"]

    # Class variables
    _directory: Optional[str] = None
    _mul_path: Dict[str, str] = {}
    _root_dir: str = ""
    _cache_data: bool = True
    _file_save_callbacks: List[Callable[[], None]] = []

    @classmethod
    def initialize(cls, root_dir: Optional[str] = None) -> bool:
        """Initialize the Files system with optional root directory.

        Returns True if a valid UO directory was found and paths loaded,
        False otherwise. Detects environment variables `UO_ROOT` or
        `ULTIMA_ONLINE_DIR` (or `ULTIMA_SDK_UO_ROOT`) before checking platform
        registry/common paths.
        """
        # Allow environment variable override
        env_root = (
            os.environ.get("UO_ROOT")
            or os.environ.get("ULTIMA_ONLINE_DIR")
            or os.environ.get("ULTIMA_SDK_UO_ROOT")
        )
        if root_dir is None and env_root:
            root_dir = env_root

        if root_dir:
            cls.set_mul_path(root_dir)
            # confirm we found at least one file
            if any(v for v in cls._mul_path.values()):
                return True
            warnings.warn(f"No known UO data files found in provided directory: {root_dir}")
            return False

        cls._directory = cls._load_directory()
        if not cls._directory:
            warnings.warn("Could not auto-detect Ultima Online directory. "
                          "Call Files.set_directory(path) or set UO_ROOT environment variable.")
            # leave _mul_path empty to make failure explicit
            cls._mul_path = {}
            cls._root_dir = ""
            return False

        cls.load_mul_path()
        return any(v for v in cls._mul_path.values())

    @classmethod
    def get_directory(cls) -> Optional[str]:
        """Get the Ultima Online client directory."""
        if cls._directory is None:
            cls._directory = cls._load_directory()
        return cls._directory

    @classmethod
    def set_directory(cls, path: str) -> None:
        """Set the Ultima Online client directory."""
        cls._directory = path
        cls.load_mul_path()

    @classmethod
    def get_root_dir(cls) -> str:
        """Get the root directory for relative paths."""
        return cls._root_dir

    @classmethod
    def set_root_dir(cls, path: str) -> None:
        """Set the root directory for relative paths."""
        cls._root_dir = path

    @classmethod
    def is_cache_data(cls) -> bool:
        """Get whether data should be cached."""
        return cls._cache_data

    @classmethod
    def set_cache_data(cls, value: bool) -> None:
        """Set whether data should be cached."""
        cls._cache_data = value

    @classmethod
    def load_mul_path(cls) -> None:
        """Load all .mul file paths from the directory."""
        cls._mul_path = {}
        cls._root_dir = cls._directory or ""

        for file in cls.UO_FILES:
            file_path = os.path.join(cls._root_dir, file)
            if os.path.exists(file_path):
                cls._mul_path[file.lower()] = file
            else:
                cls._mul_path[file.lower()] = ""

    @classmethod
    def set_mul_path(cls, root_path: str) -> None:
        """Set the root path and reload all file paths."""
        cls._root_dir = root_path
        cls._mul_path = {}

        for file in cls.UO_FILES:
            file_path = os.path.join(cls._root_dir, file)
            if os.path.exists(file_path):
                cls._mul_path[file.lower()] = file
            else:
                cls._mul_path[file.lower()] = ""

    @classmethod
    def set_mul_path_entry(cls, key: str, path: str) -> None:
        """Set a specific file path."""
        cls._mul_path[key.lower()] = path

    @classmethod
    def get_file_path(cls, file: str) -> Optional[str]:
        """Get the full path to a specific file, or None if not found."""
        # If we haven't loaded any paths yet, try to initialize (non-intrusive)
        if not cls._mul_path:
            # Try a non-raising detection once
            try:
                cls.initialize()
            except Exception:
                pass

            if not cls._mul_path:
                warnings.warn("Files.get_file_path() called before UO data path was set. "
                              "Call Files.set_directory(path) or Files.initialize(path).")
                return None

        key = file.lower()
        if key not in cls._mul_path:
            # Allow arbitrary filenames (not in known UO list) by checking root dir directly
            candidate = os.path.join(cls._root_dir, file)
            if os.path.exists(candidate):
                return candidate
            return None

        path = cls._mul_path.get(key, "")
        if not path:
            return None

        # If path is relative, join with root
        if not os.path.isabs(path):
            path = os.path.join(cls._root_dir, path)

        return path if os.path.exists(path) else None

    @classmethod
    def get_mul_path(cls) -> Dict[str, str]:
        """Get the entire mul path dictionary."""
        return cls._mul_path.copy()

    @classmethod
    def require_file_path(cls, file: str) -> str:
        """Return the absolute path for a required UO data file or raise.

        This is a convenience for callers that need a guaranteed file path
        and prefer an explicit exception when the SDK cannot resolve it.
        """
        path = cls.get_file_path(file)
        if path:
            return path
        raise FileAccessException(
            f"Required Ultima Online data file not found: '{file}'. "
            "Set Files.set_directory(path) or set the UO_ROOT/ULTIMA_ONLINE_DIR environment variable."
        )

    @classmethod
    def require_files(cls, files: List[str]) -> Dict[str, str]:
        """Require multiple files and return a mapping of filename -> absolute path.

        Raises `FileAccessException` listing any missing files.
        """
        result: Dict[str, str] = {}
        missing: List[str] = []
        for f in files:
            try:
                result[f] = cls.require_file_path(f)
            except FileAccessException:
                missing.append(f)

        if missing:
            raise FileAccessException(f"Missing required files: {', '.join(missing)}")

        return result

    @classmethod
    def add_file_save_callback(cls, callback: Callable[[], None]) -> None:
        """Add a callback to be invoked when files are saved."""
        if callback not in cls._file_save_callbacks:
            cls._file_save_callbacks.append(callback)

    @classmethod
    def remove_file_save_callback(cls, callback: Callable[[], None]) -> None:
        """Remove a file save callback."""
        if callback in cls._file_save_callbacks:
            cls._file_save_callbacks.remove(callback)

    @classmethod
    def fire_file_save_event(cls) -> None:
        """Invoke all registered file save callbacks."""
        for callback in cls._file_save_callbacks:
            try:
                callback()
            except Exception as e:
                warnings.warn(f"Error in file save callback: {e}")

    @staticmethod
    def _load_directory() -> Optional[str]:
        """Attempt to find the Ultima Online directory."""
        if platform.system() == "Windows":
            try:
                import winreg

                def _normalize_registry_path(v: object) -> str:
                    s = str(v).strip().strip('"')
                    s = os.path.expandvars(s)
                    return s

                access_flags = [winreg.KEY_READ]
                # On 64-bit Windows, UO entries are often under the 32-bit view.
                for view_flag in (getattr(winreg, "KEY_WOW64_32KEY", 0), getattr(winreg, "KEY_WOW64_64KEY", 0)):
                    if view_flag:
                        access_flags.append(winreg.KEY_READ | view_flag)

                hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
                prefixes = ["SOFTWARE\\", "SOFTWARE\\WOW6432Node\\"]

                for hive in hives:
                    for prefix in prefixes:
                        for reg_key in Files.KNOWN_REG_KEYS:
                            reg_path = f"{prefix}{reg_key}"
                            for path_key in Files.KNOWN_REG_PATH_KEYS:
                                for flags in access_flags:
                                    try:
                                        key = winreg.OpenKey(hive, reg_path, 0, flags)
                                        value, _ = winreg.QueryValueEx(key, path_key)
                                        winreg.CloseKey(key)

                                        value = _normalize_registry_path(value)
                                        if value and os.path.isdir(value):
                                            return value
                                        if value and os.path.isfile(value):
                                            return os.path.dirname(value)
                                    except OSError:
                                        continue
                                    except Exception as e:
                                        warnings.warn(
                                            f"Unexpected registry read error for {reg_path}/{path_key}: {e}"
                                        )
                                        continue
            except Exception as e:
                warnings.warn(f"Registry access failed while detecting UO directory: {e}")

        # Try common paths
        pf = os.environ.get("Program Files")
        pfx86 = os.environ.get("Program Files (x86)")
        common_paths = [
            Path.home() / "Documents" / "Ultima Online",
            Path.home() / "Games" / "Ultima Online",
            Path("/opt/ultimaonline"),
            Path("C:/Ultima Online"),
        ]

        # Windows install fallbacks (cover common EA/Origin variants)
        for base in [pfx86, pf, "C:/Program Files (x86)", "C:/Program Files"]:
            if not base:
                continue
            common_paths.extend(
                [
                    Path(base) / "Ultima Online",
                    Path(base) / "Ultima Online Classic",
                    Path(base) / "EA Games" / "Ultima Online Classic",
                    Path(base) / "Electronic Arts" / "EA Games" / "Ultima Online Classic",
                    Path(base) / "Origin Games" / "Ultima Online",
                ]
            )

        for path in common_paths:
            if path.exists():
                return str(path)

        return None


# Initialize on module load
Files.initialize()
