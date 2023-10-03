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
    cart[cart_id_cuurent] = {"customer_name": new_cart.customer, "potion_number" : 0, "gold_cost" : 0}
    cart_id_count[0] = cart_id_cuurent + 1

    return {"cart_id": cart_id_cuurent}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """Returns the given customer info for a specific id"""
    return {"customer_id" : cart_id,"customer_name" : cart[cart_id]["customer_name"], "potion_number": cart[cart_id]["potion_number"], "gold_cost": cart[cart_id]["gold_cost"]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """See the number of red postions available"""
    if (item_sku == "RED_POTION_0"):
        Get_Red_Postions_SQL = "SELECT num_red_potions FROM global_inventory;"
    else:
        return "No such item available"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(Get_Red_Postions_SQL))
        number_red_potions = result.first().num_red_potions
    

    if (number_red_potions >= cart_item.quantity):
        cart[cart_id]["potion_number"] += cart_item.quantity
        cart[cart_id]["gold_cost"] += cart_item.quantity * 50

        return "OK"
    else:
        return "Not enough potions available"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    get_red_potions_SQL = "SELECT num_red_potions FROM global_inventory;"

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(get_red_potions_SQL))
        red_potions_available = result.first().num_red_potions

    customer_red_positions = cart[cart_id]["potion_number"]
    customer_gold = cart[cart_id]["gold_cost"]

    if (customer_red_positions <= red_potions_available):

        update_red_potions = "UPDATE global_inventory SET num_red_potions = num_red_potions - " + str(customer_red_positions) + ";"
        update_gold = "UPDATE global_inventory SET gold = gold + " + str(customer_gold) + ";" 

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(update_red_potions))
            connection.execute(sqlalchemy.text(update_gold))

        return {"total_potions_bought": customer_red_positions, "total_gold_paid": customer_gold}
    else:
        return "Not enough potions available"