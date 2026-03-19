from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SectionKeyVal:
    mSection: str
    mKey: str
    mVal: str


@dataclass
class MyFlag:
    mEventName: str
    mDo: bool


class MemData:
    _data_queue: list[SectionKeyVal] = []
    _temp_flags: list[MyFlag] = []
    _kv_store: dict[tuple[str, str], str] = {}

    @classmethod
    def PutData(cls, section: str, key: str, val: str) -> None:
        cls._kv_store[(section, key)] = val
        cls._data_queue.append(SectionKeyVal(section, key, val))

    @classmethod
    def GetDataSecKeyVal(cls) -> SectionKeyVal | None:
        if not cls._data_queue:
            return None
        return cls._data_queue.pop(0)

    @classmethod
    def AddTempFlag(cls, event_name: str, do_event: bool) -> None:
        cls._temp_flags.append(MyFlag(event_name, do_event))

    @classmethod
    def GetTempFlag(cls) -> MyFlag | None:
        if not cls._temp_flags:
            return None
        return cls._temp_flags.pop(0)


class IniFile:
    _ini_data: dict[str, dict[str, str]] = {}

    def ResetIni(self) -> None:
        self._ini_data.clear()

    def ReadAllKey(self, section: str) -> dict[str, str]:
        return dict(self._ini_data.get(section, {}))


class EncryptionUtils:
    @staticmethod
    def decrypt(value: str) -> str:
        # Legacy Java code uses encrypted SQL; fallback keeps original text.
        return value or ""


class QS:
    @staticmethod
    def Str2Map(req_param: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(req_param, dict):
            return req_param
        if not req_param:
            return {}
        return json.loads(req_param)

    @staticmethod
    def Obj2Str(val: Any) -> str:
        if val is None:
            return ""
        return str(val)

    @staticmethod
    def Obj2Int(val: Any) -> int:
        if val is None:
            return 0
        try:
            text_val = str(val).strip()
            if not text_val:
                return 0
            return int(float(text_val))
        except Exception:
            return 0

    @staticmethod
    def Obj2ListString(val: Any) -> list[str]:
        if val is None:
            return []
        if isinstance(val, list):
            return [str(x) for x in val]
        return [str(val)]

    @staticmethod
    def Str2Int(val: str) -> int:
        try:
            return int(val)
        except Exception:
            return 0

    @staticmethod
    def Str2Long(val: str) -> int:
        return QS.Str2Int(val)

    @staticmethod
    def ChangeBool(val: str | bool) -> bool:
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in {"1", "true", "y", "yes"}

    @staticmethod
    def MoveFile(old_file: str, new_file: str) -> bool:
        src = Path(old_file)
        dst = Path(new_file)
        if not src.exists():
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return True

    @staticmethod
    def MoveFileForce(old_file: str, new_file: str) -> str:
        src = Path(old_file)
        dst = Path(new_file)
        if not src.exists():
            return ""
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.unlink()
        src.rename(dst)
        return str(dst)

    @staticmethod
    def DeleteFileIfExist(file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return True
        path.unlink()
        return True

    @staticmethod
    def GetFileList(parent_dir: str) -> list[str]:
        base = Path(parent_dir)
        if not base.exists():
            return []
        return [str(x) for x in base.iterdir()]

    @staticmethod
    def GetResultFiles(map_obj: dict[str, Any]) -> list[str]:
        base = Path(QS.Obj2Str(map_obj.get("baseDir", ".")))
        ext = QS.Obj2Str(map_obj.get("ext", ""))
        if not base.exists():
            return []
        if ext:
            return [str(p) for p in base.rglob(f"*{ext}")]
        return [str(p) for p in base.rglob("*") if p.is_file()]

    @staticmethod
    def GetResultFilesEx(map_obj: dict[str, Any]) -> list[str]:
        return QS.GetResultFiles(map_obj)

    @staticmethod
    def FindLargerFiles(
        base_dir: str,
        target_dir: str,
        target_file: str,
        extension: str,
        _minus_hour: int,
    ) -> list[str]:
        base = Path(base_dir)
        if not base.exists():
            return []
        pattern = f"*{extension}" if extension else "*"
        out: list[str] = []
        for file_path in base.rglob(pattern):
            if not file_path.is_file():
                continue
            if target_dir and target_dir not in str(file_path.parent):
                continue
            if target_file and target_file not in file_path.name:
                continue
            out.append(str(file_path))
        return out

    @staticmethod
    def FindLargerFilesEx(
        base_dir: str,
        last_dir: str,
        last_file: str,
        reg_exp: str,
        count: int,
    ) -> list[str]:
        base = Path(base_dir)
        if not base.exists():
            return []
        files = sorted([p for p in base.rglob("*") if p.is_file()])
        out: list[str] = []
        for file_path in files:
            if last_dir and last_dir not in str(file_path.parent):
                continue
            if last_file and file_path.name <= last_file:
                continue
            if reg_exp and reg_exp not in file_path.name:
                continue
            out.append(str(file_path))
            if len(out) >= count:
                break
        return out

    @staticmethod
    def SearchFilesFromDir(
        search_dir: str,
        last_file: str,
        regexp: str,
        count: int,
        out_list: list[str],
    ) -> None:
        base = Path(search_dir)
        if not base.exists():
            return
        for file_path in sorted([p for p in base.rglob("*") if p.is_file()]):
            if last_file and file_path.name <= last_file:
                continue
            if regexp and regexp not in file_path.name:
                continue
            out_list.append(str(file_path))
            if len(out_list) >= count:
                break


class FileClient:
    def __init__(self) -> None:
        self._read_size = 0

    def WriteFile(self, req_param_or_path: str, data: str | None = None) -> dict[str, Any] | bool:
        if data is not None:
            path = Path(req_param_or_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8")
            return True

        req_map = QS.Str2Map(req_param_or_path)
        new_file = QS.Obj2Str(req_map.get("newfile"))
        content = QS.Obj2Str(req_map.get("data"))
        if not new_file:
            return {"statusCode": "100", "statusMsg": "newfile is empty"}
        path = Path(new_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"statusCode": "200", "statusMsg": "OK"}

    def DownloadFile(self, req_param: str) -> dict[str, Any]:
        req_map = QS.Str2Map(req_param)
        target = Path(QS.Obj2Str(req_map.get("readfile", req_map.get("fullpath", ""))))
        if not target.exists() or not target.is_file():
            return {"statusCode": "100", "statusMsg": "File not found"}
        return {
            "statusCode": "200",
            "statusMsg": "OK",
            "filename": target.name,
            "content": target.read_text(encoding="utf-8", errors="ignore"),
        }

    def DownloadList(self, req_param: str) -> dict[str, Any]:
        req_map = QS.Str2Map(req_param)
        base_dir = Path(QS.Obj2Str(req_map.get("baseDir", ".")))
        if not base_dir.exists():
            return {"statusCode": "100", "statusMsg": "Base directory not found"}
        return {
            "statusCode": "200",
            "statusMsg": "OK",
            "list": [str(p) for p in base_dir.rglob("*") if p.is_file()],
        }

    def ReadFile(self, full_path: str, offset: int) -> str:
        file_path = Path(full_path)
        if not file_path.exists():
            self._read_size = 0
            return ""
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        sliced = content[offset:]
        self._read_size = len(sliced)
        return sliced

    def GetReadSize(self) -> int:
        return self._read_size


class ZipOperation:
    def File2TempZip(self, org_file: str) -> str:
        src = Path(org_file)
        if not src.exists() or not src.is_file():
            return ""
        temp_dir = Path(tempfile.gettempdir())
        zip_path = temp_dir / f"{src.stem}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(src, arcname=src.name)
        return str(zip_path)


def ok_response(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    out = {"statusCode": "200", "statusMsg": "OK"}
    if extra:
        out.update(extra)
    return out


def error_response(message: str) -> dict[str, Any]:
    return {"statusCode": "100", "statusMsg": message}


def to_map(req_param: str | dict[str, Any]) -> dict[str, Any]:
    return QS.Str2Map(req_param)
