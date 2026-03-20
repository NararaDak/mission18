-- Mission18 데이터베이스 스키마 정의 (Oracle용)
-- 기존 트리거/시퀀스 삭제
DROP TRIGGER trg_movies_id;
DROP SEQUENCE seq_movies_id;
DROP TABLE reviews CASCADE CONSTRAINTS;
DROP TABLE movies CASCADE CONSTRAINTS;

CREATE TABLE movies (
    movieId NUMBER PRIMARY KEY,
    collection VARCHAR2(1000),
    pageNo NUMBER,
    numOfRows NUMBER,
    totalCount NUMBER,
    rowValue NUMBER,
    docid VARCHAR2(1000) UNIQUE,
    kmdbMovieId VARCHAR2(1000),
    movieSeq VARCHAR2(1000),
    title VARCHAR2(2000) NOT NULL,
    titleEng VARCHAR2(2000),
    titleOrg VARCHAR2(2000),
    titleEtc VARCHAR2(4000),
    plot CLOB,
    directorNm VARCHAR2(4000),
    directorEnNm VARCHAR2(4000),
    directorId VARCHAR2(1000),
    actorNm VARCHAR2(4000),
    actorEnNm VARCHAR2(4000),
    actorId VARCHAR2(4000),
    nation VARCHAR2(1000),
    company VARCHAR2(2000),
    prodYear VARCHAR2(100),
    runtime VARCHAR2(1000),
    rating VARCHAR2(1000),
    genre VARCHAR2(2000),
    kmdbUrl VARCHAR2(1000),
    movieType VARCHAR2(1000),
    movieUse VARCHAR2(1000),
    episodes VARCHAR2(4000),
    ratedYn VARCHAR2(100),
    repRatDate VARCHAR2(1000),
    repRlsDate VARCHAR2(1000),
    ratingMain VARCHAR2(1000),
    ratingDate VARCHAR2(1000),
    ratingNo VARCHAR2(1000),
    ratingGrade VARCHAR2(1000),
    releaseDate VARCHAR2(1000),
    keywords VARCHAR2(4000),
    posterUrl VARCHAR2(2000),
    stillUrl VARCHAR2(2000),
    staffNm VARCHAR2(4000),
    staffRoleGroup VARCHAR2(4000),
    staffRole VARCHAR2(4000),
    staffEtc VARCHAR2(4000),
    staffId VARCHAR2(4000),
    vodClass VARCHAR2(1000),
    vodUrl VARCHAR2(2000),
    openThtr VARCHAR2(4000),
    screenArea VARCHAR2(4000),
    screenCnt VARCHAR2(1000),
    salesAcc VARCHAR2(1000),
    audiAcc VARCHAR2(1000),
    statSouce VARCHAR2(4000),
    statDate VARCHAR2(1000),
    themeSong VARCHAR2(4000),
    soundtrack VARCHAR2(4000),
    fLocation VARCHAR2(4000),
    awards1 VARCHAR2(4000),
    awards2 VARCHAR2(4000),
    regDate VARCHAR2(1000),
    modDate VARCHAR2(1000),
    codeNm VARCHAR2(1000),
    codeNo VARCHAR2(1000),
    commCodes VARCHAR2(4000),
    createdAt DATE DEFAULT SYSDATE
);

-- SEQUENCE 및 TRIGGER로 movieId 자동 증가
CREATE SEQUENCE seq_movies_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE OR REPLACE TRIGGER trg_movies_id
BEFORE INSERT ON movies
FOR EACH ROW
BEGIN
    IF :NEW.movieId IS NULL THEN
        SELECT seq_movies_id.NEXTVAL INTO :NEW.movieId FROM dual;
    END IF;
END;
/
-- 인덱스 추가
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_releaseDate ON movies(releaseDate);
-- 리뷰 관리 테이블
CREATE TABLE reviews (
    reviewId NUMBER PRIMARY KEY,
    movieId NUMBER NOT NULL,
    authorName VARCHAR2(100) NOT NULL,
    content VARCHAR2(2000) NOT NULL,
    sentimentLabel VARCHAR2(20),
    sentimentScore NUMBER,
    createdAt DATE DEFAULT SYSDATE,
    CONSTRAINT fk_reviews_movieId FOREIGN KEY (movieId) REFERENCES movies(movieId) ON DELETE CASCADE
);
-- SEQUENCE 및 TRIGGER로 reviewId 자동 증가
CREATE SEQUENCE seq_reviews_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE OR REPLACE TRIGGER trg_reviews_id
BEFORE INSERT ON reviews
FOR EACH ROW
BEGIN
    IF :NEW.reviewId IS NULL THEN
        SELECT seq_reviews_id.NEXTVAL INTO :NEW.reviewId FROM dual;
    END IF;
END;
/
-- 컬럼 타입 변경 (기존 테이블에 적용 시)
ALTER TABLE movies MODIFY (plot CLOB);
ALTER TABLE movies MODIFY (titleEtc VARCHAR2(4000));
/

-- 인덱스 추가
CREATE INDEX idx_reviews_movieId ON reviews(movieId);
