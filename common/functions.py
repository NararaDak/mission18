from __future__ import annotations

import configparser
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

from fastapi import Request
from pydantic import BaseModel

from app.defines import M18_BEND_INI_PATH

if TYPE_CHECKING:
	from app.services.sentiment_service import SentimentService
	from app.storage.memory_store import MemoryStore

SchemaType = TypeVar("SchemaType", bound=BaseModel)


def Ensure_Directory(dirPath: str) -> None:
	os.makedirs(dirPath, exist_ok=True)


def Get_Ini_Config() -> configparser.ConfigParser:
	configData = configparser.ConfigParser()
	configData.read(M18_BEND_INI_PATH, encoding="utf-8")
	return configData


def Get_Ini_Value(sectionName: str, keyName: str, fallbackValue: str = "") -> str:
	configData = Get_Ini_Config()
	return configData.get(sectionName, keyName, fallback=fallbackValue)


def Get_Ini_Int_Value(sectionName: str, keyName: str, fallbackValue: int) -> int:
	configData = Get_Ini_Config()
	return configData.getint(sectionName, keyName, fallback=fallbackValue)


def Set_Ini_Value(sectionName: str, keyName: str, valueData: str | int | float | bool) -> None:
	configData = Get_Ini_Config()
	if not configData.has_section(sectionName):
		configData.add_section(sectionName)

	configData.set(sectionName, keyName, str(valueData))
	with open(M18_BEND_INI_PATH, "w", encoding="utf-8") as fileData:
		configData.write(fileData)


def Get_Now() -> datetime:
	return datetime.now()


def To_Schema(sourceData: Any, schemaType: type[SchemaType]) -> SchemaType:
	return schemaType.model_validate(sourceData, from_attributes=True)


def Get_Store(request: Request) -> MemoryStore:
	return request.app.state.Store


def Get_Sentiment_Service(request: Request) -> SentimentService:
	return request.app.state.SentimentService
