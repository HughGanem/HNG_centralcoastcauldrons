import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

cart = {}
cart_id_count = [1]

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    cart_id_cuurent = cart_id_count[0]

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO carts (cart_id, customer_name)
            VALUES (:cart_id_current, :customer_name);
            """),
            [{"cart_id_current" : cart_id_cuurent, "customer_name" : new_cart.customer}])
        
    cart_id_count[0] = cart_id_cuurent + 1

    return {"cart_id": cart_id_cuurent}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            """
            SELECT cart_id, customer_name, total_cost, total_potion_num FROM carts WHERE cart_id = :cart_id;
            """),
            [{"cart_id" : cart_id}]).first()
    return [{"cart_id" : cart_id, "customer_name" : result.customer_name, "total_cost" : result.total_cost, "total_potion_num" : result.total_potion_num}]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        #Add items to cart
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO cart_items (cart_id, potion_id, quantity)
            SELECT :cart_id, potions.potion_id, :quantity
            FROM potions 
            WHERE potions.sku = :item_sku and :quantity <= potions.quantity;
            """),
            [{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])
    
    with db.engine.begin() as connection:
        #Update overall cart
        connection.execute(sqlalchemy.text(
            """
            UPDATE carts
            SET total_potion_num = total_potion_num + :quantity,total_cost = total_cost + (potions.price * :quantity)
            FROM potions
            WHERE potions.sku = :item_sku and cart_id = :cart_id and :quantity <= potions.quantity;
            """),
            [{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    #lower postion amount 
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            UPDATE potions
            SET quantity = potions.quantity - cart_items.quantity
            FROM cart_items
            WHERE potions.potion_id = cart_items.potion_id and cart_items.cart_id = :cart_id;
            """), 
            [{"cart_id" : cart_id}]
            )
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            UPDATE global_inventory
            SET gold = gold + carts.total_cost
            FROM carts
            WHERE carts.cart_id = :cart_id;
            """),
            [{"cart_id" : cart_id}]
            )
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            DELETE FROM cart_items
            WHERE cart_id = :cart_id
            """),
            [{"cart_id" : cart_id}]
        )
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            DELETE FROM carts
            WHERE cart_id = :cart_id
            """),
            [{"cart_id" : cart_id}]
        )

    return "OK"