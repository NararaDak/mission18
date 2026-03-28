# 전체 리뷰 목록 조회 및 필터링, 통합 관리를 담당하는 페이지 스크립트
import math
from calendar import monthrange
from datetime import date, datetime
import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup
from common.review_dialogs import show_edit_review_dialog, show_delete_review_dialog

# 페이지네이션 설정
PAGE_SIZE = 10
PAGE_GROUP_SIZE = 5

# 현재 리뷰 목록 페이지 번호 조회
def _getCurrentPage() -> int:
	if "rl_reviewListPage" not in st.session_state: st.session_state["rl_reviewListPage"] = 1
	return int(st.session_state["rl_reviewListPage"])

# 현재 리뷰 목록 페이지 번호 저장
def _setCurrentPage(page: int) -> None:
	st.session_state["rl_reviewListPage"] = max(1, int(page))

# 알림 메시지 설정
def _setActionMessage(msg: str) -> None:
	st.session_state["rl_reviewListActionMessage"] = msg

# 특정 개월 수를 더하거나 뺀 날짜 반환
def _addMonths(base: date, diff: int) -> date:
	totalMonth = (base.month - 1) + diff
	yy, mm = base.year + (totalMonth // 12), (totalMonth % 12) + 1
	return date(yy, mm, min(base.day, monthrange(yy, mm)[1]))

# 검색 필터 초기값 보장
def _ensureSearchDefaults() -> None:
	today = date.today()
	if "rl_SearchMovieTitle" not in st.session_state: st.session_state["rl_SearchMovieTitle"] = ""
	if "rl_SearchAuthorName" not in st.session_state: st.session_state["rl_SearchAuthorName"] = ""
	if "rl_SearchContent" not in st.session_state: st.session_state["rl_SearchContent"] = ""
	if "rl_SearchSentimentLabel" not in st.session_state: st.session_state["rl_SearchSentimentLabel"] = "all"
	if "rl_SearchSentimentScore" not in st.session_state: st.session_state["rl_SearchSentimentScore"] = "all"
	if "rl_SearchUseDateRange" not in st.session_state: st.session_state["rl_SearchUseDateRange"] = False
	if "rl_SearchStartDate" not in st.session_state: st.session_state["rl_SearchStartDate"] = _addMonths(today, -3)
	if "rl_SearchEndDate" not in st.session_state: st.session_state["rl_SearchEndDate"] = _addMonths(today, 0)

# API 요청을 위한 필터 딕셔너리 생성
def _getSearchFilters() -> dict[str, str]:
	useDateRange = bool(st.session_state.get("rl_SearchUseDateRange", True))
	start, end = st.session_state.get("rl_SearchStartDate"), st.session_state.get("rl_SearchEndDate")
	return {
		"movieTitle": str(st.session_state.get("rl_SearchMovieTitle", "")).strip(),
		"authorName": str(st.session_state.get("rl_SearchAuthorName", "")).strip(),
		"content": str(st.session_state.get("rl_SearchContent", "")).strip(),
		"sentimentLabel": str(st.session_state.get("rl_SearchSentimentLabel", "all")),
		"sentimentScore": str(st.session_state.get("rl_SearchSentimentScore", "all")),
		"createdStart": start.isoformat() if useDateRange and isinstance(start, date) else "",
		"createdEnd": end.isoformat() if useDateRange and isinstance(end, date) else "",
	}

# 전체 리뷰 건수 갱신
def _refreshTotalCount(api: CallApi) -> None:
	with LoadingPopup("집계 중..."):
		res = api.getAllReviewsCount(_getSearchFilters())
	if res.get("ok"):
		st.session_state["rl_reviewListTotalCount"] = max(0, int(res.get("totalCount", 0)))
	st.session_state.pop("rl_reviewListCacheKey", None)


# 리뷰 등록 다이얼로그
@st.dialog("리뷰 등록", width="large")
def _showCreateReviewDialog(api: CallApi) -> None:
	st.subheader("리뷰 등록")
	with st.form("rl_reviewCreateForm_dialog"):
		userName = st.session_state.get("user_name", "")
		st.write(f"**작성자:** {userName}")
		movieTitle = st.session_state.get("rl_createReviewMovieTitle", "")
		st.write(f"**영화명:** {movieTitle}")
		content = st.text_area("내용", height=120)
		c1, c2 = st.columns(2)
		if c1.form_submit_button("등록 완료", use_container_width=True):
			userId = st.session_state.get("user_id", "")
			movieId = st.session_state.get("rl_createReviewMovieId", 0)
			with LoadingPopup("등록 중..."):
				res = api.createReview(movieId, userName, content, userId=userId)
			if res.get("ok"):
				st.session_state.pop("rl_reviewListCacheKey", None)
				_refreshTotalCount(api)
				_setActionMessage("리뷰가 등록되었습니다.")
				st.session_state.pop("rl_dialogType", None)
				st.session_state.pop("rl_dialogData", None)
				st.session_state.pop("rl_createReviewMovieId", None)
				st.session_state.pop("rl_createReviewMovieTitle", None)
				st.rerun()
			else:
				st.error(res.get("error", "등록 실패"))
		if c2.form_submit_button("취소", use_container_width=True):
			st.session_state.pop("rl_dialogType", None)
			st.session_state.pop("rl_dialogData", None)
			st.session_state.pop("rl_createReviewMovieId", None)
			st.session_state.pop("rl_createReviewMovieTitle", None)
			st.rerun()

# --- API 초기화 ---
api = CallApi()

# 다이얼로그 노출 처리
rl_dtype = st.session_state.get("rl_dialogType")
rl_drow = st.session_state.get("rl_dialogData")
if rl_dtype == "edit" and rl_drow:
    def _edit_success():
        st.session_state.pop("rl_reviewListCacheKey", None)
        _setActionMessage("리뷰가 수정되었습니다.")
        st.session_state.pop("rl_dialogType", None)
        st.session_state.pop("rl_dialogData", None)
        st.rerun()
    def _edit_cancel():
        st.session_state.pop("rl_dialogType", None)
        st.session_state.pop("rl_dialogData", None)
        st.rerun()
    show_edit_review_dialog(
        api,
        int(rl_drow.get("reviewId", 0)),
        str(rl_drow.get("content", "")),
        str(rl_drow.get("authorName", "")),
        str(rl_drow.get("movieTitle", "")),
        on_success=_edit_success,
        on_cancel=_edit_cancel
    )
elif rl_dtype == "delete" and rl_drow:
    def _del_success():
        st.session_state.pop("rl_reviewListCacheKey", None)
        _refreshTotalCount(api)
        _setActionMessage("리뷰가 삭제되었습니다.")
        st.session_state.pop("rl_dialogType", None)
        st.session_state.pop("rl_dialogData", None)
        st.rerun()
    def _del_cancel():
        st.session_state.pop("rl_dialogType", None)
        st.session_state.pop("rl_dialogData", None)
        st.rerun()
    show_delete_review_dialog(
        api,
        int(rl_drow.get("reviewId", 0)),
        rl_drow.get("movieTitle", None),
        on_success=_del_success,
        on_cancel=_del_cancel
    )
elif rl_dtype == "create":
	_showCreateReviewDialog(api)

# --- 메인 렌더링 시작 ---
st.subheader("전체 리뷰 목록")
_ensureSearchDefaults()

# 검색 필터 UI
tCols = st.columns([2, 1.5, 2, 1.5, 1.5, 3.5])
tCols[0].markdown("**영화명**")
tCols[1].markdown("**작성자**")
tCols[2].markdown("**내용**")
tCols[3].markdown("**감정**")
tCols[4].markdown("**평가점수**")
with tCols[5]:
	st.checkbox("등록일", key="rl_SearchUseDateRange")

iCols = st.columns([2, 1.5, 2, 1.5, 1.5, 3.5])
iCols[0].text_input("영화명", key="rl_SearchMovieTitle", label_visibility="collapsed")
iCols[1].text_input("작성자", key="rl_SearchAuthorName", label_visibility="collapsed")
iCols[2].text_input("내용", key="rl_SearchContent", label_visibility="collapsed")
iCols[3].selectbox("감정", ["all", "positive", "neutral", "negative"], key="rl_SearchSentimentLabel", label_visibility="collapsed")
iCols[4].selectbox("점수", ["all", "1", "2", "3", "4", "5"], key="rl_SearchSentimentScore", label_visibility="collapsed")
with iCols[5]:
	dCols = st.columns([2.4, 0.3, 2.4])
	dCols[0].date_input("시작", key="rl_SearchStartDate", format="YYYY-MM-DD", min_value=date(1900,1,1), max_value=date(2100,12,31), label_visibility="collapsed", disabled=not st.session_state.get("rl_SearchUseDateRange"))
	dCols[1].markdown("<div style='text-align:center;padding-top:0.45rem;'>~</div>", unsafe_allow_html=True)
	dCols[2].date_input("종료", key="rl_SearchEndDate", format="YYYY-MM-DD", min_value=date(1900,1,1), max_value=date(2100,12,31), label_visibility="collapsed", disabled=not st.session_state.get("rl_SearchUseDateRange"))

with st.form("rl_searchForm"):
	btnCols = st.columns([1, 1, 8])
	srchClicked = btnCols[0].form_submit_button("조회", use_container_width=True)

current_filters = _getSearchFilters()
if "rl_AppliedFilters" not in st.session_state:
    st.session_state["rl_AppliedFilters"] = current_filters

if srchClicked:
    st.session_state["rl_AppliedFilters"] = current_filters
    _setCurrentPage(1)

applied_filters = st.session_state["rl_AppliedFilters"]

if srchClicked or "rl_reviewListTotalCount" not in st.session_state:
	with LoadingPopup("전체 건수 확인 중..."):
		countRes = api.getAllReviewsCount(applied_filters)
	st.session_state["rl_reviewListTotalCount"] = max(0, int(countRes.get("totalCount", 0))) if countRes.get("ok") else 0

totalC = int(st.session_state.get("rl_reviewListTotalCount", 0))
totalP = max(1, math.ceil(totalC / PAGE_SIZE))
currP = min(_getCurrentPage(), totalP)
_setCurrentPage(currP)

ckey = f"rl_review_list_{currP}_{PAGE_SIZE}_{applied_filters}"
cache_res = st.session_state.get("rl_reviewListCacheResult")
cache_key = st.session_state.get("rl_reviewListCacheKey")
if srchClicked:
	# 조회 버튼 클릭 시에만 API 호출 및 캐시 갱신
	with LoadingPopup("조회 중..."):
		res = api.getAllReviews(count=PAGE_SIZE, start=(currP-1)*PAGE_SIZE, filters=applied_filters)
		st.session_state["rl_reviewListCacheResult"], st.session_state["rl_reviewListCacheKey"] = res, ckey
else:
	# 조회 버튼 누르기 전에는 캐시 데이터만 사용
	if cache_res and cache_key == ckey:
		res = cache_res
	else:
		# 최초 진입 시 또는 페이지 이동 등으로 캐시 키가 다를 때
		with LoadingPopup("조회 중..."):
			res = api.getAllReviews(count=PAGE_SIZE, start=(currP-1)*PAGE_SIZE, filters=applied_filters)
			st.session_state["rl_reviewListCacheResult"], st.session_state["rl_reviewListCacheKey"] = res, ckey

def _renderPagination(curr: int, totalP: int, totalC: int) -> None:
	gStart = ((curr - 1) // PAGE_GROUP_SIZE) * PAGE_GROUP_SIZE + 1
	gEnd = min(totalP, gStart + PAGE_GROUP_SIZE - 1)
	pgs = list(range(gStart, gEnd + 1))
	ctrls = st.columns(2 + len(pgs) + 2)
	if ctrls[0].button("<<", key="rlPage_first", disabled=curr <= 1): _setCurrentPage(1); st.rerun()
	if ctrls[1].button("<", key="rlPage_prev", disabled=gStart <= 1): _setCurrentPage(gStart - 1); st.rerun()
	for i, p in enumerate(pgs):
		lbl = f"**[{p}]**" if p == curr else str(p)
		if ctrls[2+i].button(lbl, key=f"rlPage_{p}"): _setCurrentPage(p); st.rerun()
	if ctrls[2+len(pgs)].button(">", key="rlPage_next", disabled=gEnd >= totalP): _setCurrentPage(gEnd + 1); st.rerun()
	if ctrls[3+len(pgs)].button(">>", key="rlPage_last", disabled=curr >= totalP): _setCurrentPage(totalP); st.rerun()
	st.caption(f"페이지: {curr}/{totalP} (총 {totalC}건)")

def _renderReviewTable(api: CallApi, rows: list[dict]) -> None:
    header = st.columns([2, 1.5, 3.5, 1, 1, 1.5, 1])
    header[0].markdown("**영화명**")
    header[1].markdown("**작성자**")
    header[2].markdown("**내용**")
    header[3].markdown("**감정**")
    header[4].markdown("**평가점수**")
    header[5].markdown("**작성일**")
    header[6].markdown("**관리**")
    for i, row in enumerate(rows):
        cols = st.columns([2, 1.5, 3.5, 1, 1, 1.5, 1])
        cols[0].write(str(row.get("movieTitle", "")))
        cols[1].write(str(row.get("authorName", "")))
        cols[2].write(str(row.get("content", "")))
        cols[3].write(str(row.get("sentimentLabel", "")))
        cols[4].write(str(row.get("sentimentScore", "")))
        cols[5].write(str(row.get("createdAt", "")))
        with cols[6]:
            # 본인 또는 관리자만 수정/삭제 가능 (예시)
            userId = st.session_state.get("user_id", "")
            userName = st.session_state.get("user_name", "")
            rOwner = str(row.get("addedBy") or "").strip()
            if rOwner == userId or userName == "관리자":
                with st.popover("⋮", use_container_width=True):
                    if st.button("수정", key=f"rl_edit_{i}", use_container_width=True):
                        st.session_state["rl_dialogType"] = "edit"
                        st.session_state["rl_dialogData"] = row
                        st.rerun()
                    if st.button("삭제", key=f"rl_del_{i}", use_container_width=True):
                        st.session_state["rl_dialogType"] = "delete"
                        st.session_state["rl_dialogData"] = row
                        st.rerun()
            else:
                st.write("")
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

if not res.get("ok"):
	# API 실패 시 최근 성공 캐시라도 fallback
	if cache_res and cache_res.get("ok"):
		st.warning("API 오류, 최근 조회 데이터로 대체합니다.")
		rows = cache_res.get("rows")
	else:
		st.error("오류: 데이터 없음")
		st.info("최근 조회 데이터도 없습니다. 조건을 변경하거나 다시 시도해 주세요.")
		rows = []
else:
	rows = res.get("rows")
if rows:
	_renderReviewTable(api, rows)
	_renderPagination(currP, totalP, totalC)
else:
	st.info("데이터 없음")
