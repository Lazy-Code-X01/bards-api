import pytest
import httpx

BASE_URL = "http://localhost:8001/api/v1"
ORG_A_HEADERS = {"x-user-id": "demo-org-a", "x-organization-id": "org-alpha"}
ORG_B_HEADERS = {"x-user-id": "demo-org-b", "x-organization-id": "org-beta"}
U1_HEADERS = {"x-user-id": "u1", "x-organization-id": "org-alpha"}


@pytest.fixture
def client():
    with httpx.Client(base_url=BASE_URL, headers=ORG_A_HEADERS, timeout=10.0) as c:
        yield c


@pytest.fixture
def org_b_client():
    with httpx.Client(base_url=BASE_URL, headers=ORG_B_HEADERS, timeout=10.0) as c:
        yield c


@pytest.fixture
def u1_client():
    with httpx.Client(base_url=BASE_URL, headers=U1_HEADERS, timeout=10.0) as c:
        yield c
