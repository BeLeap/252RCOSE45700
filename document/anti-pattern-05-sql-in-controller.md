---
title: "Controller에서 직접 SQL/ORM 호출하기"
tags: ["web", "controller", "database"]
summary: "프레젠테이션 레이어가 데이터 접근 레이어를 침범하는 구조"
---

# Controller에서 직접 SQL/ORM 호출하기

## 개요
REST/GraphQL 엔드포인트 함수 안에서 바로 DB 쿼리를 날리는 패턴이다.
초기에는 빠르게 개발할 수 있지만, RAG가 코드 구조를 설명하거나 리팩터링을 추천할 때
가장 먼저 걸리는 부분이 된다.

## 문제
- 트랜잭션 경계를 관리하기 어렵다.
- 같은 쿼리가 여러 컨트롤러에 중복된다.
- 테스트 시에 컨트롤러 테스트가 곧 DB 테스트가 되어버린다.

## 흔한 형태
```python
@app.post("/users")
def create_user(payload: dict):
    # 여기서 바로 DB
    db.execute("INSERT INTO users ...")
    return {"ok": True}
```

## 개선
- Service/UseCase 레이어를 하나 두고, 컨트롤러는 그걸 호출만 한다.
- DB 접근은 Repository/DAO로 감싼다.
- 트랜잭션은 서비스 단위로 시작/종료한다.
