import token

from application import create_app
from application.models import db
import unittest

class TestCostumers(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_login_costumer(self):
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })
        login = self.client.post('/costumers/login', json={
            "email": "johnd@email.com",
            "password": "123"
        })

        self.assertEqual(login.status_code, 200)
        data = login.get_json()
        token = data["auth_token"]

        # 3. Use token on a protected route
        response = self.client.get(
            '/costumers/my_tickets',
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertIn(response.status_code, [200, 404])  # depends if tickets exist

    def test_create_costumer(self):
        response = self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "John Doe")

    def test_get_costumer(self):
        # First, create a costumer
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })

        response = self.client.get('/costumers/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "John Doe")

    def test_get_costumers(self):
        # First, create a costumer
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })

        self.client.post('/costumers/', json={
            "name": "Jane Doe",
            "phone": "3125550305",
            "email": "janed@email.com",
            "password": "123"
        })

        response = self.client.get('/costumers/')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIsInstance(data, list)

        self.assertEqual(len(data), 2)
        names = [costumer['name'] for costumer in data]
        self.assertIn("John Doe", names)
        self.assertIn("Jane Doe", names)

    def test_update_costumer(self):
        # First, create a costumer
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })

        login = self.client.post('/costumers/login', json={
            "email": "johnd@email.com",
            "password": "123"
        })

        token = login.json['auth_token']

        # Then, update the costumer
        response = self.client.put(f'/costumers/', json={
            "name": "John Updated",
            "email": "janed@email.com"
        }, headers={"Authorization": f"Bearer {token}"})


        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "John Updated")
        self.assertEqual(response.json['email'], "janed@email.com")

    def test_delete_costumer(self):
        # First, create a costumer
        self.client.post('/costumers/', json={
            "name": "John Doe",
            "phone": "3125550305",
            "email": "johnd@email.com",
            "password": "123"
        })
        
        login = self.client.post('/costumers/login', json={
            "email": "johnd@email.com",
            "password": "123"
        })

        token = login.json['auth_token']

        response = self.client.delete(f'/costumers/', headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "Costumer deleted")
