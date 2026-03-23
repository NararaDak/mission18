-- movie_user 테이블에 admin 계정 추가
INSERT INTO movie_user (user_id, user_name, user_pw)
VALUES ('admin', '관리자', 'admin_pw');

-- movies, reviews 테이블에 user_id 컬럼 추가
ALTER TABLE movies ADD (user_id VARCHAR2(20));
ALTER TABLE reviews ADD (user_id VARCHAR2(20));

-- 기존 movies, reviews 데이터의 user_id를 1(admin)로 채움
UPDATE movies SET user_id = 'admin';
UPDATE reviews SET user_id = 'admin';

-- (필요시) 외래키 제약조건 추가 예시
-- ALTER TABLE movies ADD CONSTRAINT fk_movies_user_id FOREIGN KEY (user_id) REFERENCES movie_user(user_id);
-- ALTER TABLE reviews ADD CONSTRAINT fk_reviews_user_id FOREIGN KEY (user_id) REFERENCES movie_user(user_id);
