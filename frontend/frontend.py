# Streamlit 기반 프론트엔드 메인 실행 파일
from pathlib import Path
import runpy
import sys
import os

# 프로젝트 루트 및 공통 경로를 sys.path에 추가 (임포트 해결)
projectRootDir = Path(__file__).resolve().parent.parent
commonDir = os.path.join(projectRootDir, "common")

if str(projectRootDir) not in sys.path:
    sys.path.insert(0, str(projectRootDir))
if str(commonDir) not in sys.path:
    sys.path.insert(0, str(commonDir))

# Streamlit 설치 여부 확인
try:
    import streamlit as st
except ImportError as importError:
    raise SystemExit(
        "streamlit 패키지가 설치되어 있지 않습니다. "
        "가상환경을 활성화한 뒤 'pip install streamlit'을 실행해 주세요."
    ) from importError

APP_PAGE_TITLE = "Mission18 Frontend"
PAGE_DIR =  os.path.join(os.path.dirname(__file__), "pages")


# 로그인 상태가 아니면 로그인 화면으로 이동

def Do_Render_Page():
    st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")
    
    # 세션 자동 복구 (새로고침 시 로그인 유지) - 9번 요구사항 개선 방안
    if "user_id" not in st.session_state:
        qs = st.query_params
        if qs.get("uid") and qs.get("uname"):
            st.session_state["user_id"] = qs.get("uid")
            st.session_state["user_name"] = qs.get("uname")
            st.rerun()

    # 로그인 상태가 아니면 로그인 화면 또는 회원 가입 화면으로 이동
    if "user_id" not in st.session_state:
        if st.session_state.get("goto_signup"):
            from pages.add_user import show_signup
            show_signup()
        else:
            import login
            login.show_login()
        return

    # 로그인 성공 시 상단에 사용자 이름과 로그아웃 버튼 표시
    topCols = st.columns([11, 2, 1])
    with topCols[1]:
        st.markdown(f"**{st.session_state.get('user_name')}** 접속 중")
    with topCols[2]:
        if st.button("로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                st.session_state.pop(key, None)
            st.query_params.clear() # 로그아웃 시 쿼리 파라미터도 비움
            st.rerun()

    # 영화/리뷰 목록 라디오 버튼 제공
    list_moview_page = os.path.join(PAGE_DIR, "movie_list_page.py")
    list_review_page = os.path.join(PAGE_DIR, "review_list_page.py")
    pageSpecs = [
        ("영화 목록", list_moview_page),
        ("리뷰 목록", list_review_page),
    ]
    pageNames = [pageTitle for pageTitle, _ in pageSpecs]
    if "active_tab_name" not in st.session_state:
        st.session_state["active_tab_name"] = pageNames[0]
    sel_tab = st.radio("메뉴", options=pageNames, horizontal=True, label_visibility="collapsed")
    if st.session_state["active_tab_name"] != sel_tab:
        st.session_state["active_tab_name"] = sel_tab
        for key in ["movieDialogType", "movieDialogRow", "rl_delRid", "rl_editRid"]:
            st.session_state.pop(key, None)
        st.rerun()
    for pageTitle, pagePath in pageSpecs:
        if sel_tab == pageTitle:
            if pagePath is None:
                st.info("이 탭은 준비 중입니다.")
            else:
                try:
                    runpy.run_path(str(pagePath), run_name=f"page_{Path(pagePath).stem}")
                except Exception as e:
                    # Streamlit의 RerunException이나 StopException은 그대로 상위로 던져야 페이지가 재실행/중단됨
                    # 그렇지 않고 catch 해버리면 UI에 에러 메시지가 뜸
                    exc_type = type(e).__name__
                    if exc_type in ["RerunException", "StopException", "RerunData"]:
                        raise e
                    st.error(f"페이지 실행 중 오류 발생: {e}")
                    import traceback
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    Do_Render_Page()
