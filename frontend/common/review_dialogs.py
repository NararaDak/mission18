import streamlit as st
from loading_popup import LoadingPopup

@st.dialog("리뷰 수정", width="large")
def show_edit_review_dialog(api, review_id, content, author, movie_title, on_success=None, on_cancel=None):
    st.caption(f"대상 영화: {movie_title}")
    with st.form("reviewEditForm_common"):
        userName = st.session_state.get("user_name", "")
        st.write(f"**작성자:** {userName}")
        newTxt = st.text_area("내용", value=content, height=120)
        c1, c2 = st.columns(2)
        if c1.form_submit_button("수정 완료", use_container_width=True):
            userId = st.session_state.get("user_id", "")
            with LoadingPopup("수정 중..."):
                res = api.editReview(review_id, userName, newTxt, userId=userId)
            if res.get("ok"):
                if on_success: on_success()
            else:
                st.error(res.get("error", "수정 실패"))
        if c2.form_submit_button("취소", use_container_width=True):
            if on_cancel: on_cancel()

@st.dialog("리뷰 삭제", width="small")
def show_delete_review_dialog(api, review_id, movie_title=None, on_success=None, on_cancel=None):
    st.warning(f"이 리뷰를 정말 삭제하시겠습니까?" + (f"\n\n(대상 영화: {movie_title})" if movie_title else ""))
    c1, c2 = st.columns(2)
    userId = st.session_state.get("user_id", "")
    if c1.button("삭제 확정", key=f"delOk_common_{review_id}", use_container_width=True):
        with LoadingPopup("삭제 중..."):
            res = api.deleteReview(review_id, userId=userId)
        if res.get("ok"):
            if on_success: on_success()
        else:
            st.error(res.get("error", "삭제 실패"))
    if c2.button("취소", key=f"delNo_common_{review_id}", use_container_width=True):
        if on_cancel: on_cancel()
