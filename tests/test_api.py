import os

os.environ["DATABASE_URL"] = "sqlite:///./test_finance_dashboard.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient

from app.bootstrap import initialize_database
from app.database import Base, engine
from app.main import app


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    initialize_database()


def teardown_function() -> None:
    Base.metadata.drop_all(bind=engine)


def test_role_based_permissions() -> None:
    with TestClient(app) as client:
        admin_token = _login(client, "admin@financeapp.com", "Admin@123")
        admin_headers = _auth_headers(admin_token)

        create_analyst = client.post(
            "/users",
            headers=admin_headers,
            json={
                "full_name": "Analyst One",
                "email": "analyst@financeapp.com",
                "password": "Analyst123",
                "role": "analyst",
                "is_active": True,
            },
        )
        assert create_analyst.status_code == 201

        create_viewer = client.post(
            "/users",
            headers=admin_headers,
            json={
                "full_name": "Viewer One",
                "email": "viewer@financeapp.com",
                "password": "Viewer123",
                "role": "viewer",
                "is_active": True,
            },
        )
        assert create_viewer.status_code == 201

        analyst_token = _login(client, "analyst@financeapp.com", "Analyst123")
        viewer_token = _login(client, "viewer@financeapp.com", "Viewer123")

        viewer_records = client.get("/records", headers=_auth_headers(viewer_token))
        assert viewer_records.status_code == 403

        analyst_create_record = client.post(
            "/records",
            headers=_auth_headers(analyst_token),
            json={
                "amount": "1250.00",
                "type": "income",
                "category": "Salary",
                "record_date": "2026-03-01",
            },
        )
        assert analyst_create_record.status_code == 403

        viewer_summary = client.get("/dashboard/summary", headers=_auth_headers(viewer_token))
        assert viewer_summary.status_code == 200


def test_summary_calculation_and_filters() -> None:
    with TestClient(app) as client:
        admin_token = _login(client, "admin@financeapp.com", "Admin@123")
        admin_headers = _auth_headers(admin_token)

        create_analyst = client.post(
            "/users",
            headers=admin_headers,
            json={
                "full_name": "Analyst Two",
                "email": "analyst2@financeapp.com",
                "password": "Analyst456",
                "role": "analyst",
                "is_active": True,
            },
        )
        assert create_analyst.status_code == 201
        analyst_token = _login(client, "analyst2@financeapp.com", "Analyst456")

        for payload in [
            {
                "amount": "5000.00",
                "type": "income",
                "category": "Salary",
                "record_date": "2026-02-01",
                "notes": "Primary salary",
            },
            {
                "amount": "1500.00",
                "type": "expense",
                "category": "Rent",
                "record_date": "2026-02-03",
                "notes": "House rent",
            },
            {
                "amount": "800.00",
                "type": "income",
                "category": "Freelance",
                "record_date": "2026-02-15",
                "notes": "Part-time project",
            },
        ]:
            create_record = client.post("/records", headers=admin_headers, json=payload)
            assert create_record.status_code == 201

        income_records = client.get(
            "/records",
            headers=_auth_headers(analyst_token),
            params={"type": "income"},
        )
        assert income_records.status_code == 200
        assert income_records.json()["total"] == 2

        summary = client.get("/dashboard/summary", headers=_auth_headers(analyst_token))
        assert summary.status_code == 200
        summary_data = summary.json()
        assert summary_data["total_income"] == 5800.0
        assert summary_data["total_expense"] == 1500.0
        assert summary_data["net_balance"] == 4300.0

        trends = client.get(
            "/dashboard/trends",
            headers=_auth_headers(analyst_token),
            params={"period": "monthly", "points": 12},
        )
        assert trends.status_code == 200
        trend_data = trends.json()
        assert len(trend_data) == 1
        assert trend_data[0]["period"] == "2026-02"


def test_prevent_disabling_last_admin() -> None:
    with TestClient(app) as client:
        admin_token = _login(client, "admin@financeapp.com", "Admin@123")
        response = client.get("/users", headers=_auth_headers(admin_token))
        assert response.status_code == 200
        admin_id = response.json()[0]["id"]

        deactivate = client.delete(f"/users/{admin_id}", headers=_auth_headers(admin_token))
        assert deactivate.status_code == 400
        assert "last active admin" in deactivate.json()["detail"]
