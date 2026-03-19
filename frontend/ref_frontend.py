import json

import requests
import streamlit as st


st.set_page_config(page_title="AccessData GetMovies", page_icon="🎬", layout="centered")
st.title("AccessData /getmovies 테스트")


def normalize_datalist(raw: object) -> list[object] | None:
	if isinstance(raw, list):
		return raw

	if isinstance(raw, dict):
		keys = list(raw.keys())
		if all(str(k).isdigit() for k in keys):
			sorted_items = sorted(raw.items(), key=lambda kv: int(str(kv[0])))
			return [v for _, v in sorted_items]
		return list(raw.values())

	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return normalize_datalist(parsed)
		except ValueError:
			return None

	return None

default_url = "http://127.0.0.1:8033/accessdata/getmovies"
api_url = st.text_input("API URL", value=default_url)
count_value = st.number_input("COUNT", min_value=1, max_value=1000, value=10, step=1)

request_body = {"COUNT": str(count_value)}
st.caption("전송될 요청 바디")
st.code(json.dumps(request_body, ensure_ascii=False, indent=2), language="json")

if st.button("요청 보내기", type="primary"):
	try:
		response = requests.post(api_url, json=request_body, timeout=30)
		st.write(f"HTTP 상태 코드: {response.status_code}")

		try:
			response_json = response.json()
			st.success("응답 JSON")
			st.json(response_json)

			datalist = response_json.get("datalist") if isinstance(response_json, dict) else None
			rows = normalize_datalist(datalist)
			if rows is not None:
				st.subheader("datalist 그리드")
				if len(rows) > 0:
					if isinstance(rows[0], dict):
						display_columns = ["title", "directorNm", "actorNm", "repRlsDate"]
						display_rows = [{col: row.get(col, "") for col in display_columns} for row in rows]
						st.dataframe(display_rows, use_container_width=True)
					else:
						st.dataframe([{"value": x} for x in rows], use_container_width=True)
				else:
					st.info("datalist가 비어 있습니다.")
			elif datalist is not None:
				st.warning(f"datalist 타입({type(datalist).__name__})을 표로 변환하지 못했습니다.")
			elif isinstance(response_json, dict):
				st.info("응답 JSON에 datalist 항목이 없습니다.")

			st.caption("응답 원문")
			st.code(json.dumps(response_json, ensure_ascii=False, indent=2), language="json")
		except ValueError:
			st.warning("JSON 응답이 아닙니다. 원문을 표시합니다.")
			st.text(response.text)

	except requests.RequestException as ex:
		st.error(f"요청 실패: {ex}")
