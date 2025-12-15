#show link: set text(blue)
#import "@preview/polylux:0.4.0": *
#set page(paper: "presentation-16-9")
#set text(size: 25pt, font: "NanumMyeongjo")

= COSE457 RAG 챗봇
LangChain · FAISS · Gemini (embedding / generation)
#link("https://github.com/BeLeap/252RCOSE45700")[BeLeap/252RCOSE45700]

#pagebreak()

= 프로젝트 개요
- 목표: LangChain 기반 RAG 파이프라인을 구축해 PDF 레터에서 답변을 생성하고 출처를 표기
- 데이터: S3에 저장된 2019~2022 Shareholder Letter PDF 4종
- 모델: 임베딩 `gemini-embedding-001`, 생성 `gemini-3-pro-preview`
- 제약: 베드락·스트림릿 미사용

#pagebreak()

= 요구사항 대응
- 최소 2개 이상 데이터 소스 → 4개 PDF 활용
- 임베딩 & 벡터스토어 → Google Embedding + FAISS
- 출처 표기 → chunk별 `source`, `chunk_id`, `page` 메타데이터를 응답에 포함
- 환경 설정 → `GOOGLE_API_KEY`, `RAG_*` env로 모델·인덱스 경로 제어

#pagebreak()

= 아키텍처
- Ingest 스크립트(`scripts/ingest.py`): PDF 다운로드 → 정규화 → 청킹 → 임베딩 → FAISS/메타데이터 저장
- 서버(`server/main.py`): FastAPI로 `/health`, `/reload`, `/query`(SSE 스트리밍) 제공
- 클라이언트(`client/`): 단일 페이지 UI, SSE 스트림으로 토큰/출처 실시간 렌더링

#pagebreak()

= Ingest 흐름
- 입력: 로컬 경로 또는 URL 목록 (기본값은 S3 PDF 4종)
- 전처리: 공백 정리, 파일 경로·원본 URL을 `source`/`path` 메타데이터에 저장
- 청킹: `RecursiveCharacterTextSplitter`(size=800, overlap=200), `chunk_id`/`chunk_size` 부여
- 저장: LangChain FAISS 디렉터리(`data/faiss_store`), 독립 FAISS 인덱스(`data/faiss.index`), 메타데이터(`data/faiss-meta.json`)
- 검증: `--verify-query "..." --verify-top-k 3`로 유효성 점검 가능

#pagebreak()

= 서버 RAG 파이프라인
- 구동 시 인덱스/메타데이터 로드 (`RAG_INDEX_DIR`, `RAG_METADATA_PATH`)
- `/query`: 질의 임베딩 → FAISS top-k 검색 → 프롬프트 생성(이전 대화 포함) → Gemini 스트리밍
- SSE 이벤트: `citations`(한 번), `token`(여러 번), `done` 또는 `error`
- 안전장치: 키 미설정/인덱스 미로딩 시 500/503 반환, 로깅 추가

#pagebreak()

= 클라이언트 UI
- 입력: 서버 URL, top-k, 질문
- 스트리밍: SSE 파싱으로 토큰을 실시간 반영, 중간에 Stop 가능
- 출처 표시: source/chunk/page/score, 미리보기 텍스트 제공
- 상태 표시: Streaming/Done/Error/Stopped, 타이머로 응답 시간 확인

#pagebreak()

= 실행 방법 (로컬)
1. 의존성 설치: `pip install -r requirements.txt`
2. 인덱스 생성:
```bash
python scripts/ingest.py \
  --verify-query "What was emphasized about cash flow?"
```
3. 서버 실행: `uvicorn server.main:app --reload --port 8000`
4. 클라이언트 열기:
```bash
cd client && python -m http.server 3000
```
5. 브라우저에서 `http://localhost:3000` → 서버 URL 입력 후 질문

#pagebreak()

= 데모 동작
- `/health`로 인덱스 로드 여부 확인
- 질문 입력 → 최초 SSE 이벤트로 citations 수신 → 토큰 스트림이 누적되어 답변 완성
- 답변 하단의 출처 배지 클릭/확인으로 신뢰도 점검
