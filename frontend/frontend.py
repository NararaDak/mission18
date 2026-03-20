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

# 페이지 렌더링 메인 함수
def Do_Render_Page():
    # 기본 페이지 설정 (레이아웃 와이드 모드)
    st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")
    
    # 페이지 경로 설정
    list_moview_page = os.path.join(PAGE_DIR, "movie_list_page.py")
    list_review_page = os.path.join(PAGE_DIR, "review_list_page.py")
    pageSpecs = [
        ("영화 목록", list_moview_page),
        ("리뷰 목록", list_review_page),
    ]

    # 상단 탭 대신 라디오 버튼으로 페이지 선택 (현재 탭 상태 보존 및 중복 실행 방지)
    pageNames = [pageTitle for pageTitle, _ in pageSpecs]
    
    # 세션에 현재 선택된 탭 저장
    if "active_tab_name" not in st.session_state:
        st.session_state["active_tab_name"] = pageNames[0]
    
    # 탭 메뉴 (라디오 버튼을 수평으로 배치하여 탭처럼 보이게 함)
    # Streamlit은 st.tabs 사용 시 모든 탭의 코드를 실행하므로, 
    # 명시적 선택에 따른 분기 처리가 필요합니다.
    sel_tab = st.radio("메뉴", options=pageNames, horizontal=True, label_visibility="collapsed")
    
    # 탭이 바뀌었을 경우 기존 다이얼로그 상태 등을 초기화 (중요: crosstalk 방지)
    if st.session_state["active_tab_name"] != sel_tab:
        st.session_state["active_tab_name"] = sel_tab
        # 다이얼로그 및 행 선택 상태 초기화
        for key in ["movieDialogType", "movieDialogRow", "rl_delRid", "rl_editRid"]:
            st.session_state.pop(key, None)
        st.rerun()

    # 선택된 페이지 실행
    for pageTitle, pagePath in pageSpecs:
        if sel_tab == pageTitle:
            if pagePath is None:
                st.info("이 탭은 준비 중입니다.")
            else:
                runpy.run_path(str(pagePath), run_name=f"page_{Path(pagePath).stem}")


if __name__ == "__main__":
    Do_Render_Page()
