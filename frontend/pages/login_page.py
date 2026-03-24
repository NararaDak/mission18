import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup

from login import show_login

if "login_error" not in st.session_state:
    st.session_state["login_error"] = ""

user_id = st.text_input("아이디", max_chars=20, help="아이디를 입력하세요.")
user_pw = st.text_input("비밀번호", type="password")

login_btn = st.button("로그인")

if login_btn:
    if not user_id:
        st.session_state["login_error"] = "아이디를 입력해 주세요."
    elif not user_pw:
        st.session_state["login_error"] = "비밀번호를 입력해 주세요."
    else:
        with LoadingPopup("로그인 중..."):
            # 실제 API 연동 필요: CallApi().login(user_id, user_pw)
            # 임시: admin01 / admin_pw
            if user_id == "admin01" and user_pw == "admin_pw":
                st.session_state["user_id"] = user_id
                st.session_state["user_name"] = "관리자"
                st.success("로그인 성공! 환영합니다, 관리자님.")
                st.session_state["login_error"] = ""
                st.experimental_rerun()
            else:
                st.session_state["login_error"] = "아이디 또는 비밀번호가 올바르지 않습니다."

if st.session_state["login_error"]:
    st.error(st.session_state["login_error"])
show_login()
