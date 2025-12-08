# TODO

- [x] 선정할 임베딩 모델과 벡터스토어 조사/결정 (FAISS, Chroma 등 베드락·스트림릿 제외)
  - FAISS
- [x] 최소 2개 이상의 데이터 소스 수집 및 정리
  - ~~./documents에 저장해 둠~~ s3에 업로드 해둠
  - https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2019-Shareholder-Letter.pdf
  - https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2020-Shareholder-Letter.pdf
  - https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2021-Shareholder-Letter.pdf
  - https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2022-Shareholder-Letter.pdf
  - ingest 과정에서는 S3에서 내려받거나 URL을 직접 읽도록 경로 설정 필요
- [x] RAG 파이프라인 구축 및 응답에 참조 문서 출처 표기
  - 이건 구현하면서 이렇게 구현해야하는 것
- [x] API 키 환경 변수 설정 (username 전달 후 키 수령)
  - AI_API_KEY로 설정
  - gemini-embedding-001 model 사용
  - 다만 테스트 과정에서 비용 지출이 없도록 embedding model 교체 가능하도록 설계하여 개발 과정에선 ollama 사용
    - ollama에서는 `nomic-embed-text` 사용
