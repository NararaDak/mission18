-- Mission18 데이터베이스 스키마 정의 (SQLite용)

-- 영화 정보 테이블 (KMDB 수집 데이터 기준)
CREATE TABLE IF NOT EXISTS movies (
    movieId INTEGER PRIMARY KEY AUTOINCREMENT,
    collection TEXT,
    pageNo INTEGER,
    numOfRows INTEGER,
    totalCount INTEGER,
    rowValue INTEGER,
    docid TEXT UNIQUE,
    kmdbMovieId TEXT,
    movieSeq TEXT,
    title TEXT NOT NULL,
    titleEng TEXT,
    titleOrg TEXT,
    titleEtc TEXT,
    directorNm TEXT,
    directorEnNm TEXT,
    directorId TEXT,
    actorNm TEXT,
    actorEnNm TEXT,
    actorId TEXT,
    nation TEXT,
    company TEXT,
    prodYear TEXT,
    plot TEXT,
    runtime TEXT,
    rating TEXT,
    genre TEXT,
    kmdbUrl TEXT,
    movieType TEXT,
    movieUse TEXT,
    episodes TEXT,
    ratedYn TEXT,
    repRatDate TEXT,
    repRlsDate TEXT,
    ratingMain TEXT,
    ratingDate TEXT,
    ratingNo TEXT,
    ratingGrade TEXT,
    releaseDate TEXT,
    keywords TEXT,
    posterUrl TEXT,
    stillUrl TEXT,
    staffNm TEXT,
    staffRoleGroup TEXT,
    staffRole TEXT,
    staffEtc TEXT,
    staffId TEXT,
    vodClass TEXT,
    vodUrl TEXT,
    openThtr TEXT,
    screenArea TEXT,
    screenCnt TEXT,
    salesAcc TEXT,
    audiAcc TEXT,
    statSouce TEXT,
    statDate TEXT,
    themeSong TEXT,
    soundtrack TEXT,
    fLocation TEXT,
    awards1 TEXT,
    awards2 TEXT,
    regDate TEXT,
    modDate TEXT,
    codeNm TEXT,
    codeNo TEXT,
    commCodes TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
CREATE INDEX IF NOT EXISTS idx_movies_releaseDate ON movies(releaseDate);

-- 리뷰 관리 테이블
CREATE TABLE IF NOT EXISTS reviews (
    reviewId INTEGER PRIMARY KEY AUTOINCREMENT,
    movieId INTEGER NOT NULL,  -- movies 테이블의 movieId 참조
    authorName TEXT NOT NULL,
    content TEXT NOT NULL,
    sentimentLabel TEXT,
    sentimentScore INTEGER,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movieId) REFERENCES movies(movieId) ON DELETE CASCADE
);

-- 인덱스 추가 (영화별 리뷰 조회)
CREATE INDEX IF NOT EXISTS idx_reviews_movieId ON reviews(movieId);
