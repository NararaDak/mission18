# 영화 목록 조회 및 상세 정보, 리뷰 관리를 담당하는 페이지 스크립트
import math
import configparser
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup

# 페이지네이션 설정
PAGE_SIZE = 10
PAGE_GROUP_SIZE = 5

# INI 설정에서 영문 컬럼명 대조 한국어 맵 정보 로드 (캐시 적용)
@st.cache_data(show_spinner=False)
def _getColumnTitleMap() -> dict[str, str]:
	projectRootDir = Path(__file__).resolve().parent.parent.parent
	iniPath = projectRootDir / "common" / "m18.ini"
	config = configparser.ConfigParser()
	config.optionxform = str
	config.read(iniPath, encoding="utf-8")
	return {k: v for k, v in config.items("eng_kor")} if config.has_section("eng_kor") else {}

# 세션 상태에서 현재 영화 목록 페이지 번호 조회
def _getCurrentPage() -> int:
	if "movieListPage" not in st.session_state: st.session_state["movieListPage"] = 1
	return int(st.session_state["movieListPage"])

# 세션 상태에 현재 영화 목록 페이지 번호 저장
def _setCurrentPage(page: int) -> None:
	st.session_state["movieListPage"] = max(1, int(page))

# 화면 하단 등에 표시할 알림 메시지 설정
def _setActionMessage(msg: str) -> None:
	st.session_state["ml_movieListActionMessage"] = msg

# 날짜에 특정 개월 수를 더하거나 뺌
def _addMonths(base: date, diff: int) -> date:
	totalMonth = (base.month - 1) + diff
	yy, mm = base.year + (totalMonth // 12), (totalMonth % 12) + 1
	return date(yy, mm, min(base.day, monthrange(yy, mm)[1]))

# 검색 필터 기본값 설정 (세션 상태 초기화)
def _ensureSearchDefaults() -> None:
	today = date.today()
	if "movieSearchTitle" not in st.session_state: st.session_state["movieSearchTitle"] = ""
	if "movieSearchDirector" not in st.session_state: st.session_state["movieSearchDirector"] = ""
	if "movieSearchActor" not in st.session_state: st.session_state["movieSearchActor"] = ""
	if "movieSearchUseReleaseRange" not in st.session_state: st.session_state["movieSearchUseReleaseRange"] = False
	if "movieSearchStartDate" not in st.session_state: st.session_state["movieSearchStartDate"] = _addMonths(today, -3)
	if "movieSearchEndDate" not in st.session_state: st.session_state["movieSearchEndDate"] = _addMonths(today, 3)

# 현재 세션 상태를 기반으로 API 요청용 검색 필터 딕셔너리 생성
def _getSearchFilters() -> dict[str, str]:
	useRange = bool(st.session_state.get("movieSearchUseReleaseRange", True))
	start, end = st.session_state.get("movieSearchStartDate"), st.session_state.get("movieSearchEndDate")
	return {
		"title": str(st.session_state.get("movieSearchTitle", "")).strip(),
		"director": str(st.session_state.get("movieSearchDirector", "")).strip(),
		"actor": str(st.session_state.get("movieSearchActor", "")).strip(),
		"releaseStart": start.isoformat() if useRange and isinstance(start, date) else "",
		"releaseEnd": end.isoformat() if useRange and isinstance(end, date) else "",
	}

# 다이얼로그(팝업) 오픈 상태 설정
def _openDialog(dtype: str, row: dict[str, object] | None = None) -> None:
	st.session_state["movieDialogType"] = dtype
	st.session_state["movieDialogRow"] = dict(row) if row else None

# 다이얼로그 닫기
def _closeDialog() -> None:
	st.session_state.pop("movieDialogType", None)
	st.session_state.pop("movieDialogRow", None)

# 현재 선택된 영화 행 정보 저장
def _setSelectedMovie(row: dict[str, object]) -> None:
	st.session_state["selectedMovieRow"] = dict(row)

# 현재 선택된 영화 행 정보 조회
def _getSelectedMovie() -> dict[str, object] | None:
	row = st.session_state.get("selectedMovieRow")
	return row if isinstance(row, dict) else None

# 전체 영화 건수 다시 조회하여 세션 갱신
def _refreshTotalCount(api: CallApi) -> None:
	res = api.getMoviesCount(_getSearchFilters())
	if res.get("ok"): st.session_state["ml_movieListTotalCount"] = max(0, int(res.get("totalCount", 0)))
	st.session_state.pop("ml_movieListCacheKey", None)

# 서버에서 받아온 목록과 현재 선택된 영화 동기화 (없으면 첫 번째 선택)
def _syncSelectedMovie(rows: list[dict[str, object]]) -> None:
	if not rows:
		st.session_state.pop("selectedMovieRow", None)
		return
	sel = _getSelectedMovie()
	selId = int(sel.get("movieId", 0)) if sel else 0
	for row in rows:
		if int(row.get("movieId", 0)) == selId:
			_setSelectedMovie(row)
			return
	_setSelectedMovie(rows[0])

# 다양한 형식의 날짜 데이터를 date 객체로 파싱
def _parseReleaseDate(val: object) -> date:
	nums = "".join(c for c in str(val or "").strip() if c.isdigit())
	if len(nums) >= 8:
		try: return datetime.strptime(nums[:8], "%Y%m%d").date()
		except: pass
	return date.today()

# 날짜 데이터를 'YYYY-MM-DD' 문자열로 포맷팅
def _formatReleaseDate(val: object) -> str:
	nums = "".join(c for c in str(val or "").strip() if c.isdigit())
	return f"{nums[:4]}-{nums[4:6]}-{nums[6:8]}" if len(nums) >= 8 else str(val or "")

# 신규 영화 추가 다이얼로그 (Streamlit Dialog)
@st.dialog("영화 추가", width="large")
def _showCreateMovieDialog(api: CallApi) -> None:
	with st.form("movieAddDialogForm"):
		title = st.text_input("제목")
		rlsDate = st.date_input("개봉일", value=date.today(), format="YYYY-MM-DD")
		director, actor, genre, poster = st.text_input("감독"), st.text_input("배우"), st.text_input("장르"), st.text_input("포스터 URL")
		if st.form_submit_button("영화 추가 저장", use_container_width=True):
			with LoadingPopup("영화 추가 중..."):
				res = api.createMovie(title.strip(), rlsDate.isoformat(), director=director.strip(), actor=actor.strip(), genre=genre.strip(), posterUrl=poster.strip())
			if res.get("ok"):
				_refreshTotalCount(api)
				_setActionMessage(f"추가 완료: {title.strip()}")
				_closeDialog()
				st.rerun()
			else: st.error(res.get("error", "추가 실패"))

# 영화 정보 수정 다이얼로그
@st.dialog("영화 수정", width="large")
def _showEditMovieDialog(api: CallApi, row: dict[str, object]) -> None:
	mid = int(row.get("movieId", 0))
	with st.form(f"movieEditDialogForm_{mid}"):
		title = st.text_input("제목", value=str(row.get("title", "")))
		rlsDate = st.date_input("개봉일", value=_parseReleaseDate(row.get("repRlsDate")), format="YYYY-MM-DD")
		director, actor, genre, poster = st.text_input("감독", value=str(row.get("directorNm", ""))), st.text_input("배우", value=str(row.get("actorNm", ""))), st.text_input("장르", value=str(row.get("genre", ""))), st.text_input("포스터 URL", value=str(row.get("posterUrl", "")))
		if st.form_submit_button("영화 수정 저장", use_container_width=True):
			with LoadingPopup("영화 수정 중..."):
				res = api.updateMovie(mid, title.strip(), rlsDate.isoformat(), director.strip(), actor.strip(), genre.strip(), poster.strip())
			if res.get("ok"):
				st.session_state.pop("movieListCacheKey", None)
				_closeDialog()
				st.rerun()
			else: st.error(res.get("error", "수정 실패"))

# 리뷰 등록 다이얼로그
@st.dialog("리뷰 등록", width="large")
def _showCreateReviewDialog(api: CallApi, row: dict[str, object]) -> None:
	mid, title = int(row.get("movieId", 0)), str(row.get("title", ""))
	st.caption(f"대상 영화: {title}")
	with st.form(f"reviewCreateDialogForm_{mid}"):
		author = st.text_input("작성자")
		content = st.text_area("리뷰 내용", height=160)
		if st.form_submit_button("리뷰 등록", use_container_width=True):
			with LoadingPopup("리뷰 등록 중..."):
				res = api.createReview(mid, author.strip(), content.strip())
			if res.get("ok"):
				st.session_state.pop("movieReviewListCacheKey", None)
				_setSelectedMovie(row)
				_setActionMessage(f"리뷰 등록 완료: {title}")
				_closeDialog()
				st.rerun()
			else: st.error(res.get("error", "등록 실패"))

# 영화 목록 테이블 렌더링
def _renderMovieTable(api: CallApi, rows: list[dict[str, object]], cols: list[str], titleMap: dict[str, str]) -> None:
	header = st.columns([3, 2, 3, 2, 1])
	for h, c in zip(header[:-1], cols): h.markdown(f"**{titleMap.get(c, c)}**")
	header[-1].markdown("**관리**")
	sel = _getSelectedMovie()
	selId = int(sel.get("movieId", 0)) if sel else 0

	for i, row in enumerate(rows):
		line = st.columns([3, 2, 3, 2, 1])
		rid = int(row.get("movieId", 0))
		for j, (cell, c) in enumerate(zip(line[:-1], cols)):
			val = row.get(c, "")
			if j == 0: # 제목 버튼 (클릭 시 선택)
				lbl = ("▶ " if rid == selId else "") + str(val or "선택")
				if cell.button(lbl, key=f"movieSelect_{i}", use_container_width=True):
					_setSelectedMovie(row)
					st.rerun()
			else: cell.write(_formatReleaseDate(val) if c in ("repRlsDate", "releaseDate") else str(val or ""))

		with line[-1]:
			with st.popover("⋮", use_container_width=True):
				if st.button("수정", key=f"movieEdit_{i}", use_container_width=True):
					_setSelectedMovie(row)
					_openDialog("edit", row)
					st.rerun()
				if st.button("삭제", key=f"movieDelete_{rid}", use_container_width=True):
					st.session_state["delMid"], st.session_state["delTitle"] = rid, str(row.get("title", ""))
					st.rerun()
				
				# 삭제 확인 로직
				if st.session_state.get("delMid") == rid:
					st.warning("삭제?")
					c1, c2 = st.columns(2)
					if c1.button("확인", key=f"delOk_{rid}"):
						with LoadingPopup("삭제 중..."): res = api.deleteMovie(rid)
						if res.get("ok"):
							_refreshTotalCount(api)
							st.session_state.pop("selectedMovieRow", None)
							st.session_state.pop("delMid", None)
							_setActionMessage("삭제 완료")
							st.rerun()
						else: st.error("삭제 실패")
					if c2.button("취소", key=f"delNo_{rid}"):
						st.session_state.pop("delMid", None)
						st.rerun()
		st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

# 우측 상세 정보 및 리뷰 패널 렌더링
def _renderReviewPanel(api: CallApi) -> None:
	row = _getSelectedMovie()
	if not row:
		st.subheader("영화별 리뷰 목록")
		st.info("영화를 선택하세요.")
		return

	mid, title = int(row.get("movieId", 0)), str(row.get("title", ""))
	t1, t2 = st.tabs(["🎥 상세 정보", "📋 리뷰 목록"])

	with t1: # 영화 상세 정보 탭
		st.subheader(title)
		cImg, cTxt = st.columns([1, 1.5])
		pst = str(row.get("posterUrl", ""))
		with cImg:
			if pst.startswith("http"): st.image(pst, use_container_width=True)
			else: st.info("이미지 없음")
		with cTxt:
			st.markdown(f"**🎬 감독:** {row.get('directorNm', '-')}")
			st.markdown(f"**👥 배우:** {row.get('actorNm', '-')}")
			st.markdown(f"**🏷️ 장르:** {row.get('genre', '-')}")
			st.markdown(f"**📅 개봉일:** {_formatReleaseDate(row.get('repRlsDate') or row.get('releaseDate', ''))}")
			st.markdown("**📝 줄거리:**")
			st.write(row.get("plot", "내용 없음"))

	with t2: # 리뷰 목록 탭
		ch, cb = st.columns([3, 1])
		ch.subheader(f"{title} 리뷰")
		if cb.button("➕ 리뷰 등록", key=f"revAdd_{mid}", use_container_width=True):
			_openDialog("review", row)
			st.rerun()

		# 리뷰 목록 캐시 처리
		ckey = f"rev_list_{mid}"
		if st.session_state.get("movieReviewListCacheKey") != ckey:
			with LoadingPopup("조회 중..."):
				res = api.getReviews(mid)
				st.session_state["movieReviewListCacheResult"], st.session_state["movieReviewListCacheKey"] = res, ckey
		else: res = st.session_state["movieReviewListCacheResult"]

		if not res.get("ok"):
			st.error("실패")
			return
		
		revs = res.get("rows")
		if not revs:
			st.info("리뷰 없음")
			return
		for i, r in enumerate(revs):
			rvid = int(r.get("reviewId", 0))
			with st.container(border=True):
				st.markdown(f"**{r.get('authorName', '')}**")
				st.caption(f"{r.get('sentimentLabel', '')} / {r.get('sentimentScore', '')} / {r.get('createdAt', '')}")
				st.write(r.get("content", ""))
				c1, c2, _ = st.columns([1, 1, 8])
				if c1.button("수정", key=f"ml_revEdit_{rvid}_{i}"):
					st.session_state["ml_editRid"], st.session_state["ml_editTxt"], st.session_state["ml_editAuth"] = rvid, str(r.get("content", "")), str(r.get("authorName", ""))
				if c2.button("삭제", key=f"ml_revDel_{rvid}_{i}"): st.session_state["ml_revDelRid"] = rvid
				
				# 리뷰 수정 폼
				if st.session_state.get("ml_editRid") == rvid:
					with st.form(f"ml_revEditForm_{rvid}_{i}"):
						txt = st.text_area("내용", value=st.session_state.get("ml_editTxt", ""), height=120)
						auth = st.text_input("작성자", value=st.session_state.get("ml_editAuth", ""))
						if st.form_submit_button("수정 완료"):
							with LoadingPopup("수정 중..."): editRes = api.editReview(rvid, auth, txt)
							if editRes.get("ok"):
								st.session_state.pop("movieReviewListCacheKey", None)
								st.session_state.pop("ml_editRid", None)
								st.rerun()
							else: st.error("실패")
						if st.form_submit_button("취소"):
							st.session_state.pop("ml_editRid", None)
							st.rerun()

				# 리뷰 삭제 확인
				if st.session_state.get("ml_revDelRid") == rvid:
					st.warning("삭제?")
					dc1, dc2 = st.columns(2)
					if dc1.button("삭제 확정", key=f"ml_revDelOk_{rvid}_{i}"):
						with LoadingPopup("삭제 중..."): delRes = api.deleteReview(rvid)
						if delRes.get("ok"):
							st.session_state.pop("movieReviewListCacheKey", None)
							st.session_state.pop("ml_revDelRid", None)
							st.rerun()
						else: st.error("실패")
					if dc2.button("취소", key=f"ml_revDelNo_{rvid}_{i}"):
						st.session_state.pop("ml_revDelRid", None)
						st.rerun()

# 페이지네이션 컨트롤 렌더링
def _renderPagination(curr: int, totalP: int, totalC: int) -> None:
	gStart = ((curr - 1) // PAGE_GROUP_SIZE) * PAGE_GROUP_SIZE + 1
	gEnd = min(totalP, gStart + PAGE_GROUP_SIZE - 1)
	pgs = list(range(gStart, gEnd + 1))
	ctrls = st.columns(2 + len(pgs) + 2)
	if ctrls[0].button("<<", key="movPage_first", disabled=curr <= 1): _setCurrentPage(1); st.rerun()
	if ctrls[1].button("<", key="movPage_prev", disabled=gStart <= 1): _setCurrentPage(gStart - 1); st.rerun()
	for i, p in enumerate(pgs):
		lbl = f"**[{p}]**" if p == curr else str(p)
		if ctrls[2+i].button(lbl, key=f"movPage_{p}"): _setCurrentPage(p); st.rerun()
	if ctrls[2+len(pgs)].button(">", key="movPage_next", disabled=gEnd >= totalP): _setCurrentPage(gEnd + 1); st.rerun()
	if ctrls[3+len(pgs)].button(">>", key="movPage_last", disabled=curr >= totalP): _setCurrentPage(totalP); st.rerun()
	st.caption(f"페이지: {curr}/{totalP} (총 {totalC}건)")

# --- 메인 렌더링 시작 ---
st.subheader("영화 목록(ver1.0)")
_ensureSearchDefaults()

# 검색 폼 설계
with st.form("movieSearchForm"):
	tCols = st.columns([2, 2, 2, 6])
	tCols[0].markdown("**영화제목**"); tCols[1].markdown("**감독**"); tCols[2].markdown("**배우**")
	with tCols[3]: st.checkbox("개봉일", key="movieSearchUseReleaseRange")

	iCols = st.columns([2, 2, 2, 6])
	iCols[0].text_input("제목", key="movieSearchTitle", label_visibility="collapsed")
	iCols[1].text_input("감독", key="movieSearchDirector", label_visibility="collapsed")
	iCols[2].text_input("배우", key="movieSearchActor", label_visibility="collapsed")
	with iCols[3]:
		dCols = st.columns([2.4, 0.3, 2.4])
		dCols[0].date_input("시작", key="movieSearchStartDate", format="YYYY-MM-DD", min_value=date(1900,1,1), max_value=date(2100,12,31), label_visibility="collapsed", disabled=not st.session_state.get("movieSearchUseReleaseRange"))
		dCols[1].markdown("<div style='text-align:center;padding-top:0.45rem;'>~</div>", unsafe_allow_html=True)
		dCols[2].date_input("종료", key="movieSearchEndDate", format="YYYY-MM-DD", min_value=date(1900,1,1), max_value=date(2100,12,31), label_visibility="collapsed", disabled=not st.session_state.get("movieSearchUseReleaseRange"))

	btnCols = st.columns([1, 1, 8])
	srchClicked, addClicked = btnCols[0].form_submit_button("조회", use_container_width=True), btnCols[1].form_submit_button("영화 추가", use_container_width=True)

if addClicked: _openDialog("create"); st.rerun()

# 알림 메시지 노출
msg = st.session_state.get("ml_movieListActionMessage", "")
if msg: st.info(msg); st.session_state["ml_movieListActionMessage"] = ""

api = CallApi()
filters = _getSearchFilters()

# 다이얼로그 노출 처리
dtype, drow = st.session_state.get("movieDialogType"), st.session_state.get("movieDialogRow")
if dtype == "create": _showCreateMovieDialog(api)
elif dtype == "edit" and drow: _showEditMovieDialog(api, drow)
elif dtype == "review" and drow: _showCreateReviewDialog(api, drow)

# 조회 시작 시 페이지 초기화 및 건수 갱신
if srchClicked or "ml_movieListTotalCount" not in st.session_state:
	if srchClicked: _setCurrentPage(1)
	with LoadingPopup("전체 건수 확인 중..."):
		countRes = api.getMoviesCount(filters)
	st.session_state["ml_movieListTotalCount"] = max(0, int(countRes.get("totalCount", 0))) if countRes.get("ok") else 0

# 페이지네이션 정보 계산
totalC = int(st.session_state.get("ml_movieListTotalCount", 0))
totalP = max(1, math.ceil(totalC / PAGE_SIZE))
currP = min(_getCurrentPage(), totalP)
_setCurrentPage(currP)

# 목록 데이터 캐시 로드
ckey = f"movie_list_{currP}_{PAGE_SIZE}_{filters}"
if srchClicked or st.session_state.get("movieListCacheKey") != ckey:
	with LoadingPopup("조회 중..."):
		res = api.getMovies(count=PAGE_SIZE, start=(currP-1)*PAGE_SIZE, filters=filters)
		st.session_state["movieListCacheResult"], st.session_state["movieListCacheKey"] = res, ckey
else: res = st.session_state["movieListCacheResult"]

if not res.get("ok"): st.error(res.get("error", "오류 발생"))
else:
	rows = res.get("rows")
	if rows:
		_syncSelectedMovie(rows)
		titleMap = _getColumnTitleMap()
		dispCols = ["title", "directorNm", "actorNm", "repRlsDate"]
		left, right = st.columns(2)
		with left:
			_renderMovieTable(api, rows, dispCols, titleMap)
			_renderPagination(currP, totalP, totalC)
		with right: _renderReviewPanel(api)
	else: st.info("데이터 없음")

