import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class PickleHandler:
    """Handler for saving and loading pickle files."""

    def __init__(self, default_dir: Optional[Union[str, Path]] = None):
        """
        Determine the default directory for pickle files.

        Args:
            default_dir: Default directory for pickle files. If None, uses current directory.
        """
        self.default_dir = Path(default_dir) if default_dir else Path.cwd()
        self.default_dir.mkdir(parents=True, exist_ok=True)

    def save_index_dict(
        self,
        index_dict: Dict[Any, Any],
        filename: str,
        location: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Save indexing dictionary to pickle file.

        Parameters
        ----------
        index_dict : dict
            Dictionary to save.
        filename : str
            Name of the pickle file (with or without .pkl extension).
        location : str or Path, optional
            Directory to save the file. If None, uses default_dir.

        Returns
        -------
        Path
            Path to the saved file.

        Raises
        ------
        ValueError
            If index_dict is not a dictionary.
        OSError
            If unable to save file.
        """
        if not isinstance(index_dict, dict):
            raise ValueError("index_dict must be a dictionary")

        # Ensure filename has .pkl extension
        if not filename.endswith(".pkl"):
            filename += ".pkl"

        # Determine save location
        save_dir = Path(location) if location else self.default_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / filename
        try:
            with open(file_path, "wb") as f:
                pickle.dump(index_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.info("Successfully saved index dictionary to %s", file_path)
            return file_path

        except Exception as e:
            logger.error("Failed to save index dictionary to %s: %s", file_path, e)
            raise OSError(f"Unable to save pickle file: {e}") from e

    def load_index_dict(
        self, filename: str, location: Optional[Union[str, Path]] = None
    ) -> Dict[Any, Any]:
        """
        Load indexing dictionary from pickle file.

        Parameters
        ----------
        filename : str
            Name of the pickle file (with or without .pkl extension).
        location : str or Path, optional
            Directory to load from. If None, uses default_dir.

        Returns
        -------
        dict
            Loaded dictionary.

        Raises
        ------
        FileNotFoundError
            If pickle file doesn't exist.
        ValueError
            If loaded object is not a dictionary.
        OSError
            If unable to load file.
        """
        # Ensure filename has .pkl extension
        if not filename.endswith(".pkl"):
            filename += ".pkl"

        # Determine load location
        load_dir = Path(location) if location else self.default_dir
        file_path = load_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Pickle file not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                loaded_data = pickle.load(f)

            if not isinstance(loaded_data, dict):
                raise ValueError(
                    f"Loaded object is not a dictionary, got {type(loaded_data)}"
                )

            logger.info("Successfully loaded index dictionary from %s", file_path)
            return loaded_data

        except Exception as e:
            logger.error("Failed to load index dictionary from %s: %s", file_path, e)
            raise OSError(f"Unable to load pickle file: {e}") from e


# Convenience functions for quick usage
def save(
    index_dict: Dict[Any, Any],
    filename: str,
    location: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Save indexing dictionary to a pickle file.

    Parameters
    ----------
    index_dict : dict
        Dictionary to save.
    filename : str
        Name of the pickle file (with or without .pkl extension).
    location : str or Path, optional
        Directory to save the file. If None, uses current directory.

    Returns
    -------
    Path
        Path to the saved file.
    """
    handler = PickleHandler()
    return handler.save_index_dict(index_dict, filename, location)


def load(filename: str, location: Optional[Union[str, Path]] = None) -> Dict[Any, Any]:
    """
    Load indexing dictionary from a pickle file.

    Parameters
    ----------
    filename : str
        Name of the pickle file (with or without .pkl extension).
    location : str or Path, optional
        Directory to load the file from. If None, uses current directory.

    Returns
    -------
    dict
        Loaded dictionary.
    """
    handler = PickleHandler()
    return handler.load_index_dict(filename, location)
