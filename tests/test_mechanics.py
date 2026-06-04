import token

from application import create_app
from application.models import db
import unittest

class TestMechanics(unittest.TestCase):
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

    def test_login_mechanic(self):
        # 1. Create mechanic
        create = self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "email": "carlos.ramirez@test.com",
            "phone": "3125550405",
            "salary": 61000,
            "password": "password123"
        })

        self.assertEqual(create.status_code, 201)

        # 2. Login
        login = self.client.post('/mechanics/login', json={
            "email": "carlos.ramirez@test.com",
            "password": "password123"
        })

        # 3. Assertions
        self.assertEqual(login.status_code, 200)

        data = login.get_json()
        self.assertIn("auth_token", data)


    def test_create_mechanic(self):
        response = self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "email": "carlos.ramirez@test.com",
            "phone": "3125550405",
            "salary": 61000,
            "password": "password123"
            })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "Carlos Ramirez")

    def test_get_mechanic(self):
        # First, create a mechanic
        self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "email": "carlos.ramirez@test.com",
            "phone": "3125550405",
            "salary": 61000,
            "password": "password123"

        })

        response = self.client.get('/mechanics/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Carlos Ramirez")

    def test_get_mechanics(self):
        # First, create a mechanic
        self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "phone": "3125550405",
            "email": "carlos.ramirez@test.com",
            "salary": 61000,
            "password": "password123"
        })

        self.client.post('/mechanics/', json={
            "name": "Mike Johnson",
            "phone": "3125550401",
            "email": "mike.johnson@test.com",
            "salary": 55000,
            "password": "password123",
        })

        response = self.client.get('/mechanics/')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIsInstance(data, list)

        self.assertEqual(len(data), 2)
        names = [mechanic['name'] for mechanic in data]
        self.assertIn("Carlos Ramirez", names)
        self.assertIn("Mike Johnson", names)

    def test_update_mechanic(self):
        # First, create a mechanic
        self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "phone": "3125550305",
            "email": "carlos.ramirez@test.com",
            "salary": 61000,
            "password": "password123"
        })

        login = self.client.post('/mechanics/login', json={
            "email": "carlos.ramirez@test.com",
            "password": "password123"
        })

        token = login.json['auth_token']

        # Then, update the mechanic
        response = self.client.put(f'/mechanics/', json={
            "name": "Carlos Ramirez Updated",
            "email": "carlos.ramirez.updated@test.com",
        }, headers={"Authorization": f"Bearer {token}"})


        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Carlos Ramirez Updated")
        self.assertEqual(response.json['email'], "carlos.ramirez.updated@test.com")

    def test_delete_mechanic(self):
        # First, create a mechanic
        self.client.post('/mechanics/', json={
            "name": "Carlos Ramirez",
            "phone": "3125550305",
            "email": "carlos.ramirez@test.com",
            "salary": 61000,
            "password": "password123"
        })
        
        login = self.client.post('/mechanics/login', json={
            "email": "carlos.ramirez@test.com",
            "password": "password123"
        })

        token = login.json['auth_token']

        response = self.client.delete(f'/mechanics/', headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "Mechanic deleted")
