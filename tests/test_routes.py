import uuid
import pytest

BASE = "/api/routers/tasks"


class TestTaskRoutes:
    """Ручки для работы с задачами"""

    def test_create_task_success(self, client):
        """Создание задачи со всеми полями → получаем 201 и правильные данные"""
        response = client.post(BASE, json={"title": "Test Task", "priority": "HIGH"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["status"] == "PENDING"
        assert "id" in data

    def test_create_task_default_priority(self, client):
        """Если priority не указан → проставляется MEDIUM"""
        response = client.post(BASE, json={"title": "Default Priority Task"})
        assert response.status_code == 201
        assert response.json()["priority"] == "MEDIUM"

    def test_create_task_empty_title_fails(self, client):
        """Пустой заголовок → 422"""
        response = client.post(BASE, json={"title": ""})
        assert response.status_code == 422

    def test_create_task_missing_title_fails(self, client):
        """Заголовок обязателен → без него 422"""
        response = client.post(BASE, json={"priority": "HIGH"})
        assert response.status_code == 422

    def test_list_tasks_with_data(self, client):
        """Накидали задач → total показывает правильное количество"""
        client.post(BASE, json={"title": "Task 1"})
        client.post(BASE, json={"title": "Task 2"})
        client.post(BASE, json={"title": "Task 3"})
        client.post(BASE, json={"title": "Task 4"})
        client.post(BASE, json={"title": "Task 5"})
        response = client.get(BASE)
        assert response.status_code == 200
        assert response.json()["total"] == 5

    def test_list_tasks_pagination(self, client):
        """Пагинация работает: limit и offset режут список как надо"""
        for i in range(5):
            client.post(BASE, json={"title": f"Task {i}"})

        resp = client.get(f"{BASE}?limit=2&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2

    def test_list_tasks_status_filter(self, client):
        """Фильтр по статусу → возвращаются только задачи с нужным статусом"""
        client.post(BASE, json={"title": "Task 1"})
        resp = client.get(f"{BASE}?status=PENDING")
        assert resp.status_code == 200
        assert all(t["status"] == "PENDING" for t in resp.json()["items"])

    def test_list_tasks_invalid_status(self, client):
        """Левым статусом фильтруемся → валидация ругается 422"""
        resp = client.get(f"{BASE}?status=INVALID_STATUS")
        assert resp.status_code == 422

    def test_get_task_success(self, client):
        """Существующая задача отдаётся по id"""
        create_resp = client.post(BASE, json={"title": "Get Me"})
        task_id = create_resp.json()["id"]

        resp = client.get(f"{BASE}/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    def test_get_task_not_found(self, client):
        """Несуществующий id → 404"""
        resp = client.get(f"{BASE}/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_task_invalid_uuid(self, client):
        """Невалидный формат UUID → 422"""
        resp = client.get(f"{BASE}/not-a-uuid")
        assert resp.status_code == 422

    def test_get_task_status(self, client):
        """Смотрим только статус задачи через отдельный эндпоинт"""
        create_resp = client.post(BASE, json={"title": "Status Task"})
        task_id = create_resp.json()["id"]

        resp = client.get(f"{BASE}/{task_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == task_id
        assert "status" in data

    def test_cancel_task_success(self, client):
        """Отмена задачи → статус становится CANCELLED"""
        create_resp = client.post(BASE, json={"title": "Cancel Me"})
        task_id = create_resp.json()["id"]

        resp = client.delete(f"{BASE}/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancel_task_not_found(self, client):
        """Отмена несуществующей → 404"""
        resp = client.delete(f"{BASE}/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_limit_validation_min(self, client):
        """limit не может быть 0 → 422"""
        resp = client.get(f"{BASE}?limit=0")
        assert resp.status_code == 422

    def test_limit_validation_max(self, client):
        """limit не больше 100 → 101 уже 422"""
        resp = client.get(f"{BASE}?limit=101")
        assert resp.status_code == 422

    def test_offset_validation_negative(self, client):
        """Отрицательный offset → 422"""
        resp = client.get(f"{BASE}?offset=-1")
        assert resp.status_code == 422