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
    
    # 탭 메뉴 구성을 위한 페이지 경로 설정
    list_moview_page = os.path.join(PAGE_DIR, "movie_list_page.py")
    list_review_page = os.path.join(PAGE_DIR, "review_list_page.py")
    pageSpecs = [
        ("영화 목록", list_moview_page),
        ("리뷰 목록", list_review_page),
    ]

    # 상단 탭 생성
    tabList = st.tabs([pageTitle for pageTitle, _ in pageSpecs])

    # 각 탭 클릭 시 해당 페이지 스크립트 실행
    for tabItem, (_, pagePath) in zip(tabList, pageSpecs):
        with tabItem:
            if pagePath is None:
                st.info("이 탭은 준비 중입니다.")
            else:
                # 지정된 경로의 Python 파일을 현재 컨텍스트에서 실행
                runpy.run_path(str(pagePath), run_name=f"page_{Path(pagePath).stem}")

if __name__ == "__main__":
    Do_Render_Page()
