import math
from calendar import monthrange
from datetime import date, datetime

import streamlit as st

from call_api import CallApi
from loading_popup import LoadingPopup

PAGE_SIZE = 10
PAGE_GROUP_SIZE = 5


def _getCurrentPage() -> int:
	if "reviewListPage" not in st.session_state:
		st.session_state["reviewListPage"] = 1
	return int(st.session_state["reviewListPage"])


def _setCurrentPage(pageValue: int) -> None:
	st.session_state["reviewListPage"] = max(1, int(pageValue))


def _setActionMessage(messageText: str) -> None:
	st.session_state["reviewListActionMessage"] = messageText


def _addMonths(baseDate: date, monthDiff: int) -> date:
	totalMonth = (baseDate.month - 1) + monthDiff
	newYear = baseDate.year + (totalMonth // 12)
	newMonth = (totalMonth % 12) + 1
	maxDay = monthrange(newYear, newMonth)[1]
	newDay = min(baseDate.day, maxDay)
	return date(newYear, newMonth, newDay)


def _ensureSearchDefaults() -> None:
	todayValue = date.today()
	if "reviewSearchMovieTitle" not in st.session_state:
		st.session_state["reviewSearchMovieTitle"] = ""
	if "reviewSearchAuthorName" not in st.session_state:
		st.session_state["reviewSearchAuthorName"] = ""
	if "reviewSearchContent" not in st.session_state:
		st.session_state["reviewSearchContent"] = ""
	if "reviewSearchSentimentLabel" not in st.session_state:
		st.session_state["reviewSearchSentimentLabel"] = "all"
	if "reviewSearchSentimentScore" not in st.session_state:
		st.session_state["reviewSearchSentimentScore"] = "all"
	if "reviewSearchUseDateRange" not in st.session_state:
		st.session_state["reviewSearchUseDateRange"] = True
	if "reviewSearchStartDate" not in st.session_state:
		st.session_state["reviewSearchStartDate"] = _addMonths(todayValue, -3)
	if "reviewSearchEndDate" not in st.session_state:
		st.session_state["reviewSearchEndDate"] = _addMonths(todayValue, 3)
	if "reviewSearchMovieTitle" not in st.session_state:
		st.session_state["reviewSearchMovieTitle"] = ""
	if "reviewSearchAuthorName" not in st.session_state:
		st.session_state["reviewSearchAuthorName"] = ""
	if "reviewSearchContent" not in st.session_state:
		st.session_state["reviewSearchContent"] = ""


def _getSearchFilters() -> dict[str, str]:
	useDateRange = bool(st.session_state.get("reviewSearchUseDateRange", True))
	startDateValue = st.session_state.get("reviewSearchStartDate")
	endDateValue = st.session_state.get("reviewSearchEndDate")
	return {
		"movieTitle": str(st.session_state.get("reviewSearchMovieTitle", "") or "").strip(),
		"authorName": str(st.session_state.get("reviewSearchAuthorName", "") or "").strip(),
		"content": str(st.session_state.get("reviewSearchContent", "") or "").strip(),
		"sentimentLabel": str(st.session_state.get("reviewSearchSentimentLabel", "all")),
		"sentimentScore": str(st.session_state.get("reviewSearchSentimentScore", "all")),
		"createdStart": startDateValue.isoformat() if useDateRange and isinstance(startDateValue, date) else "",
		"createdEnd": endDateValue.isoformat() if useDateRange and isinstance(endDateValue, date) else "",
	}


def _refreshTotalCount(callApi: CallApi) -> None:
	with LoadingPopup("리뷰 데이터를 집계 중입니다..."):
		countResult = callApi.getAllReviewsCount(_getSearchFilters())
	if countResult.get("ok"):
		st.session_state["reviewListTotalCount"] = max(0, int(countResult.get("totalCount", 0)))
	st.session_state.pop("reviewListCacheKey", None)


def _renderReviewTable(callApi: CallApi, rows: list[dict]) -> None:
	headerColumns = st.columns([2, 2, 4, 2, 2, 2, 1])
	headerLabels = ["영화명", "작성자", "내용", "감성", "점수", "등록일", "관리"]
	for headerColumn, label in zip(headerColumns, headerLabels):
		headerColumn.markdown(f"**{label}**")

	st.divider()

	for rowIndex, row in enumerate(rows):
		dataColumns = st.columns([2, 2, 4, 2, 2, 2, 1])
		movieTitle = str(row.get("movieTitle", ""))
		authorName = str(row.get("authorName", ""))
		content = str(row.get("content", ""))
		contentShort = content[:40] + "..." if len(content) > 40 else content
		sentimentLabel = str(row.get("sentimentLabel", ""))
		sentimentScore = row.get("sentimentScore", "")
		try:
			sentimentScore = int(float(sentimentScore))
		except (ValueError, TypeError):
			sentimentScore = ""
		createdAt = str(row.get("createdAt", ""))[:19]
		reviewId = int(row.get("reviewId", 0) or 0)

		dataColumns[0].write(movieTitle)
		dataColumns[1].write(authorName)
		dataColumns[2].write(contentShort)
		dataColumns[3].write(sentimentLabel)
		dataColumns[4].write(str(sentimentScore))
		dataColumns[5].write(createdAt)
		with dataColumns[6]:
			with st.popover("⋮", use_container_width=True):
				# 삭제 버튼은 reviewId 기준으로 한 번만 생성
				if st.button("리뷰삭제", key=f"reviewDelete_{reviewId}", use_container_width=True):
					st.session_state["deleteReviewId"] = reviewId
					st.session_state["deleteReviewContent"] = contentShort
					st.rerun()

				# 삭제 확인 UI
				if st.session_state.get("deleteReviewId") == reviewId:
					st.warning("삭제하시겠습니까?")
					col_confirm, col_cancel = st.columns([1,1])
					with col_confirm:
						if st.button("확인", key=f"reviewDeleteConfirm_{reviewId}"):
							with LoadingPopup("리뷰 삭제 중입니다..."):
								deleteResult = callApi.deleteReview(reviewId)
							if deleteResult.get("ok"):
								st.session_state.pop("reviewListCacheKey", None)
								_refreshTotalCount(callApi)
								_setActionMessage("리뷰 삭제 완료")
								st.session_state.pop("deleteReviewId", None)
								st.session_state.pop("deleteReviewContent", None)
								st.rerun()
							else:
								st.error(deleteResult.get("error", "리뷰 삭제에 실패했습니다."))
					with col_cancel:
						if st.button("취소", key=f"reviewDeleteCancel_{reviewId}"):
							st.session_state.pop("deleteReviewId", None)
							st.session_state.pop("deleteReviewContent", None)
							st.rerun()

				# ── 리뷰 수정 버튼 및 폼 ──
				if st.button("리뷰수정", key=f"reviewEdit_{rowIndex}", use_container_width=True):
					st.session_state["editReviewId"] = reviewId
					st.session_state["editReviewContent"] = content
					st.session_state["editReviewScore"] = sentimentScore
					st.session_state["editReviewLabel"] = sentimentLabel
					st.session_state["editReviewMovieTitle"] = movieTitle
					st.session_state["editReviewAuthorName"] = authorName
					st.session_state["editReviewRowIndex"] = rowIndex

		# 리뷰 수정 폼 (리스트 하단에 노출)
if "editReviewId" in st.session_state:
	with st.form("reviewEditForm"):
		st.subheader(f"리뷰 수정: {st.session_state.get('editReviewMovieTitle', '')}")
		newContent = st.text_area("리뷰 내용", value=st.session_state.get("editReviewContent", ""), height=120)
		newAuthor = st.text_input("작성자", value=st.session_state.get("editReviewAuthorName", ""))
		submitEdit = st.form_submit_button("수정 완료")
		cancelEdit = st.form_submit_button("취소")
		if submitEdit:
			with LoadingPopup("리뷰 수정 중입니다..."):
				editResult = callApi.editReview(
					st.session_state["editReviewId"],
					newAuthor,
					newContent
				)
			if editResult.get("ok"):
				st.session_state.pop("reviewListCacheKey", None)
				_setActionMessage("리뷰 수정 완료")
				_refreshTotalCount(callApi)
				st.session_state.pop("editReviewId", None)
				st.rerun()
			else:
				st.error(editResult.get("error", "리뷰 수정에 실패했습니다."))
		if cancelEdit:
			st.session_state.pop("editReviewId", None)
			st.rerun()


def _renderPagination(currentPage: int, totalPages: int, totalCount: int) -> None:
	pageGroupStart = ((currentPage - 1) // PAGE_GROUP_SIZE) * PAGE_GROUP_SIZE + 1
	pageGroupEnd = min(totalPages, pageGroupStart + PAGE_GROUP_SIZE - 1)
	pageNumberList = list(range(pageGroupStart, pageGroupEnd + 1))

	canGoPrevGroup = pageGroupStart > 1
	canGoNextGroup = pageGroupEnd < totalPages

	controlColumns = st.columns(2 + len(pageNumberList) + 2)

	if controlColumns[0].button("<<", key="reviewPageFirst", disabled=currentPage <= 1):
		_setCurrentPage(1)
		st.rerun()

	if controlColumns[1].button("<", key="reviewPagePrev", disabled=not canGoPrevGroup):
		_setCurrentPage(pageGroupStart - 1)
		st.rerun()

	for indexValue, pageValue in enumerate(pageNumberList):
		buttonLabel = f"**[{pageValue}]**" if pageValue == currentPage else str(pageValue)
		if controlColumns[2 + indexValue].button(buttonLabel, key=f"reviewPage_{pageValue}"):
			_setCurrentPage(pageValue)
			st.rerun()

	if controlColumns[2 + len(pageNumberList)].button(">", key="reviewPageNext", disabled=not canGoNextGroup):
		_setCurrentPage(pageGroupEnd + 1)
		st.rerun()

	if controlColumns[3 + len(pageNumberList)].button(">>", key="reviewPageLast", disabled=currentPage >= totalPages):
		_setCurrentPage(totalPages)
		st.rerun()

	st.caption(f"현재 페이지: {currentPage} / {totalPages} (총 {totalCount}건)")


# ── 페이지 진입점 ──────────────────────────────────────────────────────────────

st.subheader("리뷰 목록")
_ensureSearchDefaults()

with st.form("reviewSearchForm", clear_on_submit=False):
	titleColumns = st.columns([1.5, 1.5, 3, 1.5, 1.5, 4.5])
	titleColumns[0].markdown("**영화명**")
	titleColumns[1].markdown("**작성자**")
	titleColumns[2].markdown("**내용**")
	titleColumns[3].markdown("**감성**")
	titleColumns[4].markdown("**점수**")
	with titleColumns[5]:
		st.checkbox("등록일", key="reviewSearchUseDateRange")

	inputColumns = st.columns([1.5, 1.5, 3, 1.5, 1.5, 4.5])
	inputColumns[0].text_input("영화명", key="reviewSearchMovieTitle", label_visibility="collapsed")
	inputColumns[1].text_input("작성자", key="reviewSearchAuthorName", label_visibility="collapsed")
	inputColumns[2].text_input("내용", key="reviewSearchContent", label_visibility="collapsed")
	inputColumns[3].selectbox("감성", options=["all", "positive", "neutral", "negative"], key="reviewSearchSentimentLabel", label_visibility="collapsed")
	inputColumns[4].selectbox("점수", options=["all", "1", "2", "3", "4", "5"], key="reviewSearchSentimentScore", label_visibility="collapsed")
	
	with inputColumns[5]:
		dateColumns = st.columns([2.4, 0.3, 2.4])
		dateColumns[0].date_input(
			"시작일",
			key="reviewSearchStartDate",
			format="YYYY-MM-DD",
			label_visibility="collapsed",
			disabled=not bool(st.session_state.get("reviewSearchUseDateRange", True)),
		)
		dateColumns[1].markdown("<div style='text-align:center;padding-top:0.45rem;'>~</div>", unsafe_allow_html=True)
		dateColumns[2].date_input(
			"종료일",
			key="reviewSearchEndDate",
			format="YYYY-MM-DD",
			label_visibility="collapsed",
			disabled=not bool(st.session_state.get("reviewSearchUseDateRange", True)),
		)

	searchClicked = st.form_submit_button("조회", use_container_width=False)

actionMessage = st.session_state.get("reviewListActionMessage", "")
if actionMessage:
	st.info(actionMessage)
	st.session_state["reviewListActionMessage"] = ""

callApi = CallApi()
searchFilters = _getSearchFilters()

if searchClicked:
	_setCurrentPage(1)

if searchClicked or "reviewListTotalCount" not in st.session_state:
	with LoadingPopup("리뷰 건수를 확인 중입니다..."):
		countResult = callApi.getAllReviewsCount(searchFilters)
	if countResult.get("ok"):
		st.session_state["reviewListTotalCount"] = max(0, int(countResult.get("totalCount", 0)))
	else:
		st.session_state["reviewListTotalCount"] = 0

totalCount = int(st.session_state.get("reviewListTotalCount", 0))
totalPages = max(1, math.ceil(totalCount / PAGE_SIZE))
currentPage = _getCurrentPage()
if currentPage > totalPages:
	currentPage = totalPages
	_setCurrentPage(currentPage)
startValue = (currentPage - 1) * PAGE_SIZE

current_cache_key = f"review_list_{currentPage}_{PAGE_SIZE}_{searchFilters}"
if searchClicked or "reviewListCacheKey" not in st.session_state or st.session_state["reviewListCacheKey"] != current_cache_key:
	with LoadingPopup("리뷰 목록을 불러오는 중입니다..."):
		result = callApi.getAllReviews(countValue=PAGE_SIZE, startValue=startValue, filtersData=searchFilters)
		st.session_state["reviewListCacheResult"] = result
		st.session_state["reviewListCacheKey"] = current_cache_key
else:
	result = st.session_state["reviewListCacheResult"]

if not result.get("ok"):
	st.error(result.get("error", "알 수 없는 오류가 발생했습니다."))
else:
	rows = result.get("rows")
	if rows:
		_renderReviewTable(callApi, rows)
		_renderPagination(currentPage, totalPages, totalCount)
	else:
		st.info("등록된 리뷰가 없습니다.")

