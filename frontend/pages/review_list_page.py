# 전체 리뷰 목록 조회 및 필터링, 통합 관리를 담당하는 페이지 스크립트
import math
from calendar import monthrange
from datetime import date, datetime
import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup

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

# 리뷰 목록 테이블 렌더링
def _renderReviewTable(api: CallApi, rows: list[dict]) -> None:
	cols = st.columns([2, 2, 4, 2, 2, 2, 1])
	for c, lbl in zip(cols, ["영화명", "작성자", "내용", "감성", "점수", "등록일", "관리"]):
		c.markdown(f"**{lbl}**")
	st.divider()

	for i, row in enumerate(rows):
		line = st.columns([2, 2, 4, 2, 2, 2, 1])
		rid = int(row.get("reviewId", 0))
		txt = str(row.get("content", ""))
		txtS = (txt[:40] + "...") if len(txt) > 40 else txt
		
		line[0].write(row.get("movieTitle", ""))
		line[1].write(row.get("authorName", ""))
		line[2].write(txtS)
		line[3].write(row.get("sentimentLabel", ""))
		try: sc = int(float(row.get("sentimentScore", 0)))
		except: sc = ""
		line[4].write(str(sc))
		line[5].write(str(row.get("createdAt", ""))[:19])

		with line[6]:
			with st.popover("⋮", use_container_width=True):
				if st.button("삭제", key=f"rl_revDel_{rid}_{i}", use_container_width=True):
					st.session_state["rl_delRid"] = rid
					st.rerun()
				if st.session_state.get("rl_delRid") == rid:
					st.warning("삭제?")
					if st.button("확인", key=f"rl_delOk_{rid}_{i}"):
						with LoadingPopup("삭제 중..."): res = api.deleteReview(rid)
						if res.get("ok"):
							st.session_state.pop("rl_reviewListCacheKey", None)
							_refreshTotalCount(api)
							st.session_state.pop("rl_delRid", None)
							st.rerun()
					if st.button("취소", key=f"rl_delNo_{rid}_{i}"):
						st.session_state.pop("rl_delRid", None)
						st.rerun()

				if st.button("수정", key=f"rl_revEdit_{rid}_{i}", use_container_width=True):
					st.session_state["rl_editRid"] = rid
					st.session_state["rl_editTxt"] = txt
					st.session_state["rl_editAuth"] = str(row.get("authorName", ""))
					st.session_state["rl_editTitle"] = str(row.get("movieTitle", ""))
					st.rerun()
		st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

if "rl_editRid" in st.session_state:
	with st.form("rl_reviewEditForm"):
		st.subheader(f"리뷰 수정: {st.session_state.get('rl_editTitle')}")
		newTxt = st.text_area("내용", value=st.session_state.get("rl_editTxt"), height=120)
		newAuth = st.text_input("작성자", value=st.session_state.get("rl_editAuth"))
		c1, c2 = st.columns(2)
		if c1.form_submit_button("수정 완료"):
			with LoadingPopup("수정 중..."):
				res = CallApi().editReview(st.session_state["rl_editRid"], newAuth, newTxt)
			if res.get("ok"):
				st.session_state.pop("rl_reviewListCacheKey", None)
				st.session_state.pop("rl_editRid", None)
				st.rerun()
			else: st.error("실패")
		if c2.form_submit_button("취소"):
			st.session_state.pop("rl_editRid", None)
			st.rerun()

def _renderPagination(curr: int, totalP: int, totalC: int) -> None:
	gStart = ((curr - 1) // PAGE_GROUP_SIZE) * PAGE_GROUP_SIZE + 1
	gEnd = min(totalP, gStart + PAGE_GROUP_SIZE - 1)
	pgs = list(range(gStart, gEnd + 1))
	ctrls = st.columns(2 + len(pgs) + 2)
	if ctrls[0].button("<<", key="rl_p_first", disabled=curr <= 1): _setCurrentPage(1); st.rerun()
	if ctrls[1].button("<", key="rl_p_prev", disabled=gStart <= 1): _setCurrentPage(gStart - 1); st.rerun()
	for i, p in enumerate(pgs):
		lbl = f"**[{p}]**" if p == curr else str(p)
		if ctrls[2+i].button(lbl, key=f"rl_p_{p}"): _setCurrentPage(p); st.rerun()
	if ctrls[2+len(pgs)].button(">", key="rl_p_next", disabled=gEnd >= totalP): _setCurrentPage(gEnd + 1); st.rerun()
	if ctrls[3+len(pgs)].button(">>", key="rl_p_last", disabled=curr >= totalP): _setCurrentPage(totalP); st.rerun()
	st.caption(f"페이지: {curr}/{totalP} (총 {totalC}건)")

st.subheader("리뷰 목록")
_ensureSearchDefaults()

with st.form("rl_reviewSearchForm"):
	tCols = st.columns([1.5, 1.5, 3, 1.5, 1.5, 4.5])
	tCols[0].markdown("**영화명**"); tCols[1].markdown("**작성자**"); tCols[2].markdown("**내용**"); tCols[3].markdown("**감성**"); tCols[4].markdown("**점수**")
	with tCols[5]: st.checkbox("등록일", key="rl_SearchUseDateRange")

	iCols = st.columns([1.5, 1.5, 3, 1.5, 1.5, 4.5])
	iCols[0].text_input("영화", key="rl_SearchMovieTitle", label_visibility="collapsed")
	iCols[1].text_input("작성자", key="rl_SearchAuthorName", label_visibility="collapsed")
	iCols[2].text_input("내용", key="rl_SearchContent", label_visibility="collapsed")
	iCols[3].selectbox("감성", options=["all", "positive", "neutral", "negative"], key="rl_SearchSentimentLabel", label_visibility="collapsed")
	iCols[4].selectbox("점수", options=["all", "1", "2", "3", "4", "5"], key="rl_SearchSentimentScore", label_visibility="collapsed")
	with iCols[5]:
		dCols = st.columns([2.4, 0.3, 2.4])
		dCols[0].date_input("시작", key="rl_SearchStartDate", format="YYYY-MM-DD", label_visibility="collapsed", disabled=not st.session_state.get("rl_SearchUseDateRange"))
		dCols[1].markdown("<div style='text-align:center;padding-top:0.45rem;'>~</div>", unsafe_allow_html=True)
		dCols[2].date_input("종료", key="rl_SearchEndDate", format="YYYY-MM-DD", label_visibility="collapsed", disabled=not st.session_state.get("rl_SearchUseDateRange"))

	srchClicked = st.form_submit_button("조회")

msg = st.session_state.get("rl_reviewListActionMessage", "")
if msg: st.info(msg); st.session_state["rl_reviewListActionMessage"] = ""

api = CallApi()
filters = _getSearchFilters()

if srchClicked or "rl_reviewListTotalCount" not in st.session_state:
	if srchClicked: _setCurrentPage(1)
	with LoadingPopup("전체 건수 확인 중..."):
		countRes = api.getAllReviewsCount(filters)
	st.session_state["rl_reviewListTotalCount"] = max(0, int(countRes.get("totalCount", 0))) if countRes.get("ok") else 0

totalC = int(st.session_state.get("rl_reviewListTotalCount", 0))
totalP = max(1, math.ceil(totalC / PAGE_SIZE))
currP = min(_getCurrentPage(), totalP)
_setCurrentPage(currP)

ckey = f"rl_review_list_{currP}_{PAGE_SIZE}_{filters}"
if srchClicked or st.session_state.get("rl_reviewListCacheKey") != ckey:
	with LoadingPopup("조회 중..."):
		res = api.getAllReviews(count=PAGE_SIZE, start=(currP-1)*PAGE_SIZE, filters=filters)
		st.session_state["rl_reviewListCacheResult"], st.session_state["rl_reviewListCacheKey"] = res, ckey
else: res = st.session_state["rl_reviewListCacheResult"]

if not res.get("ok"): st.error("오류")
else:
	rows = res.get("rows")
	if rows:
		_renderReviewTable(api, rows)
		_renderPagination(currP, totalP, totalC)
	else: st.info("데이터 없음")
