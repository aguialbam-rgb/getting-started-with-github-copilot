from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as api


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "activities", deepcopy(api.activities))
    return TestClient(api.app)


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert activities["Soccer Team"]["participants"] == []


def test_signup_adds_participant_and_returns_confirmation(client):
    email = "new.student@mergington.edu"
    response = client.post(
        "/activities/Soccer Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Soccer Team"
    }
    assert email in client.get("/activities").json()["Soccer Team"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    email = "michael@mergington.edu"
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
    assert client.get("/activities").json()["Chess Club"]["participants"].count(email) == 1