
-- 영화 정보 테이블 (Oracle 스키마와 최대한 일치)
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
    plot TEXT,
    directorNm TEXT,
    directorEnNm TEXT,
    directorId TEXT,
    actorNm TEXT,
    actorEnNm TEXT,
    actorId TEXT,
    nation TEXT,
    company TEXT,
    prodYear TEXT,
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

-- 리뷰 관리 테이블 (Oracle 스키마와 최대한 일치)
CREATE TABLE IF NOT EXISTS reviews (
    reviewId INTEGER PRIMARY KEY AUTOINCREMENT,
    movieId INTEGER NOT NULL,
    authorName TEXT NOT NULL,
    content TEXT NOT NULL,
    sentimentLabel TEXT,
    sentimentScore REAL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movieId) REFERENCES movies(movieId) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reviews_movieId ON reviews(movieId);

-- 사용자 관리 테이블 (Oracle 스키마와 최대한 일치)
CREATE TABLE IF NOT EXISTS movie_user (
    user_id TEXT PRIMARY KEY CHECK (LENGTH(user_id) >= 4 AND LENGTH(user_id) <= 32),
    user_name TEXT NOT NULL,
    user_pw TEXT NOT NULL CHECK (LENGTH(user_pw) >= 6 AND LENGTH(user_pw) <= 64)
);
