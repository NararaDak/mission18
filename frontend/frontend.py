from pathlib import Path
import runpy
import sys
import os

projectRootDir = Path(__file__).resolve().parent.parent
commonDir = os.path.join(projectRootDir, "common")

if str(projectRootDir) not in sys.path:
    sys.path.insert(0, str(projectRootDir))
if str(commonDir) not in sys.path:
    sys.path.insert(0, str(commonDir))

try:
    import streamlit as st
except ImportError as importError:
    raise SystemExit(
        "streamlit 패키지가 설치되어 있지 않습니다. "
        "가상환경을 활성화한 뒤 'pip install streamlit'을 실행해 주세요."
    ) from importError

APP_PAGE_TITLE = "Mission18 Frontend"

PAGE_DIR =  os.path.join(os.path.dirname(__file__), "pages")

def Do_Render_Page():
    st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")
    list_moview_page = os.path.join(PAGE_DIR, "movie_list_page.py")
    list_review_page = os.path.join(PAGE_DIR, "review_list_page.py")
    pageSpecs = [
        ("영화 목록", list_moview_page),
        ("리뷰 목록", list_review_page),
    ]

    tabList = st.tabs([pageTitle for pageTitle, _ in pageSpecs])

    for tabItem, (_, pagePath) in zip(tabList, pageSpecs):
        with tabItem:
            if pagePath is None:
                st.info("이 탭은 준비 중입니다. 현재는 영화 목록 탭을 사용할 수 있습니다.")
            else:
                runpy.run_path(str(pagePath), run_name=f"page_{Path(pagePath).stem}")


if __name__ == "__main__":
    Do_Render_Page()
