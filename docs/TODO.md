# TODO

- [x] 선정할 임베딩 모델과 벡터스토어 조사/결정 (FAISS, Chroma 등 베드락·스트림릿 제외)
  - FAISS
- [x] 최소 2개 이상의 데이터 소스 수집 및 정리
  - ./documents에 저장해 둠
- [x] RAG 파이프라인 구축 및 응답에 참조 문서 출처 표기
  - 이건 구현하면서 이렇게 구현해야하는 것
- [x] API 키 환경 변수 설정 (username 전달 후 키 수령)
  - AI_API_KEY로 설정
  - gemini-embedding-001 model 사용
  - 다만 테스트 과정에서 비용 지출이 없도록 embedding model 교체 가능하도록 설계하여 개발 과정에선 ollama 사용
    - ollama에서는 `nomic-embed-text` 사용
