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
    """Put intial customer value in a dictionary, key is the customer id"""
    cart_id_cuurent = cart_id_count[0]
    cart[cart_id_cuurent] = {"customer_name": new_cart.customer, "red_potion_number" : 0, "green_potion_number" : 0, "blue_potion_number" : 0, "gold_cost" : 0, "checkout" : False}
    cart_id_count[0] = cart_id_cuurent + 1

    return {"cart_id": cart_id_cuurent}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """Returns the given customer info for a specific id"""
    return {"customer_id" : cart_id, "customer_name" : cart[cart_id]["customer_name"], "red_potion_number": cart[cart_id]["red_potion_number"], "green_potion_number": cart[cart_id]["green_potion_number"], "blue_potion_number": cart[cart_id]["blue_potion_number"],"gold_cost": cart[cart_id]["gold_cost"]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """See the number of red postions available"""

    if (item_sku == "RED_POTION_0"):
        cart[cart_id]["red_potion_number"] += cart_item.quantity
        cart[cart_id]["gold_cost"] += cart_item.quantity * 1
        return "OK"
    elif (item_sku == "GREEN_POTION_0"):
        cart[cart_id]["green_potion_number"] += cart_item.quantity
        cart[cart_id]["gold_cost"] += cart_item.quantity * 1
        return "OK"
    elif (item_sku == "BLUE_POTION_0"):    
        cart[cart_id]["blue_potion_number"] += cart_item.quantity
        cart[cart_id]["gold_cost"] += cart_item.quantity * 1
        return "OK"
    else:
        return "No such item available"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    if (cart_id > len(cart) or cart_id <= 0):
        return "Customer doesn't exist"
    if (cart[cart_id]["checkout"]):
        return "Already checked out"

    with db.engine.begin() as connection:
        red_potions_available = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory;")).first().num_red_potions 
        green_potions_available = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;")).first().num_green_potions 
        blue_potions_available = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory;")).first().num_blue_potions 

    customer_red_positions = cart[cart_id]["red_potion_number"]
    customer_green_positions = cart[cart_id]["green_potion_number"]
    customer_blue_positions = cart[cart_id]["blue_potion_number"]
    customer_gold = cart[cart_id]["gold_cost"]

    if(customer_red_positions > red_potions_available or customer_green_positions > green_potions_available or customer_blue_positions > blue_potions_available):
        return "Not enough potions available"

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions - {customer_red_positions};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions - {customer_green_positions};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions - {customer_blue_positions};"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {customer_gold};" ))

    cart[cart_id]["checkout"] = True
    return {"total_potions_bought": (customer_red_positions + customer_green_positions + customer_blue_positions), "total_gold_paid": customer_gold}
