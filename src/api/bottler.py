import sqlalchemy
import random
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    if (len(potions_delivered) == 0):
        return "No potions made!"

    for potion in potions_delivered:
        if (potion.quantity == 0):
            continue
        red_ml = potion.potion_type[0]
        green_ml = potion.potion_type[1]
        blue_ml = potion.potion_type[2]
        dark_ml = potion.potion_type[3]

        with db.engine.begin() as connection:
            transaction_id = connection.execute(sqlalchemy.text(
                """
                INSERT INTO transaction (description) 
                VALUES ('Created potions! Made :quantity potions that are [:red_ml, :blue_ml, :green_ml, :dark_ml] type.')
                RETURNING transaction_id;
                """),
                [{"quantity": potion.quantity, "potion_type": potion.potion_type,
                  "red_ml" : red_ml, "green_ml" : green_ml, "blue_ml" : blue_ml, "dark_ml" : dark_ml}]
                ).scalar_one()

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO ml_ledger (transaction_id, red_ml, green_ml, blue_ml, dark_ml) 
                VALUES (:transaction_id, :red_ml, :green_ml, :blue_ml, :dark_ml);
                """
            ),
            [{"transaction_id": transaction_id, "red_ml" : -red_ml * potion.quantity, "green_ml" : -green_ml * potion.quantity, "blue_ml" : -blue_ml * potion.quantity, "dark_ml" : -dark_ml * potion.quantity}]
            )
        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger (transaction_id, potion_id, quantity)
                    SELECT :transaction_id, potions.potion_id, :quantity
                    FROM potions
                    WHERE potions.red_ml = :red_ml and potions.green_ml = :green_ml and potions.blue_ml = :blue_ml and potions.dark_ml = :dark_ml;
                    """),
                    [{"transaction_id": transaction_id, "quantity" : potion.quantity, "red_ml" : red_ml, "green_ml" : green_ml, "blue_ml" : blue_ml, "dark_ml" : dark_ml}])
    
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
        """SELECT
        SUM(red_ml) AS num_red_ml,
        SUM(green_ml) AS num_green_ml,
        SUM(blue_ml) AS num_blue_ml,
        SUM(dark_ml) AS num_dark_ml
        FROM ml_ledger;"""
        )).first()
    red_ml = result.num_red_ml
    green_ml = result.num_green_ml
    blue_ml = result.num_blue_ml
    dark_ml = result.num_dark_ml

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text(
            """SELECT * 
            FROM potions 
            ORDER BY potion_id DESC;
            """)).all()

    return_lst = []
    for potion in potions:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text(
            """
            SELECT SUM(quantity) AS potion_quantity
            FROM potion_ledger
            WHERE potion_ledger.potion_id = :potion_id;
            """
            ),
            [{"potion_id" : potion.potion_id}]).first()
        
        quantity = result.potion_quantity
        if (quantity is None):
            quantity = 0

        added_potion = False

        quantity_made = 0
        if (quantity <= 4):
            while (red_ml >= potion.red_ml and green_ml >= potion.green_ml and blue_ml >= potion.blue_ml and dark_ml >= potion.dark_ml and (quantity + quantity_made) <= 4):
                red_ml -= potion.red_ml
                green_ml -= potion.green_ml
                blue_ml -= potion.blue_ml
                dark_ml -= potion.dark_ml
                quantity_made += 1
                added_potion = True
            
            if (added_potion):
                return_lst.append(
                    {
                        "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                        "quantity": quantity_made
                    }
                )
    
    if (len(return_lst) == 0):
        return ()
    return return_lst