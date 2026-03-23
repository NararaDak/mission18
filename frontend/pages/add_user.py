import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup

def show_signup():
    api = CallApi()
    st.markdown("""
        <style>
        .signup-card {
            max-width: 400px;
            margin: 40px auto 0 auto;
            padding: 2rem 2rem 1.5rem 2rem;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px 0 rgba(0,0,0,0.1);
        }
        .signup-title {text-align:center; font-size:2rem; font-weight:700; margin-bottom:1.5rem; color: #333;}
        </style>
    """, unsafe_allow_html=True)

    # 7번 요구사항: 회원가입 화면 크기 조정 및 중앙 배치
    _, centerCol, _ = st.columns([1, 1, 1])
    with centerCol:
        st.markdown('<div class="signup-card">', unsafe_allow_html=True)
        st.markdown('<div class="signup-title">회원 가입</div>', unsafe_allow_html=True)

    if "signup_error" not in st.session_state:
        st.session_state["signup_error"] = ""

    with st.form("signup_form", clear_on_submit=False):
        user_id = st.text_input("아이디", max_chars=32, help="4~32자")
        user_nm = st.text_input("이름 (닉네임)", max_chars=100)
        user_pw = st.text_input("비밀번호", type="password", max_chars=64, help="6~64자")
        user_pw_confirm = st.text_input("비밀번호 확인", type="password", max_chars=64)
        
        btnCols = st.columns([1, 1])
        signup_btn = btnCols[0].form_submit_button("가입하기", use_container_width=True)
        back_btn = btnCols[1].form_submit_button("취소 (로그인으로)", use_container_width=True)

        if signup_btn:
            if not (4 <= len(user_id) <= 32):
                st.session_state["signup_error"] = "아이디는 4~32자여야 합니다."
            elif not user_nm:
                st.session_state["signup_error"] = "이름을 입력하세요."
            elif not (6 <= len(user_pw) <= 64):
                st.session_state["signup_error"] = "비밀번호는 6~64자여야 합니다."
            elif user_pw != user_pw_confirm:
                st.session_state["signup_error"] = "비밀번호가 일치하지 않습니다."
            else:
                with LoadingPopup("가입 처리 중..."):
                    res = api.createUser(user_id, user_nm, user_pw)
                    if res.get("ok"):
                        st.success("회원 가입 성공! 로그인해 주세요.")
                        st.session_state["signup_error"] = ""
                        st.session_state["goto_signup"] = False
                        st.rerun()
                    else:
                        st.session_state["signup_error"] = res.get("error", "회원 가입에 실패했습니다.")
        
        if back_btn:
            st.session_state["goto_signup"] = False
            st.rerun()

    if st.session_state["signup_error"]:
        st.error(st.session_state["signup_error"])
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_signup()
