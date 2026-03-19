import streamlit as st

from functions import Build_Movie_Label, Build_Sentiment_Text, Draw_Page_Header, Get_Client


Draw_Page_Header()
client = Get_Client()
movieList = client.getMovies()

st.subheader("리뷰 등록")
if not movieList:
    st.info("리뷰를 등록하려면 먼저 영화를 추가하세요.")
else:
    if all(movieItem.get("id") is None for movieItem in movieList):
        st.warning("백엔드 영화 목록 응답에 movieId가 없어 리뷰 등록 대상을 식별할 수 없습니다. API.md 명세와 실제 응답을 확인하세요.")

    movieLabelList = [Build_Movie_Label(movieItem) for movieItem in movieList]
    movieByLabel = {Build_Movie_Label(movieItem): movieItem for movieItem in movieList}

    with st.form("reviewCreateForm"):
        selectedMovieLabel = st.selectbox("영화 선택", options=movieLabelList)
        docIdValue = st.text_input("문서 ID(docid)")
        reviewerValue = st.text_input("작성자")
        contentValue = st.text_area("리뷰 내용", height=140)
        submitReview = st.form_submit_button("리뷰 등록 및 감성 분석")

    if submitReview:
        selectedMovie = movieByLabel[selectedMovieLabel]
        movieId = selectedMovie.get("id")

        if movieId is None:
            st.error("선택한 영화에 movieId가 없어 리뷰를 등록할 수 없습니다.")
        elif not docIdValue.strip():
            st.error("문서 ID(docid)는 필수입니다.")
        elif not reviewerValue.strip():
            st.error("작성자 이름은 필수입니다.")
        elif not contentValue.strip():
            st.error("리뷰 내용은 필수입니다.")
        else:
            createReview = client.doCreateReview(movieId, docIdValue.strip(), reviewerValue.strip(), contentValue.strip())
            if createReview is None:
                st.error("리뷰 등록에 실패했습니다.")
            else:
                sentimentText = Build_Sentiment_Text(createReview)
                st.success("리뷰가 등록되었습니다.")
                st.write(f"감성 분석 결과: {sentimentText}")
