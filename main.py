from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="Example API",
    description="Une API d'exemple pour démontrer le CI/CD",
    version="1.0.0"
)

# Modèles de données
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    in_stock: bool = True

class HealthResponse(BaseModel):
    status: str
    version: str

# Base de données en mémoire (simulation)
items_db: List[Item] = [
    Item(id=1, name="Laptop", description="Un ordinateur portable", price=999.99, in_stock=True),
    Item(id=2, name="Mouse", description="Une souris sans fil", price=29.99, in_stock=True),
    Item(id=3, name="Keyboard", description="Un clavier mécanique", price=149.99, in_stock=False),
]

@app.get("/", tags=["Root"])
async def root():
    """Endpoint racine"""
    return {
        "message": "Bienvenue sur l'API d'exemple! v5.7",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Vérification de l'état de santé de l'API"""
    return HealthResponse(status="healthy", version="1.0.0")

@app.get("/items", response_model=List[Item], tags=["Items"])
async def get_items(in_stock: Optional[bool] = None):
    """Récupérer tous les items"""
    if in_stock is None:
        return items_db
    return [item for item in items_db if item.in_stock == in_stock]

@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item(item_id: int):
    """Récupérer un item par son ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item non trouvé")

@app.post("/items", response_model=Item, status_code=201, tags=["Items"])
async def create_item(item: Item):
    """Créer un nouvel item"""
    # Générer un nouvel ID
    new_id = max([i.id for i in items_db if i.id]) + 1 if items_db else 1
    item.id = new_id
    items_db.append(item)
    return item

@app.put("/items/{item_id}", response_model=Item, tags=["Items"])
async def update_item(item_id: int, updated_item: Item):
    """Mettre à jour un item existant"""
    for idx, item in enumerate(items_db):
        if item.id == item_id:
            updated_item.id = item_id
            items_db[idx] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item non trouvé")

@app.delete("/items/{item_id}", tags=["Items"])
async def delete_item(item_id: int):
    """Supprimer un item"""
    for idx, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(idx)
            return {"message": f"Item {item_id} supprimé avec succès"}
    raise HTTPException(status_code=404, detail="Item non trouvé")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
