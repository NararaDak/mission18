import math
import configparser
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from call_api import CallApi
from loading_popup import LoadingPopup

PAGE_SIZE = 10
PAGE_GROUP_SIZE = 5


@st.cache_data(show_spinner=False)
def _getColumnTitleMap() -> dict[str, str]:
	projectRootDir = Path(__file__).resolve().parent.parent.parent
	iniPath = projectRootDir / "common" / "m18.ini"

	configData = configparser.ConfigParser()
	configData.optionxform = str
	configData.read(iniPath, encoding="utf-8")

	if not configData.has_section("eng_kor"):
		return {}

	return {key: value for key, value in configData.items("eng_kor")}


def _getCurrentPage() -> int:
	if "movieListPage" not in st.session_state:
		st.session_state["movieListPage"] = 1
	return int(st.session_state["movieListPage"])


def _setCurrentPage(pageValue: int) -> None:
	st.session_state["movieListPage"] = max(1, int(pageValue))


def _setActionMessage(messageText: str) -> None:
	st.session_state["movieListActionMessage"] = messageText


def _addMonths(baseDate: date, monthDiff: int) -> date:
	totalMonth = (baseDate.month - 1) + monthDiff
	newYear = baseDate.year + (totalMonth // 12)
	newMonth = (totalMonth % 12) + 1
	maxDay = monthrange(newYear, newMonth)[1]
	newDay = min(baseDate.day, maxDay)
	return date(newYear, newMonth, newDay)


def _ensureSearchDefaults() -> None:
	todayValue = date.today()
	if "movieSearchTitle" not in st.session_state:
		st.session_state["movieSearchTitle"] = ""
	if "movieSearchDirector" not in st.session_state:
		st.session_state["movieSearchDirector"] = ""
	if "movieSearchActor" not in st.session_state:
		st.session_state["movieSearchActor"] = ""
	if "movieSearchUseReleaseRange" not in st.session_state:
		st.session_state["movieSearchUseReleaseRange"] = True
	if "movieSearchStartDate" not in st.session_state:
		st.session_state["movieSearchStartDate"] = _addMonths(todayValue, -3)
	if "movieSearchEndDate" not in st.session_state:
		st.session_state["movieSearchEndDate"] = _addMonths(todayValue, 3)


def _getSearchFilters() -> dict[str, str]:
	useReleaseRange = bool(st.session_state.get("movieSearchUseReleaseRange", True))
	startDateValue = st.session_state.get("movieSearchStartDate")
	endDateValue = st.session_state.get("movieSearchEndDate")

	return {
		"title": str(st.session_state.get("movieSearchTitle", "") or "").strip(),
		"director": str(st.session_state.get("movieSearchDirector", "") or "").strip(),
		"actor": str(st.session_state.get("movieSearchActor", "") or "").strip(),
		"releaseStart": startDateValue.isoformat() if useReleaseRange and isinstance(startDateValue, date) else "",
		"releaseEnd": endDateValue.isoformat() if useReleaseRange and isinstance(endDateValue, date) else "",
	}


def _openDialog(dialogType: str, rowData: dict[str, object] | None = None) -> None:
	st.session_state["movieDialogType"] = dialogType
	st.session_state["movieDialogRow"] = dict(rowData) if rowData is not None else None


def _closeDialog() -> None:
	st.session_state.pop("movieDialogType", None)
	st.session_state.pop("movieDialogRow", None)


def _setSelectedMovie(rowData: dict[str, object]) -> None:
	st.session_state["selectedMovieRow"] = dict(rowData)


def _getSelectedMovie() -> dict[str, object] | None:
	selectedRow = st.session_state.get("selectedMovieRow")
	return selectedRow if isinstance(selectedRow, dict) else None


def _refreshTotalCount(callApi: CallApi) -> None:
	countResult = callApi.getMoviesCount(_getSearchFilters())
	if countResult.get("ok"):
		st.session_state["movieListTotalCount"] = max(0, int(countResult.get("totalCount", 0)))
	st.session_state.pop("movieListCacheKey", None)


def _syncSelectedMovie(rows: list[dict[str, object]]) -> None:
	if not rows:
		st.session_state.pop("selectedMovieRow", None)
		return

	selectedRow = _getSelectedMovie()
	selectedMovieId = 0 if selectedRow is None else int(selectedRow.get("movieId", 0) or 0)
	for row in rows:
		if int(row.get("movieId", 0) or 0) == selectedMovieId:
			_setSelectedMovie(row)
			return

	_setSelectedMovie(rows[0])


def _parseReleaseDate(valueData: object) -> date:
	textValue = "" if valueData is None else str(valueData).strip()
	digitOnly = "".join(ch for ch in textValue if ch.isdigit())
	if len(digitOnly) >= 8:
		try:
			return datetime.strptime(digitOnly[:8], "%Y%m%d").date()
		except ValueError:
			pass
	return date.today()


def _formatReleaseDate(valueData: object) -> str:
	"""YYYYMMDD 또는 YYYY-MM-DD 등 → YYYY-MM-DD 문자열로 변환"""
	textValue = "" if valueData is None else str(valueData).strip()
	digitOnly = "".join(ch for ch in textValue if ch.isdigit())
	if len(digitOnly) >= 8:
		return f"{digitOnly[:4]}-{digitOnly[4:6]}-{digitOnly[6:8]}"
	return textValue


@st.dialog("영화 추가", width="large")
def _showCreateMovieDialog(callApi: CallApi) -> None:
	with st.form("movieAddDialogForm"):
		titleValue = st.text_input("제목")
		releaseDateValue = st.date_input("개봉일", value=date.today(), format="YYYY-MM-DD")
		directorValue = st.text_input("감독")
		actorValue = st.text_input("배우")
		genreValue = st.text_input("장르")
		posterUrlValue = st.text_input("포스터 URL")
		submitCreate = st.form_submit_button("영화 추가 저장", use_container_width=True)

	if submitCreate:
		with LoadingPopup("영화 추가 중입니다..."):
			createResult = callApi.createMovie(
				titleValue=titleValue.strip(),
				releaseDateValue=releaseDateValue.isoformat(),
				directorValue=directorValue.strip(),
				actorValue=actorValue.strip(),
				genreValue=genreValue.strip(),
				posterUrlValue=posterUrlValue.strip(),
			)
		if createResult.get("ok"):
			_refreshTotalCount(callApi)
			_setActionMessage(f"영화 추가 완료: {titleValue.strip()}")
			_closeDialog()
			st.rerun()
		else:
			st.error(createResult.get("error", "영화 추가에 실패했습니다."))


@st.dialog("영화 수정", width="large")
def _showEditMovieDialog(callApi: CallApi, rowData: dict[str, object]) -> None:
	movieId = int(rowData.get("movieId", 0) or 0)
	with st.form(f"movieEditDialogForm_{movieId}"):
		titleValue = st.text_input("제목", value=str(rowData.get("title", "")))
		releaseDateValue = st.date_input("개봉일", value=_parseReleaseDate(rowData.get("repRlsDate")), format="YYYY-MM-DD")
		directorValue = st.text_input("감독", value=str(rowData.get("directorNm", "")))
		actorValue = st.text_input("배우", value=str(rowData.get("actorNm", "")))
		genreValue = st.text_input("장르", value=str(rowData.get("genre", "")))
		posterUrlValue = st.text_input("포스터 URL", value=str(rowData.get("posterUrl", "")))
		submitEdit = st.form_submit_button("영화 수정 저장", use_container_width=True)

	if submitEdit:
		with LoadingPopup("영화 수정 중입니다..."):
			updateResult = callApi.updateMovie(
				movieIdValue=movieId,
				titleValue=titleValue.strip(),
				releaseDateValue=releaseDateValue.isoformat(),
				directorValue=directorValue.strip(),
				actorValue=actorValue.strip(),
				genreValue=genreValue.strip(),
				posterUrlValue=posterUrlValue.strip(),
			)
		if updateResult.get("ok"):
			st.session_state.pop("movieListCacheKey", None)
			st.session_state.pop("movieListActionMessage", None)
			_closeDialog()
			st.rerun()
		else:
			st.error(updateResult.get("error", "영화 수정에 실패했습니다."))


@st.dialog("리뷰 등록", width="large")
def _showCreateReviewDialog(callApi: CallApi, rowData: dict[str, object]) -> None:
	movieId = int(rowData.get("movieId", 0) or 0)
	movieTitle = str(rowData.get("title", ""))
	st.caption(f"대상 영화: {movieTitle} (movieId: {movieId})")
	with st.form(f"reviewCreateDialogForm_{movieId}"):
		authorNameValue = st.text_input("작성자")
		contentValue = st.text_area("리뷰 내용", height=160)
		submitReview = st.form_submit_button("리뷰 등록", use_container_width=True)

	if submitReview:
		with LoadingPopup("리뷰 등록 중입니다..."):
			createResult = callApi.createReview(movieId, authorNameValue.strip(), contentValue.strip())
		if createResult.get("ok"):
			st.session_state.pop("movieReviewListCacheKey", None)
			_setSelectedMovie(rowData)
			_setActionMessage(f"리뷰 등록 완료: {movieTitle}")
			_closeDialog()
			st.rerun()
		else:
			st.error(createResult.get("error", "리뷰 등록에 실패했습니다."))


def _renderMovieTable(callApi: CallApi, rows: list[dict[str, object]], displayColumns: list[str], columnTitleMap: dict[str, str]) -> None:
	headerColumns = st.columns([3, 2, 3, 2, 1])
	for headerColumn, col in zip(headerColumns[:-1], displayColumns):
		headerColumn.markdown(f"**{columnTitleMap.get(col, col)}**")
	headerColumns[-1].markdown("**관리**")
	selectedRow = _getSelectedMovie()
	selectedMovieId = 0 if selectedRow is None else int(selectedRow.get("movieId", 0) or 0)

	for rowIndex, row in enumerate(rows):
		dataColumns = st.columns([3, 2, 3, 2, 1])
		rowMovieId = int(row.get("movieId", 0) or 0)
		for columnIndex, (dataColumn, col) in enumerate(zip(dataColumns[:-1], displayColumns)):
			cellValue = row.get(col, "")
			if columnIndex == 0:
				buttonLabel = ("▶ " if rowMovieId == selectedMovieId else "") + ("" if cellValue is None else str(cellValue))
				if dataColumn.button(buttonLabel or "선택", key=f"movieSelect_{rowIndex}", use_container_width=True):
					_setSelectedMovie(row)
					st.rerun()
			else:
				dataColumn.write("" if cellValue is None else _formatReleaseDate(cellValue) if col in ("repRlsDate", "releaseDate") else str(cellValue))

		movieTitle = str(row.get("title", ""))
		movieId = rowMovieId
		with dataColumns[-1]:
			with st.popover("⋮", use_container_width=True):
				if st.button("리뷰등록", key=f"movieReview_{rowIndex}", use_container_width=True):
					_setSelectedMovie(row)
					_openDialog("review", row)
					st.rerun()
				if st.button("영화수정", key=f"movieEdit_{rowIndex}", use_container_width=True):
					_setSelectedMovie(row)
					_openDialog("edit", row)
					st.rerun()


				# 삭제 버튼 클릭 시 session_state에 삭제 대상 저장
				if st.button("영화삭제", key=f"movieDelete_{movieId}", use_container_width=True):
					st.session_state["deleteMovieId"] = movieId
					st.session_state["deleteMovieTitle"] = movieTitle
					st.rerun()

				# 삭제 확인 UI
				if st.session_state.get("deleteMovieId") == movieId:
					st.warning("삭제하시겠습니까?")
					col_confirm, col_cancel = st.columns([1,1])
					with col_confirm:
						if st.button("확인", key=f"movieDeleteConfirm_{movieId}"):
							with LoadingPopup("영화 삭제 중입니다..."):
								deleteResult = callApi.deleteMovie(movieId)
							if deleteResult.get("ok"):
								_refreshTotalCount(callApi)
								st.session_state.pop("selectedMovieRow", None)
								st.session_state.pop("deleteMovieId", None)
								st.session_state.pop("deleteMovieTitle", None)
								_setActionMessage(f"영화 삭제 완료: {movieTitle}")
								st.rerun()
							else:
								st.error(deleteResult.get("error", "영화 삭제에 실패했습니다."))
					with col_cancel:
						if st.button("취소", key=f"movieDeleteCancel_{movieId}"):
							st.session_state.pop("deleteMovieId", None)
							st.session_state.pop("deleteMovieTitle", None)
							st.rerun()


def _renderReviewPanel(callApi: CallApi) -> None:
	st.subheader("영화별 리뷰 목록")
	selectedRow = _getSelectedMovie()
	if selectedRow is None:
		st.info("왼쪽 영화 목록에서 영화를 선택하세요.")
		return

	selectedMovieId = int(selectedRow.get("movieId", 0) or 0)
	selectedMovieTitle = str(selectedRow.get("title", ""))
	st.caption(f"선택 영화: {selectedMovieTitle} (movieId: {selectedMovieId})")

	current_review_cache_key = f"review_list_{selectedMovieId}"
	if "movieReviewListCacheKey" not in st.session_state or st.session_state["movieReviewListCacheKey"] != current_review_cache_key:
		with LoadingPopup("리뷰 목록을 불러오는 중입니다..."):
			reviewResult = callApi.getReviews(selectedMovieId)
			st.session_state["movieReviewListCacheResult"] = reviewResult
			st.session_state["movieReviewListCacheKey"] = current_review_cache_key
	else:
		reviewResult = st.session_state["movieReviewListCacheResult"]

	if not reviewResult.get("ok"):
		st.error(reviewResult.get("error", "리뷰 목록 조회에 실패했습니다."))
		return

	reviewRows = reviewResult.get("rows")
	if not reviewRows:
		st.info("등록된 리뷰가 없습니다.")
		return
	for reviewRow in reviewRows:
		reviewId = int(reviewRow.get("reviewId", 0) or 0)
		with st.container(border=True):
			reviewAuthor = str(reviewRow.get("authorName", ""))
			reviewCreatedAt = str(reviewRow.get("createdAt", ""))
			reviewLabel = str(reviewRow.get("sentimentLabel", ""))
			reviewScore = reviewRow.get("sentimentScore", "")
			reviewContent = str(reviewRow.get("content", ""))
			st.markdown(f"**{reviewAuthor}**")
			st.caption(f"감성: {reviewLabel} / 점수: {reviewScore} / 작성일: {reviewCreatedAt}")
			st.write(reviewContent)

			# 수정/삭제 버튼 영역 (한 줄에 Streamlit columns로)
			col1, col2, _ = st.columns([1, 1, 8])
			with col1:
				if st.button("수정", key=f"reviewEditBtn_{reviewId}"):
					st.session_state["editReviewId_movie"] = reviewId
					st.session_state["editReviewContent_movie"] = reviewContent
					st.session_state["editReviewAuthor_movie"] = reviewAuthor
			with col2:
				if st.button("삭제", key=f"reviewDeleteBtn_{reviewId}"):
					st.session_state["deleteReviewId_movie"] = reviewId

			# 리뷰 수정 폼 (해당 리뷰 아래에만 노출)
			if st.session_state.get("editReviewId_movie") == reviewId:
				with st.form(f"reviewEditForm_{reviewId}"):
					newContent = st.text_area("리뷰 내용", value=st.session_state.get("editReviewContent_movie", reviewContent), height=120)
					newAuthor = st.text_input("작성자", value=st.session_state.get("editReviewAuthor_movie", reviewAuthor))
					submitEdit = st.form_submit_button("수정 완료")
					cancelEdit = st.form_submit_button("취소")
					if submitEdit:
						with LoadingPopup("리뷰 수정 중입니다..."):
							editResult = callApi.editReview(reviewId, newAuthor, newContent)
						if editResult.get("ok"):
							st.session_state.pop("movieReviewListCacheKey", None)
							_setActionMessage("리뷰 수정 완료")
							st.session_state.pop("editReviewId_movie", None)
							st.rerun()
						else:
							st.error(editResult.get("error", "리뷰 수정에 실패했습니다."))
					if cancelEdit:
						st.session_state.pop("editReviewId_movie", None)
						st.rerun()

			# 리뷰 삭제 확인 및 실행
			if st.session_state.get("deleteReviewId_movie") == reviewId:
				st.warning("정말 삭제하시겠습니까?")
				col_confirm, col_cancel = st.columns([1,1])
				with col_confirm:
					if st.button("삭제 확정", key=f"reviewDeleteConfirm_{reviewId}"):
						with LoadingPopup("리뷰 삭제 중입니다..."):
							deleteResult = callApi.deleteReview(reviewId)
						if deleteResult.get("ok"):
							st.session_state.pop("movieReviewListCacheKey", None)
							_setActionMessage("리뷰 삭제 완료")
							st.session_state.pop("deleteReviewId_movie", None)
							st.rerun()
						else:
							st.error(deleteResult.get("error", "리뷰 삭제에 실패했습니다."))
				with col_cancel:
					if st.button("취소", key=f"reviewDeleteCancel_{reviewId}"):
						st.session_state.pop("deleteReviewId_movie", None)
						st.rerun()

def _renderPagination(currentPage: int, totalPages: int, totalCount: int) -> None:
	pageGroupStart = ((currentPage - 1) // PAGE_GROUP_SIZE) * PAGE_GROUP_SIZE + 1
	pageGroupEnd = min(totalPages, pageGroupStart + PAGE_GROUP_SIZE - 1)
	pageNumberList = list(range(pageGroupStart, pageGroupEnd + 1))

	canGoPrevGroup = pageGroupStart > 1
	canGoNextGroup = pageGroupEnd < totalPages

	controlColumns = st.columns(2 + len(pageNumberList) + 2)

	if controlColumns[0].button("<<", key="moviePageFirst", disabled=currentPage <= 1):
		_setCurrentPage(1)
		st.rerun()

	if controlColumns[1].button("<", key="moviePagePrev", disabled=not canGoPrevGroup):
		_setCurrentPage(pageGroupStart - 1)
		st.rerun()

	for indexValue, pageValue in enumerate(pageNumberList):
		buttonLabel = f"**[{pageValue}]**" if pageValue == currentPage else str(pageValue)
		if controlColumns[2 + indexValue].button(buttonLabel, key=f"moviePage_{pageValue}"):
			_setCurrentPage(pageValue)
			st.rerun()

	if controlColumns[2 + len(pageNumberList)].button(">", key="moviePageNext", disabled=not canGoNextGroup):
		_setCurrentPage(pageGroupEnd + 1)
		st.rerun()

	if controlColumns[3 + len(pageNumberList)].button(">>", key="moviePageLast", disabled=currentPage >= totalPages):
		_setCurrentPage(totalPages)
		st.rerun()

	st.caption(f"현재 페이지: {currentPage} / {totalPages} (총 {totalCount}건)")

st.subheader("영화 목록")
_ensureSearchDefaults()

with st.form("movieSearchForm", clear_on_submit=False):
	titleColumns = st.columns([2, 2, 2, 6])
	titleColumns[0].markdown("**영화제목**")
	titleColumns[1].markdown("**감독**")
	titleColumns[2].markdown("**배우**")
	with titleColumns[3]:
		st.checkbox("개봉일", key="movieSearchUseReleaseRange")

	inputColumns = st.columns([2, 2, 2, 6])
	inputColumns[0].text_input("영화제목", key="movieSearchTitle", label_visibility="collapsed")
	inputColumns[1].text_input("감독", key="movieSearchDirector", label_visibility="collapsed")
	inputColumns[2].text_input("배우", key="movieSearchActor", label_visibility="collapsed")

	with inputColumns[3]:
		dateColumns = st.columns([2.4, 0.3, 2.4])
		dateColumns[0].date_input(
			"개봉일시작",
			key="movieSearchStartDate",
			format="YYYY-MM-DD",
			min_value=date(1900, 1, 1),
			max_value=date(2100, 12, 31),
			label_visibility="collapsed",
			disabled=not bool(st.session_state.get("movieSearchUseReleaseRange", True)),
		)
		dateColumns[1].markdown("<div style='text-align:center;padding-top:0.45rem;'>~</div>", unsafe_allow_html=True)
		dateColumns[2].date_input(
			"개봉일종료",
			key="movieSearchEndDate",
			format="YYYY-MM-DD",
			min_value=date(1900, 1, 1),
			max_value=date(2100, 12, 31),
			label_visibility="collapsed",
			disabled=not bool(st.session_state.get("movieSearchUseReleaseRange", True)),
		)

	submitCols = st.columns([1, 1, 8])
	with submitCols[0]:
		searchClicked = st.form_submit_button("조회", use_container_width=True)
	with submitCols[1]:
		addClicked = st.form_submit_button("영화 추가", use_container_width=True)

if addClicked:
	_openDialog("create")
	st.rerun()

actionMessage = st.session_state.get("movieListActionMessage", "")
if actionMessage:
	st.info(actionMessage)

callApi = CallApi()
searchFilters = _getSearchFilters()

dialogType = st.session_state.get("movieDialogType")
dialogRow = st.session_state.get("movieDialogRow")
if dialogType == "create":
	_showCreateMovieDialog(callApi)
elif dialogType == "edit" and isinstance(dialogRow, dict):
	_showEditMovieDialog(callApi, dialogRow)
elif dialogType == "review" and isinstance(dialogRow, dict):
	_showCreateReviewDialog(callApi, dialogRow)

if searchClicked:
	_setCurrentPage(1)

# 초기 로드이거나 조회 버튼 클릭 시 총 건수 조회
if searchClicked or "movieListTotalCount" not in st.session_state:
	with LoadingPopup("영화 건수를 확인 중입니다..."):
		countResult = callApi.getMoviesCount(searchFilters)
	if countResult.get("ok"):
		st.session_state["movieListTotalCount"] = max(0, int(countResult.get("totalCount", 0)))
	else:
		st.session_state["movieListTotalCount"] = 0

totalCount = int(st.session_state.get("movieListTotalCount", 0))
totalPages = max(1, math.ceil(totalCount / PAGE_SIZE))
currentPage = _getCurrentPage()
if currentPage > totalPages:
	currentPage = totalPages
	_setCurrentPage(currentPage)
startValue = (currentPage - 1) * PAGE_SIZE

current_cache_key = f"movie_list_{currentPage}_{PAGE_SIZE}_{searchFilters}"
if searchClicked or "movieListCacheKey" not in st.session_state or st.session_state["movieListCacheKey"] != current_cache_key:
	with LoadingPopup("영화 목록을 불러오는 중입니다..."):
		result = callApi.getMovies(countValue=PAGE_SIZE, startValue=startValue, filtersData=searchFilters)
		st.session_state["movieListCacheResult"] = result
		st.session_state["movieListCacheKey"] = current_cache_key
else:
	result = st.session_state["movieListCacheResult"]

if not result.get("ok"):
	st.error(result.get("error", "알 수 없는 오류가 발생했습니다."))
	if result.get("text"):
		st.text(result["text"])
else:
	rows = result.get("rows")
	dataList = result.get("dataList")

	if rows is not None:
		if len(rows) > 0:
			if isinstance(rows[0], dict):
				_syncSelectedMovie(rows)
				columnTitleMap = _getColumnTitleMap()
				displayColumns = ["title", "directorNm", "actorNm", "repRlsDate"]
				leftColumn, rightColumn = st.columns(2)
				with leftColumn:
					_renderMovieTable(callApi, rows, displayColumns, columnTitleMap)
					_renderPagination(currentPage, totalPages, totalCount)
				with rightColumn:
					_renderReviewPanel(callApi)
			else:
				st.dataframe([{"value": item} for item in rows], use_container_width=True)
		else:
			st.info("데이터가 없습니다.")
	elif dataList is not None:
		st.warning(f"datalist 타입({type(dataList).__name__})을 표로 변환하지 못했습니다.")
	else:
		st.info("응답 JSON에 datalist 항목이 없습니다.")

