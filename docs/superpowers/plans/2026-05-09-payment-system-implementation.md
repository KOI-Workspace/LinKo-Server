# 결제 시스템 구현 계획

> **에이전트 작업자용:** 필수 하위 스킬: 이 계획을 작업 단위로 구현하려면 superpowers:subagent-driven-development(권장) 또는 superpowers:executing-plans를 사용한다. 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다.

**목표:** Lemon Squeezy 기반 Free/Pro 월간 구독 결제, 로컬 구독 상태 저장, 월간 사용량 제한을 LinKo Server에 추가한다.

**아키텍처:** 결제 기능은 기존 FastAPI 앱 안의 작은 billing 도메인으로 만든다. Lemon Squeezy API 호출과 웹훅 파싱은 제공자 어댑터에 가두고, 나머지 애플리케이션은 내부 구독, 플랜, 사용량 개념에만 의존한다. 일반 제품 API 요청은 Lemon Squeezy를 실시간 호출하지 않고 로컬 DB의 구독/사용량 상태로 권한을 판단한다.

**기술 스택:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic, httpx, pytest, Lemon Squeezy hosted checkout, Lemon Squeezy webhooks.

---

## 선행조건

먼저 FastAPI MVP 구현 계획이 완료되어 있어야 한다. 이 계획은 다음 파일과 구조가 이미 존재한다고 가정한다.

- `app/main.py`: `/api` 라우터 등록.
- `app/core/config.py`: Pydantic settings.
- `app/db/session.py`: SQLAlchemy `get_db` 의존성.
- `app/db/base.py`: declarative `Base`.
- `app/models/user.py`: `User` 모델.
- `app/api/deps.py`: 현재 인증 사용자를 반환하는 `get_current_user`.
- `app/api/videos.py`: `GET /api/videos/metadata`.
- `pyproject.toml`: FastAPI, SQLAlchemy, httpx, pytest 의존성.

## 첫 버전 제품 결정

- Free 월간 사용량 한도: `5`.
- Pro 월간 사용량 한도: `100`.
- Pro 월간 가격은 Lemon Squeezy 대시보드에서 설정한다.
- 서버는 `LEMON_SQUEEZY_PRO_VARIANT_ID`로 Pro variant를 참조한다.
- `past_due`, `cancelled`, `expired` 상태에는 Pro 유예 기간을 주지 않는다.
- 첫 제한 대상 작업은 `GET /api/videos/metadata`이다.
- 월간 한도를 모두 사용하면 `402 Payment Required`를 반환한다.

## 파일 구조

- `app/core/config.py` 수정: Lemon Squeezy 설정과 플랜 한도 설정 추가.
- `app/models/billing.py` 생성: `Subscription`, `UsagePeriod`, `PaymentProviderEvent` 모델.
- `app/db/base.py` 수정: billing 모델을 metadata에 포함.
- `app/schemas/billing.py` 생성: 체크아웃/구독 응답 스키마.
- `app/services/billing.py` 생성: 제공자 중립 권한/사용량 정책.
- `app/services/lemon_squeezy.py` 생성: Lemon Squeezy 체크아웃 생성, 서명 검증, 웹훅 파싱.
- `app/api/billing.py` 생성: 인증된 체크아웃 생성과 구독 상태 조회 엔드포인트.
- `app/api/webhooks.py` 생성: Lemon Squeezy 웹훅 엔드포인트.
- `app/main.py` 수정: billing과 webhook 라우터 등록.
- `app/api/videos.py` 수정: metadata 조회에 월간 사용량 제한 적용.
- `tests/test_billing_settings.py` 생성: billing 설정 테스트.
- `tests/test_billing_models.py` 생성: billing 모델 테스트.
- `tests/test_billing_policy.py` 생성: 권한/사용량 정책 테스트.
- `tests/test_lemon_squeezy.py` 생성: provider adapter 테스트.
- `tests/test_billing_api.py` 생성: billing HTTP API 테스트.
- `tests/test_billing_webhooks.py` 생성: 웹훅 동기화와 멱등성 테스트.
- `tests/test_video_usage_limits.py` 생성: metadata endpoint 사용량 제한 테스트.

---

### 작업 1: 결제 설정 추가

**파일:**
- 수정: `app/core/config.py`
- 테스트: `tests/test_billing_settings.py`

- [ ] **1단계: 실패하는 설정 테스트 작성**

`tests/test_billing_settings.py` 생성:

```python
from app.core.config import Settings


def test_billing_settings_have_safe_defaults():
    settings = Settings()

    assert settings.free_monthly_usage_limit == 5
    assert settings.pro_monthly_usage_limit == 100
    assert settings.lemon_squeezy_api_key == "dev-lemon-squeezy-api-key"
    assert settings.lemon_squeezy_store_id == "dev-lemon-squeezy-store-id"
    assert settings.lemon_squeezy_pro_variant_id == "dev-lemon-squeezy-pro-variant-id"
    assert settings.lemon_squeezy_webhook_secret == "dev-lemon-squeezy-webhook-secret"
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_billing_settings.py -v`

예상: billing 설정 필드가 아직 없으므로 FAIL.

- [ ] **3단계: `Settings`에 결제 설정 추가**

`app/core/config.py`의 `Settings` 클래스에 다음 필드를 추가한다.

```python
free_monthly_usage_limit: int = 5
pro_monthly_usage_limit: int = 100
lemon_squeezy_api_key: str = "dev-lemon-squeezy-api-key"
lemon_squeezy_store_id: str = "dev-lemon-squeezy-store-id"
lemon_squeezy_pro_variant_id: str = "dev-lemon-squeezy-pro-variant-id"
lemon_squeezy_webhook_secret: str = "dev-lemon-squeezy-webhook-secret"
```

- [ ] **4단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_billing_settings.py -v`

예상: PASS.

- [ ] **5단계: 커밋**

```bash
git add app/core/config.py tests/test_billing_settings.py
git commit -m "Add billing configuration"
```

---

### 작업 2: 결제 영속성 모델 추가

**파일:**
- 생성: `app/models/billing.py`
- 수정: `app/db/base.py`
- 테스트: `tests/test_billing_models.py`

- [ ] **1단계: 실패하는 모델 테스트 작성**

`tests/test_billing_models.py` 생성:

```python
from datetime import UTC, datetime

from app.models.billing import PaymentProviderEvent, Subscription, UsagePeriod


def test_subscription_defaults_to_free_status():
    subscription = Subscription(user_id=1)

    assert subscription.provider == "internal"
    assert subscription.plan == "free"
    assert subscription.status == "free"
    assert subscription.cancel_at_period_end is False


def test_usage_period_stores_count_and_dates():
    starts_at = datetime(2026, 5, 1, tzinfo=UTC)
    ends_at = datetime(2026, 6, 1, tzinfo=UTC)

    usage = UsagePeriod(
        user_id=1,
        period_start=starts_at,
        period_end=ends_at,
        used_count=3,
    )

    assert usage.used_count == 3
    assert usage.period_start == starts_at
    assert usage.period_end == ends_at


def test_payment_provider_event_records_processing_key():
    event = PaymentProviderEvent(
        provider="lemon_squeezy",
        provider_event_id="evt_123",
        event_name="subscription_created",
        payload={"meta": {"event_name": "subscription_created"}},
    )

    assert event.provider == "lemon_squeezy"
    assert event.provider_event_id == "evt_123"
    assert event.event_name == "subscription_created"
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_billing_models.py -v`

예상: `app.models.billing`이 없으므로 FAIL.

- [ ] **3단계: billing 모델 추가**

`app/models/billing.py` 생성:

```python
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="internal", nullable=False)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class UsagePeriod(Base):
    __tablename__ = "usage_periods"
    __table_args__ = (UniqueConstraint("user_id", "period_start", "period_end", name="uq_usage_period_user_window"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class PaymentProviderEvent(Base):
    __tablename__ = "payment_provider_events"
    __table_args__ = (UniqueConstraint("provider", "provider_event_id", name="uq_payment_provider_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

`app/db/base.py`에 billing 모델 import를 추가한다.

```python
from app.db.session import Base
from app.models import billing, user, video  # noqa: F401
```

- [ ] **4단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_billing_models.py -v`

예상: PASS.

- [ ] **5단계: 커밋**

```bash
git add app/models/billing.py app/db/base.py tests/test_billing_models.py
git commit -m "Add billing persistence models"
```

---

### 작업 3: 제공자 중립 권한/사용량 정책 추가

**파일:**
- 생성: `app/services/billing.py`
- 테스트: `tests/test_billing_policy.py`

- [ ] **1단계: 실패하는 정책 테스트 작성**

`tests/test_billing_policy.py` 생성:

```python
from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.models.billing import Subscription, UsagePeriod
from app.services.billing import BillingLimitExceeded, get_monthly_allowance, require_usage_available


def test_free_plan_gets_free_allowance():
    settings = Settings(free_monthly_usage_limit=5, pro_monthly_usage_limit=100)
    subscription = Subscription(plan="free", status="free")

    assert get_monthly_allowance(subscription, settings) == 5


def test_active_pro_gets_pro_allowance():
    settings = Settings(free_monthly_usage_limit=5, pro_monthly_usage_limit=100)
    subscription = Subscription(plan="pro", status="active")

    assert get_monthly_allowance(subscription, settings) == 100


@pytest.mark.parametrize("status", ["past_due", "cancelled", "expired"])
def test_inactive_pro_status_gets_free_allowance(status):
    settings = Settings(free_monthly_usage_limit=5, pro_monthly_usage_limit=100)
    subscription = Subscription(plan="pro", status=status)

    assert get_monthly_allowance(subscription, settings) == 5


def test_usage_limit_raises_when_exhausted():
    settings = Settings(free_monthly_usage_limit=5, pro_monthly_usage_limit=100)
    subscription = Subscription(plan="free", status="free")
    usage = UsagePeriod(
        user_id=1,
        period_start=datetime(2026, 5, 1, tzinfo=UTC),
        period_end=datetime(2026, 6, 1, tzinfo=UTC),
        used_count=5,
    )

    with pytest.raises(BillingLimitExceeded) as exc_info:
        require_usage_available(subscription, usage, settings)

    assert exc_info.value.allowance == 5
    assert exc_info.value.used_count == 5
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_billing_policy.py -v`

예상: `app.services.billing`이 없으므로 FAIL.

- [ ] **3단계: billing policy service 추가**

`app/services/billing.py` 생성:

```python
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.billing import Subscription, UsagePeriod


@dataclass(frozen=True)
class UsageAllowance:
    allowance: int
    used_count: int
    remaining_count: int


class BillingLimitExceeded(Exception):
    def __init__(self, allowance: int, used_count: int) -> None:
        self.allowance = allowance
        self.used_count = used_count
        super().__init__("Monthly usage limit exceeded")


def get_monthly_allowance(subscription: Subscription | None, settings: Settings) -> int:
    if subscription and subscription.plan == "pro" and subscription.status == "active":
        return settings.pro_monthly_usage_limit
    return settings.free_monthly_usage_limit


def require_usage_available(
    subscription: Subscription | None,
    usage_period: UsagePeriod,
    settings: Settings,
) -> UsageAllowance:
    allowance = get_monthly_allowance(subscription, settings)
    remaining = allowance - usage_period.used_count
    if remaining <= 0:
        raise BillingLimitExceeded(allowance=allowance, used_count=usage_period.used_count)
    return UsageAllowance(allowance=allowance, used_count=usage_period.used_count, remaining_count=remaining)


def current_calendar_month(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(UTC)
    period_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)
    return period_start, period_end


def get_or_create_subscription(db: Session, user_id: int) -> Subscription:
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()
    if subscription:
        return subscription
    subscription = Subscription(user_id=user_id)
    db.add(subscription)
    db.flush()
    return subscription


def get_or_create_current_usage_period(db: Session, user_id: int, now: datetime | None = None) -> UsagePeriod:
    period_start, period_end = current_calendar_month(now)
    usage_period = (
        db.query(UsagePeriod)
        .filter(
            UsagePeriod.user_id == user_id,
            UsagePeriod.period_start == period_start,
            UsagePeriod.period_end == period_end,
        )
        .one_or_none()
    )
    if usage_period:
        return usage_period
    usage_period = UsagePeriod(user_id=user_id, period_start=period_start, period_end=period_end, used_count=0)
    db.add(usage_period)
    db.flush()
    return usage_period


def increment_usage(usage_period: UsagePeriod) -> None:
    usage_period.used_count += 1
```

- [ ] **4단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_billing_policy.py -v`

예상: PASS.

- [ ] **5단계: 커밋**

```bash
git add app/services/billing.py tests/test_billing_policy.py
git commit -m "Add billing entitlement policy"
```

---

### 작업 4: Lemon Squeezy 어댑터 추가

**파일:**
- 생성: `app/services/lemon_squeezy.py`
- 테스트: `tests/test_lemon_squeezy.py`

- [ ] **1단계: 실패하는 어댑터 테스트 작성**

`tests/test_lemon_squeezy.py` 생성:

```python
import hashlib
import hmac

from app.core.config import Settings
from app.services.lemon_squeezy import build_checkout_payload, verify_webhook_signature


def test_build_checkout_payload_includes_user_metadata():
    settings = Settings(lemon_squeezy_store_id="store_123", lemon_squeezy_pro_variant_id="variant_456")

    payload = build_checkout_payload(user_id=7, user_email="user@example.com", settings=settings)

    assert payload["data"]["type"] == "checkouts"
    assert payload["data"]["attributes"]["checkout_data"]["email"] == "user@example.com"
    assert payload["data"]["attributes"]["checkout_data"]["custom"]["user_id"] == "7"
    assert payload["data"]["relationships"]["store"]["data"]["id"] == "store_123"
    assert payload["data"]["relationships"]["variant"]["data"]["id"] == "variant_456"


def test_verify_webhook_signature_accepts_valid_signature():
    secret = "secret"
    body = b'{"meta":{"event_name":"subscription_created"}}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, signature, secret) is True


def test_verify_webhook_signature_rejects_invalid_signature():
    assert verify_webhook_signature(b"{}", "bad-signature", "secret") is False
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_lemon_squeezy.py -v`

예상: `app.services.lemon_squeezy`가 없으므로 FAIL.

- [ ] **3단계: Lemon Squeezy 어댑터 추가**

`app/services/lemon_squeezy.py` 생성:

```python
from dataclasses import dataclass
import hashlib
import hmac
from typing import Any

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class LemonSqueezyEvent:
    provider_event_id: str
    event_name: str
    user_id: int
    provider_customer_id: str
    provider_subscription_id: str
    plan: str
    status: str
    current_period_start: str | None
    current_period_end: str | None
    cancel_at_period_end: bool
    raw_payload: dict[str, Any]


def build_checkout_payload(user_id: int, user_email: str, settings: Settings) -> dict[str, Any]:
    return {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {"user_id": str(user_id)},
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": settings.lemon_squeezy_store_id}},
                "variant": {"data": {"type": "variants", "id": settings.lemon_squeezy_pro_variant_id}},
            },
        }
    }


async def create_checkout_url(user_id: int, user_email: str, settings: Settings) -> str:
    payload = build_checkout_payload(user_id=user_id, user_email=user_email, settings=settings)
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {settings.lemon_squeezy_api_key}",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post("https://api.lemonsqueezy.com/v1/checkouts", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["attributes"]["url"]


def verify_webhook_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def map_subscription_status(provider_status: str) -> str:
    if provider_status == "active":
        return "active"
    if provider_status == "past_due":
        return "past_due"
    if provider_status in {"cancelled", "expired", "unpaid"}:
        return "cancelled"
    return "expired"


def parse_subscription_event(provider_event_id: str, payload: dict[str, Any]) -> LemonSqueezyEvent:
    meta = payload.get("meta", {})
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    custom_data = meta.get("custom_data") or attributes.get("custom_data") or {}
    raw_user_id = custom_data.get("user_id")
    if not raw_user_id:
        raise ValueError("Lemon Squeezy webhook missing user_id custom data")

    return LemonSqueezyEvent(
        provider_event_id=provider_event_id,
        event_name=str(meta.get("event_name") or ""),
        user_id=int(raw_user_id),
        provider_customer_id=str(attributes.get("customer_id") or ""),
        provider_subscription_id=str(data.get("id") or ""),
        plan="pro",
        status=map_subscription_status(str(attributes.get("status") or "")),
        current_period_start=attributes.get("created_at"),
        current_period_end=attributes.get("renews_at") or attributes.get("ends_at"),
        cancel_at_period_end=bool(attributes.get("cancelled")),
        raw_payload=payload,
    )
```

- [ ] **4단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_lemon_squeezy.py -v`

예상: PASS.

- [ ] **5단계: 커밋**

```bash
git add app/services/lemon_squeezy.py tests/test_lemon_squeezy.py
git commit -m "Add Lemon Squeezy billing adapter"
```

---

### 작업 5: Billing API 추가

**파일:**
- 생성: `app/schemas/billing.py`
- 생성: `app/api/billing.py`
- 수정: `app/main.py`
- 테스트: `tests/test_billing_api.py`

- [ ] **1단계: 실패하는 API 테스트 작성**

`tests/test_billing_api.py` 생성:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.billing import router
from app.api.deps import get_current_user
from app.models.user import User


def test_create_checkout_returns_url(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api")
    user = User(id=1, email="user@example.com", name="User", picture=None, google_sub="google-1")

    async def override_current_user():
        return user

    async def fake_checkout_url(user_id, user_email, settings):
        return "https://checkout.lemonsqueezy.com/checkout/test"

    app.dependency_overrides[get_current_user] = override_current_user
    monkeypatch.setattr("app.api.billing.create_checkout_url", fake_checkout_url)
    client = TestClient(app)

    response = client.post("/api/billing/checkout")

    assert response.status_code == 200
    assert response.json() == {"checkout_url": "https://checkout.lemonsqueezy.com/checkout/test"}
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_billing_api.py -v`

예상: `app.api.billing`이 없으므로 FAIL.

- [ ] **3단계: billing 스키마 추가**

`app/schemas/billing.py` 생성:

```python
from datetime import datetime

from pydantic import BaseModel


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    monthly_allowance: int
    used_count: int
    remaining_count: int
    cancel_at_period_end: bool
```

- [ ] **4단계: billing 라우터 추가**

`app/api/billing.py` 생성:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.billing import CheckoutResponse, SubscriptionResponse
from app.services.billing import get_monthly_allowance, get_or_create_current_usage_period, get_or_create_subscription
from app.services.lemon_squeezy import create_checkout_url

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_billing_checkout(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> CheckoutResponse:
    try:
        checkout_url = await create_checkout_url(current_user.id, current_user.email, settings)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to create checkout") from exc
    return CheckoutResponse(checkout_url=checkout_url)


@router.get("/subscription", response_model=SubscriptionResponse)
def get_billing_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SubscriptionResponse:
    subscription = get_or_create_subscription(db, current_user.id)
    usage_period = get_or_create_current_usage_period(db, current_user.id)
    allowance = get_monthly_allowance(subscription, settings)
    return SubscriptionResponse(
        plan=subscription.plan,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        monthly_allowance=allowance,
        used_count=usage_period.used_count,
        remaining_count=max(allowance - usage_period.used_count, 0),
        cancel_at_period_end=subscription.cancel_at_period_end,
    )
```

- [ ] **5단계: `app/main.py`에 billing 라우터 등록**

기존 라우터 import와 include 목록에 billing을 추가한다.

```python
from app.api import billing

api_router.include_router(billing.router)
```

- [ ] **6단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_billing_api.py -v`

예상: PASS.

- [ ] **7단계: 커밋**

```bash
git add app/schemas/billing.py app/api/billing.py app/main.py tests/test_billing_api.py
git commit -m "Add billing subscription API"
```

---

### 작업 6: Lemon Squeezy 웹훅 엔드포인트 추가

**파일:**
- 생성: `app/api/webhooks.py`
- 수정: `app/main.py`
- 테스트: `tests/test_billing_webhooks.py`

- [ ] **1단계: 실패하는 웹훅 테스트 작성**

`tests/test_billing_webhooks.py` 생성:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.webhooks import router


def test_webhook_rejects_invalid_signature():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    client = TestClient(app)

    response = client.post("/api/webhooks/lemon-squeezy", json={}, headers={"X-Signature": "bad"})

    assert response.status_code == 401
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_billing_webhooks.py -v`

예상: `app.api.webhooks`가 없으므로 FAIL.

- [ ] **3단계: 웹훅 라우터 추가**

`app/api/webhooks.py` 생성:

```python
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.billing import PaymentProviderEvent, Subscription
from app.services.lemon_squeezy import parse_subscription_event, verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/lemon-squeezy")
async def receive_lemon_squeezy_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_event_id: str | None = Header(default=None, alias="X-Event-Id"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    body = await request.body()
    if not verify_webhook_signature(body, x_signature, settings.lemon_squeezy_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    provider_event_id = x_event_id or str(payload.get("data", {}).get("id") or "")
    existing_event = (
        db.query(PaymentProviderEvent)
        .filter(
            PaymentProviderEvent.provider == "lemon_squeezy",
            PaymentProviderEvent.provider_event_id == provider_event_id,
        )
        .one_or_none()
    )
    if existing_event:
        return {"status": "duplicate"}

    event = parse_subscription_event(provider_event_id, payload)
    subscription = db.query(Subscription).filter(Subscription.user_id == event.user_id).one_or_none()
    if subscription is None:
        subscription = Subscription(user_id=event.user_id)
        db.add(subscription)

    subscription.provider = "lemon_squeezy"
    subscription.provider_customer_id = event.provider_customer_id
    subscription.provider_subscription_id = event.provider_subscription_id
    subscription.plan = event.plan
    subscription.status = event.status
    subscription.cancel_at_period_end = event.cancel_at_period_end

    db.add(
        PaymentProviderEvent(
            provider="lemon_squeezy",
            provider_event_id=event.provider_event_id,
            event_name=event.event_name,
            payload=event.raw_payload,
        )
    )
    db.commit()
    return {"status": "processed"}
```

- [ ] **4단계: `app/main.py`에 webhook 라우터 등록**

기존 라우터 import와 include 목록에 webhooks를 추가한다.

```python
from app.api import webhooks

api_router.include_router(webhooks.router)
```

- [ ] **5단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_billing_webhooks.py -v`

예상: PASS.

- [ ] **6단계: 커밋**

```bash
git add app/api/webhooks.py app/main.py tests/test_billing_webhooks.py
git commit -m "Add Lemon Squeezy webhook sync"
```

---

### 작업 7: 동영상 메타데이터 조회에 사용량 제한 적용

**파일:**
- 수정: `app/api/videos.py`
- 테스트: `tests/test_video_usage_limits.py`

- [ ] **1단계: 실패하는 사용량 제한 테스트 작성**

`tests/test_video_usage_limits.py` 생성:

```python
from datetime import UTC, datetime

from app.core.config import Settings
from app.models.billing import Subscription, UsagePeriod
from app.services.billing import BillingLimitExceeded, require_usage_available


def test_free_metadata_lookup_limit_is_enforced():
    settings = Settings(free_monthly_usage_limit=5, pro_monthly_usage_limit=100)
    subscription = Subscription(user_id=1, plan="free", status="free")
    usage_period = UsagePeriod(
        user_id=1,
        period_start=datetime(2026, 5, 1, tzinfo=UTC),
        period_end=datetime(2026, 6, 1, tzinfo=UTC),
        used_count=5,
    )

    try:
        require_usage_available(subscription, usage_period, settings)
    except BillingLimitExceeded as exc:
        assert exc.allowance == 5
        assert exc.used_count == 5
    else:
        raise AssertionError("Expected BillingLimitExceeded")
```

- [ ] **2단계: 테스트를 실행해 실패 확인**

실행: `python3 -m pytest tests/test_video_usage_limits.py -v`

예상: 작업 3이 끝나기 전에는 import 실패, 작업 3 이후에는 route 적용 전 통합 테스트를 추가하면 FAIL.

- [ ] **3단계: metadata route에 사용량 검사 추가**

`app/api/videos.py`의 `GET /api/videos/metadata` 핸들러에서 metadata lookup 전에 사용량을 확인하고, 성공 후 카운터를 증가시킨다.

```python
from fastapi import HTTPException

from app.services.billing import (
    BillingLimitExceeded,
    get_or_create_current_usage_period,
    get_or_create_subscription,
    increment_usage,
    require_usage_available,
)


subscription = get_or_create_subscription(db, current_user.id)
usage_period = get_or_create_current_usage_period(db, current_user.id)
try:
    require_usage_available(subscription, usage_period, settings)
except BillingLimitExceeded as exc:
    raise HTTPException(
        status_code=402,
        detail={
            "code": "usage_limit_exceeded",
            "message": "Monthly usage limit exceeded",
            "monthly_allowance": exc.allowance,
            "used_count": exc.used_count,
        },
    ) from exc

metadata = await lookup_video_metadata(url=url, db=db, user=current_user)
increment_usage(usage_period)
db.commit()
return metadata
```

- [ ] **4단계: 테스트 통과 확인**

실행: `python3 -m pytest tests/test_video_usage_limits.py -v`

예상: PASS.

- [ ] **5단계: 기존 video 테스트와 함께 확인**

실행: `python3 -m pytest tests/test_videos.py tests/test_video_usage_limits.py -v`

예상: PASS.

- [ ] **6단계: 커밋**

```bash
git add app/api/videos.py tests/test_video_usage_limits.py
git commit -m "Enforce monthly video usage limits"
```

---

### 작업 8: 환경 변수와 README 문서화

**파일:**
- 수정: `.env.example`
- 수정: `README.md`
- 테스트: 자동 테스트 없음

- [ ] **1단계: `.env.example`에 결제 설정 추가**

```text
FREE_MONTHLY_USAGE_LIMIT=5
PRO_MONTHLY_USAGE_LIMIT=100
LEMON_SQUEEZY_API_KEY=replace-with-lemon-squeezy-api-key
LEMON_SQUEEZY_STORE_ID=replace-with-lemon-squeezy-store-id
LEMON_SQUEEZY_PRO_VARIANT_ID=replace-with-lemon-squeezy-pro-variant-id
LEMON_SQUEEZY_WEBHOOK_SECRET=replace-with-lemon-squeezy-webhook-secret
```

- [ ] **2단계: `README.md`에 Billing 섹션 추가**

```markdown
## Billing

LinKo는 Free/Pro 월간 구독 모델을 사용한다. 첫 결제 제공자는 Lemon Squeezy이며, hosted checkout, 구독 결제, billing webhook 처리를 위해 Merchant of Record로 사용한다.

프론트엔드는 업그레이드를 시작할 때 `POST /api/billing/checkout`을 호출한다. 서버는 Lemon Squeezy hosted checkout URL을 생성해 프론트엔드에 반환한다. Lemon Squeezy는 구독 생명주기 이벤트를 `POST /api/webhooks/lemon-squeezy`로 전송하고, 서버는 그 결과를 로컬 구독 상태로 저장한다.

제품 권한 판단은 로컬 DB 상태를 사용한다. 동영상 메타데이터 엔드포인트는 월간 사용량 한도를 검사하고, 현재 사용자가 한도를 모두 사용하면 `402 Payment Required`를 반환한다.
```

- [ ] **3단계: 문서 diff 확인**

실행: `git diff -- .env.example README.md`

예상: billing 환경 변수와 README billing 섹션만 추가된다.

- [ ] **4단계: 커밋**

```bash
git add .env.example README.md
git commit -m "Document billing configuration"
```

---

### 작업 9: 전체 검증

**파일:**
- 코드 변경 없음.

- [ ] **1단계: 결제 관련 테스트 실행**

실행:

```bash
python3 -m pytest tests/test_billing_settings.py tests/test_billing_models.py tests/test_billing_policy.py tests/test_lemon_squeezy.py tests/test_billing_api.py tests/test_billing_webhooks.py tests/test_video_usage_limits.py -v
```

예상: PASS.

- [ ] **2단계: 전체 테스트 실행**

실행: `python3 -m pytest -v`

예상: PASS.

- [ ] **3단계: git 상태 확인**

실행: `git status --short`

예상: 작업자가 만든 변경이 모두 커밋되어 clean working tree가 출력된다. 사용자가 별도로 남긴 미추적 파일이 있다면 해당 파일은 그대로 남아도 된다.

- [ ] **4단계: 수동 API 스모크 체크**

개발 서버를 실행한 뒤 다음 동작을 확인한다.

```text
GET  /api/billing/subscription: 새 사용자는 Free plan 상태를 받는다.
POST /api/billing/checkout: 인증된 사용자는 Lemon Squeezy checkout URL을 받는다.
POST /api/webhooks/lemon-squeezy: 잘못된 서명은 거부된다.
GET  /api/videos/metadata: Free 월간 한도 소진 후 402를 반환한다.
```

예상: 모든 항목이 적힌 동작과 일치한다.

## 자체 리뷰

스펙 커버리지:

- Lemon Squeezy 첫 제공자: 작업 1, 4, 5, 6, 8에서 다룬다.
- Free/Pro 월간 구독 모델: 작업 1, 3, 5에서 다룬다.
- 로컬 구독 상태 저장: 작업 2, 3, 5, 6에서 다룬다.
- 월간 사용량 기간과 한도 적용: 작업 2, 3, 7에서 다룬다.
- 웹훅 서명 검증과 멱등성: 작업 4, 6에서 다룬다.
- 제공자 어댑터 격리: 작업 4에서 다룬다.
- 한도 소진 시 `402 Payment Required`: 작업 7에서 다룬다.
- 테스트에서 provider 호출 mock 처리: 작업 4, 5, 6에서 다룬다.

빈칸 표현 점검:

- 미완성 표시나 나중에 채우라는 지시는 없음.

타입/이름 일관성:

- plan 식별자는 `free`, `pro`를 사용한다.
- subscription status는 `free`, `active`, `past_due`, `cancelled`, `expired`를 사용한다.
- provider 이름은 `lemon_squeezy`를 사용한다.
- usage 필드는 `period_start`, `period_end`, `used_count`를 사용한다.
