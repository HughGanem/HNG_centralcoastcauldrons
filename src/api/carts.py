import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):

    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(
            """
            INSERT INTO carts (customer_name)
            VALUES (:customer_name)
            RETURNING cart_id
            """),
            [{"customer_name" : new_cart.customer}]).first().cart_id
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    with db.engine.begin() as connection:
        cust_name = connection.execute(sqlalchemy.text(
            """
            SELECT customer_name
            FROM carts
            WHERE carts.cart_id = :cart_id;
            """),
            [{"cart_id" : cart_id}]).first().customer_name
        
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
        """
        SELECT 
        SUM(cart_items.quantity * potions.price) AS gold_cost,
        SUM(cart_items.quantity) AS total_quantity
        FROM cart_items
        JOIN potions
        ON potions.potion_id = cart_items.potion_id
        WHERE cart_items.cart_id = :cart_id;
        """
        ),
        [{"cart_id" : cart_id}]).first()
    
    quantity = result.total_quantity
    if (quantity is None):
        quantity = 0
    gold = result.gold_cost
    if (gold is None):
        gold = 0
    
    return [{"cart_id" : cart_id, "customer_name" : cust_name, "quantity" : quantity, "gold_cost" : gold}]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(potion_ledger.quantity) AS potion_quantity
            FROM potion_ledger
            JOIN potions 
            ON potion_ledger.potion_id = potions.potion_id and potions.sku = :item_sku;
            """
            ),
            [{"item_sku" : item_sku}]).first()
        
        quantity = result.potion_quantity
        if (quantity is None):
            print("No potions")
            return "OK"

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO cart_items (cart_id, potion_id, quantity)
            SELECT :cart_id, potion_ledger.potion_id, :quantity
            FROM potion_ledger, potions 
            WHERE :quantity <= :potion_quantity and potions.sku = :item_sku;
            """),
            [{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity, "potion_quantity" : quantity}])

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    #get items 
    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text(
            """
            SELECT *
            FROM cart_items 
            WHERE cart_id = :cart_id;
            """),
            [{"cart_id" : cart_id}])
        
    for item in cart_items:
        with db.engine.begin() as connection:
            potion = connection.execute(sqlalchemy.text(
            """
            SELECT *
            FROM potions
            WHERE potion_id = :potion_id;
            """),
            [{"potion_id" : item.potion_id}]).first()

            transaction_id = connection.execute(sqlalchemy.text(
            """
            INSERT INTO transaction (description) 
            VALUES ('Potions brought! Customer :cust_id brought :num_potions potions that are :potion_type costing :gold_cost.')
            RETURNING transaction_id;
            """),
            [{"cust_id" : cart_id, "num_potions" : item.quantity, "potion_type" : item.potion_id, "gold_cost" : potion.price * item.quantity}]
            ).scalar_one()

            connection.execute(sqlalchemy.text(
            """
            INSERT INTO gold_ledger (gold, transaction_id)
            VALUES (:gold, :transaction_id)
            """),
            [{"gold" : item.quantity * potion.price, "transaction_id" : transaction_id}])

            connection.execute(sqlalchemy.text(
            """
            INSERT INTO potion_ledger (transaction_id, potion_id, quantity)
            VALUES (:transaction_id, :potion_id, :quantity)
            """),
            [{"transaction_id" : transaction_id, "potion_id" : item.potion_id, "quantity" : -item.quantity}])

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            DELETE FROM cart_items
            WHERE cart_id = :cart_id
            """),
            [{"cart_id" : cart_id}]
        )
        connection.execute(sqlalchemy.text(
            """
            DELETE FROM carts
            WHERE cart_id = :cart_id
            """),
            [{"cart_id" : cart_id}]
        )

    return "OK"