-- movie_user 테이블에 admin 계정 추가
INSERT OR IGNORE INTO movie_user (user_id, user_name, user_pw)
VALUES ('admin', '관리자', 'admin_pw');

-- movies, reviews 테이블에 user_id 컬럼 추가 (이미 있으면 무시)
ALTER TABLE movies ADD COLUMN user_id TEXT;
ALTER TABLE reviews ADD COLUMN user_id TEXT;

-- 기존 movies, reviews 데이터의 user_id를 'admin'으로 채움
UPDATE movies SET user_id = 'admin';
UPDATE reviews SET user_id = 'admin';

-- (필요시) 외래키 제약조건 추가 예시 (SQLite는 테이블 생성 시에만 가능, ALTER 불가)
-- 외래키를 추가하려면 테이블을 새로 만들어야 하므로, 아래는 참고용입니다.
-- CREATE TABLE new_movies (..., user_id TEXT, FOREIGN KEY(user_id) REFERENCES movie_user(user_id));
-- CREATE TABLE new_reviews (..., user_id TEXT, FOREIGN KEY(user_id) REFERENCES movie_user(user_id));
