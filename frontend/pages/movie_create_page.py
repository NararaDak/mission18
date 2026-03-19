from datetime import datetime

import streamlit as st

from call_api import CallApi


callApi = CallApi()

st.subheader("영화 추가")
with st.form("movieCreateForm"):
    titleValue = st.text_input("제목")
    releaseDateValue = st.date_input("개봉일", value=datetime.today())
    directorValue = st.text_input("감독")
    genreValue = st.text_input("장르")
    posterUrlValue = st.text_input("포스터 URL")
    submitMovie = st.form_submit_button("영화 등록")

if submitMovie:
    if not titleValue.strip():
        st.error("제목은 필수입니다.")
    else:
        createResult = callApi.createMovie(
            titleValue=titleValue.strip(),
            releaseDateValue=releaseDateValue.isoformat(),
            directorValue=directorValue.strip(),
            genreValue=genreValue.strip(),
            posterUrlValue=posterUrlValue.strip(),
        )
        if not createResult.get("ok"):
            st.error(createResult.get("error", "영화 등록에 실패했습니다. 백엔드 API를 확인하세요."))
            if createResult.get("responseJson") is not None:
                st.json(createResult["responseJson"])
        else:
            st.success("영화가 등록되었습니다.")
            if createResult.get("data") is not None:
                st.json(createResult["data"])
