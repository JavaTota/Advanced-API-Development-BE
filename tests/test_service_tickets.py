from application import create_app
from application.models import db
import unittest


class TestServiceTickets(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

        # Create costumer
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })

        # Login costumer
        login = self.client.post('/costumers/login', json={
            "email": "johnd@email.com",
            "password": "123"
        })

        self.token = login.json["auth_token"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_service_ticket(self):
        response = self.client.post('/service_tickets/', json={
            "VIN": "1HGBH41JXMN109186",
            "service_desc": "Oil change"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["VIN"], "1HGBH41JXMN109186")
        self.assertEqual(response.json["service_desc"], "Oil change")

    def test_get_service_ticket(self):
        create = self.client.post('/service_tickets/', json={
            "VIN": "1HGBH41JXMN109186",
            "service_desc": "Oil change"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        ticket_id = create.json["id"]

        response = self.client.get(f'/service_tickets/{ticket_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["VIN"], "1HGBH41JXMN109186")

    def test_get_service_tickets(self):
        self.client.post('/service_tickets/', json={
            "VIN": "1HGBH41JXMN109186",
            "service_desc": "Oil change"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        self.client.post('/service_tickets/', json={
            "VIN": "2HGCM82633A004352",
            "service_desc": "Brake inspection"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        response = self.client.get('/service_tickets/')

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        vins = [ticket["VIN"] for ticket in data]
        self.assertIn("1HGBH41JXMN109186", vins)
        self.assertIn("2HGCM82633A004352", vins)

    def test_get_my_tickets(self):
        self.client.post('/service_tickets/', json={
            "VIN": "1HGBH41JXMN109186",
            "service_desc": "Oil change"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        response = self.client.get('/service_tickets/my_tickets', headers={
            "Authorization": f"Bearer {self.token}"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 1)
        self.assertEqual(response.json["tickets"][0]["VIN"], "1HGBH41JXMN109186")

    def test_delete_service_ticket(self):
        create = self.client.post('/service_tickets/', json={
            "VIN": "1HGBH41JXMN109186",
            "service_desc": "Oil change"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })

        ticket_id = create.json["id"]

        response = self.client.delete(
            f'/service_tickets/{ticket_id}',
            headers={"Authorization": f"Bearer {self.token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "service_ticket deleted")