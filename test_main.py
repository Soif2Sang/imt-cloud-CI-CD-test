import pytest
from fastapi.testclient import TestClient
from main import app, items_db, Item

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """Reset la base de données avant chaque test"""
    items_db.clear()
    items_db.extend([
        Item(id=1, name="Laptop", description="Un ordinateur portable", price=999.99, in_stock=True),
        Item(id=2, name="Mouse", description="Une souris sans fil", price=29.99, in_stock=True),
        Item(id=3, name="Keyboard", description="Un clavier mécanique", price=149.99, in_stock=False),
    ])


class TestRoot:
    """Tests pour l'endpoint racine"""
    
    def test_read_root(self):
        """Test de l'endpoint racine renvoie du HTML avec fond bleu"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "background-color: blue;" in response.text
        assert "<h1>Bienvenue sur l'API d'exemple!</h1>" in response.text


class TestHealth:
    """Tests pour l'endpoint de santé"""
    
    def test_health_check(self):
        """Test du health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestGetItems:
    """Tests pour récupérer les items"""
    
    def test_get_all_items(self):
        """Test pour récupérer tous les items"""
        response = client.get("/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Laptop"
    
    def test_get_items_in_stock(self):
        """Test pour récupérer seulement les items en stock"""
        response = client.get("/items?in_stock=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["in_stock"] for item in data)
    
    def test_get_items_out_of_stock(self):
        """Test pour récupérer les items hors stock"""
        response = client.get("/items?in_stock=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Keyboard"


class TestGetItem:
    """Tests pour récupérer un item spécifique"""
    
    def test_get_existing_item(self):
        """Test pour récupérer un item existant"""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Laptop"
        assert data["price"] == pytest.approx(999.99)
    
    def test_get_non_existing_item(self):
        """Test pour récupérer un item qui n'existe pas"""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Item non trouvé"


class TestCreateItem:
    """Tests pour créer un item"""
    
    def test_create_item_success(self):
        """Test de création d'un item avec succès"""
        new_item = {
            "name": "Monitor",
            "description": "Un écran 4K",
            "price": 399.99,
            "in_stock": True
        }
        response = client.post("/items", json=new_item)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 4
        assert data["name"] == "Monitor"
        assert data["price"] == pytest.approx(399.99)
    
    def test_create_item_minimal(self):
        """Test de création d'un item avec données minimales"""
        new_item = {
            "name": "Webcam",
            "price": 79.99
        }
        response = client.post("/items", json=new_item)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Webcam"
        assert data["in_stock"] is True  # Valeur par défaut
    
    def test_create_item_invalid_data(self):
        """Test de création avec données invalides"""
        invalid_item = {
            "name": "Invalid",
            # price manquant (requis)
        }
        response = client.post("/items", json=invalid_item)
        assert response.status_code == 422  # Unprocessable Entity


class TestUpdateItem:
    """Tests pour mettre à jour un item"""
    
    def test_update_existing_item(self):
        """Test de mise à jour d'un item existant"""
        updated_data = {
            "name": "Gaming Laptop",
            "description": "Un laptop de gaming puissant",
            "price": 1499.99,
            "in_stock": True
        }
        response = client.put("/items/1", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Gaming Laptop"
        assert data["price"] == pytest.approx(1499.99)
    
    def test_update_non_existing_item(self):
        """Test de mise à jour d'un item qui n'existe pas"""
        updated_data = {
            "name": "Ghost Item",
            "price": 99.99
        }
        response = client.put("/items/999", json=updated_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Item non trouvé"


class TestDeleteItem:
    """Tests pour supprimer un item"""
    
    def test_delete_existing_item(self):
        """Test de suppression d'un item existant"""
        response = client.delete("/items/2")
        assert response.status_code == 200
        assert "supprimé avec succès" in response.json()["message"]
        
        # Vérifier que l'item est vraiment supprimé
        get_response = client.get("/items/2")
        assert get_response.status_code == 404
    
    def test_delete_non_existing_item(self):
        """Test de suppression d'un item qui n'existe pas"""
        response = client.delete("/items/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Item non trouvé"


class TestIntegration:
    """Tests d'intégration end-to-end"""
    
    def test_full_crud_workflow(self):
        """Test du workflow CRUD complet"""
        # 1. Créer un nouvel item
        new_item = {
            "name": "Headphones",
            "description": "Casque sans fil",
            "price": 199.99,
            "in_stock": True
        }
        create_response = client.post("/items", json=new_item)
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]
        
        # 2. Lire l'item créé
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Headphones"
        
        # 3. Mettre à jour l'item
        update_data = {
            "name": "Premium Headphones",
            "description": "Casque haut de gamme",
            "price": 299.99,
            "in_stock": False
        }
        update_response = client.put(f"/items/{item_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["price"] == pytest.approx(299.99)
        
        # 4. Supprimer l'item
        delete_response = client.delete(f"/items/{item_id}")
        assert delete_response.status_code == 200
        
        # 5. Vérifier que l'item n'existe plus
        final_get = client.get(f"/items/{item_id}")
        assert final_get.status_code == 404