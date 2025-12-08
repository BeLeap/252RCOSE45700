# ingest / server / client 구현 작업 정리

`docs/REQUIREMENT.md`와 `docs/TODO.md`를 충족하기 위해 필요한 ingest, server, client 작업을 구체적으로 나눠 적었습니다. 각 항목은 체크박스 그대로 작업 진행 여부를 표시하면서 사용하면 됩니다.

## ingest: FAISS 인덱스 생성

- [ ] 데이터 소스 로딩: S3 버킷(`korea-sw-26-s3`)에 올려둔 PDF(예: 연차 서한) 다운받아 로컬 경로(`./documents` 등)로 정리하거나 원격 URL을 직접 읽도록 지원
- [ ] 전처리: 인코딩 통일, 불필요한 공백/마크다운 제거 규칙, 파일별 title/경로/페이지 등 메타데이터 구조 정의
- [ ] 청킹 전략: 토큰/문자 기반 chunk size와 overlap 결정, 청크별로 `source`, `chunk_id`, `start_line` 등 메타데이터 부여
- [ ] 임베딩 프로바이더 스위치: 개발용 `ollama:nomic-embed-text`, 운영용 `gemini-embedding-001`을 환경 변수로 선택(`EMBEDDING_PROVIDER`, `AI_API_KEY`, `OLLAMA_HOST`)
- [ ] 벡터스토어 생성: FAISS 인덱스와 메타데이터 매핑을 `./data/faiss.index`, `./data/faiss-meta.json` 등 경로로 저장
- [ ] CLI/스크립트화: `aws s3 sync s3://korea-sw-26-s3 ./documents && python scripts/ingest.py --source ./documents --model ollama/nomic-embed-text --index-path ./data/faiss.index`처럼 S3 동기화 포함 실행 방법 제공
- [ ] 검증: 샘플 질의로 top-k 검색 결과와 메타데이터를 출력해 인덱스 유효성 확인하는 간단한 테스트 추가

## server: RAG API (prompt 수신 + 검색 + LLM 호출)

- [ ] 환경 설정: `AI_API_KEY`, 임베딩/LLM 모델 선택, `INDEX_PATH`, `TOP_K` 기본값을 설정 파일이나 env로 관리
- [ ] 인덱스 로드: 부팅 시 FAISS 인덱스와 메타데이터 로딩 및 헬스체크/리로드 엔드포인트(`/health`, `/reload`) 제공
- [ ] RAG 파이프라인: 질의 임베딩 → FAISS 검색 → 상위 k개 컨텍스트 정렬/필터링 → 프롬프트 템플릿에 삽입 → LLM 호출
- [ ] 출처 표기: 응답에 사용된 청크의 `source`와 `chunk_id`/페이지 등을 함께 반환하고, 클라이언트가 표시할 수 있도록 구조화
- [ ] API 설계: `POST /query`에 `{ query, top_k }` 입력, 서버는 SSE/스트리밍으로 토큰과 citations를 단계적으로 전송
- [ ] 에러/레이트 리밋: 잘못된 요청, 키 미설정, 타임아웃 처리 및 로깅/트레이싱 추가
- [ ] 테스트: LLM 모킹하여 검색-응답 파이프라인 단위 테스트, 인덱스 없는 경우/빈 결과 등 예외 케이스 테스트

## client: 사용자 입력 및 스트리밍 응답 표시

- [ ] 입력 UI: 단일 입력창과 전송 버튼(또는 CLI 입력) 제공, 이전 대화 히스토리 표시 방식 정의
- [ ] 스트리밍 처리: 서버 SSE를 구독하거나 fetch ReadableStream으로 토큰을 실시간 렌더링
- [ ] 출처 노출: 서버가 준 citations를 응답 하단에 리스트/배지로 표시하고, 클릭 시 `source` 경로/페이지로 이동 가능하도록 렌더링 규칙 정의
- [ ] 상태 표시: 로딩/에러/중단/재시도 UI, 토큰 소비량·응답 시간 등 부가 정보 표시 여부 결정
- [ ] 설정 토글: 개발/운영용 서버 주소, top-k, 모델 선택 등 기본 설정을 환경 변수(.env)나 UI 토글로 주입
- [ ] 테스트: 스트리밍 파싱, 에러 상태, citation 렌더링에 대한 단위 테스트 및 최소한의 스냅샷/통합 테스트 추가
