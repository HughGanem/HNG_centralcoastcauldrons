import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            DELETE FROM cart_items;
            DELETE FROM carts;
            DELETE FROM ml_ledger;
            DELETE FROM potion_ledger;
            DELETE FROM transaction;
            """
        ))
    with db.engine.begin() as connection:
            transaction_id = connection.execute(sqlalchemy.text(
                """
                INSERT INTO transaction (description) 
                VALUES ('Reset shop! Set gold to 100, got rid of potions, carts and ml')
                RETURNING transaction_id;
                """)).scalar_one()

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO ml_ledger (transaction_id, gold, red_ml, green_ml, blue_ml, dark_ml) 
            VALUES (:transaction_id, 100, 0, 0, 0, 0);
            """
        ),
        [{"transaction_id": transaction_id}])
    

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    return {
        "shop_name": "Hugh's Hoppin' Potions",
        "shop_owner": "Hugh",
    }

