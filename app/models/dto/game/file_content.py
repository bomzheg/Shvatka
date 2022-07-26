import io
import os
import typing
import zipfile
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.utils.exceptions import FileNotFound, ScenarioNotCorrect


@dataclass
class FileContent:
    file_id: typing.Optional[str] = None
    """telegram file_id"""
    file_path: typing.Optional[str] = None
    """path to file"""
    guid_: typing.Optional[str] = None
    """GUID for filename in file storage, DB and in archive"""
    original_filename: typing.Optional[str] = None
    """Filename from user before renamed to guid"""
    extension: typing.Optional[str] = None
    """extension with leading dot: ".zip" ".tar.gz" etc"""
    content: typing.Optional[str] = None
    """type of content"""

    def __post_init__(self):
        self.check_probably_inconsistent()

    def get_file(self):
        if all([self.file_id is None, self.file_path is None]):
            raise FileNotFound(text="file_id, file_path are together None")
        if self.file_id is not None:
            yield self.file_id
        if self.file_path is not None:
            with self.open_file_func(self.file_path, 'rb') as fp:
                yield BufferedInputFile(fp.read(), self.original_filename)
        return

    def file_kwargs(self):
        for file in self.get_file():
            yield {self.content: file}

    def get_file_str(self):
        if self.file_id is not None:
            return 'file_id', self.file_id
        if self.file_path is not None:
            return 'file_path', self.file_path
        raise FileNotFound(text="file_id, file_path are together None")

    def get_json_serializable(self):
        return {
            "__file__": True,
            "file_id": self.file_id,
            "guid": self.guid_,
            "original_file_name": self.original_filename,
            "extension": self.extension,
        }

    @classmethod
    def parse_as_file(cls, dct: dict):
        if "__file__" not in dct:
            raise ScenarioNotCorrect("file doesn't contains key __file__")
        return cls(
            file_id=dct.get("file_id", None),
            file_path=dct.get("file_path", None),
            guid_=dct.get("guid", None),
            original_filename=dct.get("original_filename", None),
            extension=dct.get("extension", None)
        )

    def is_all_filled(self):
        return all([
            self.file_id is not None,
            len(self.guid_) > 0,
            len(self.original_filename) > 0,
        ])

    def check_probably_inconsistent(self):
        if not any([
            bool(self.guid_ and self.extension),
            bool(self.file_id),
        ]):
            raise ScenarioNotCorrect(
                "No one of (file_id, guid + file) "
                "in file/thumb section exists"
            )

    @property
    def local_file_name(self):
        return self.guid_ + (self.extension or "")

    @property
    def open_file_func(self) -> typing.Callable[[typing.Union[str, bytes, os.PathLike, Path], typing.Any], io.FileIO]:
        if isinstance(self.file_path, Path):
            # noinspection PyTypeChecker
            return Path.open
        if isinstance(self.file_path, zipfile.Path):
            # noinspection PyTypeChecker
            return zipfile.Path.open
        if isinstance(self.file_path, (str, bytes, os.PathLike)):
            return open
        raise AttributeError(f"this method only for files on local drive, got type {type(self.file_path)}")

    async def redownload_from_tg(self, bot: Bot):
        with await bot.download(
            file=self.file_id,
            destination=self.file_path
        ) as downloaded_path:
            self.file_path = downloaded_path.name
