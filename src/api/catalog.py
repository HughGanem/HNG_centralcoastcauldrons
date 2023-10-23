import sqlalchemy
from src import database as db
from fastapi import APIRouter


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions;")).all()

    return_lst = []
    count = 0
    for potion in potions:
        if count >= 20:
            break
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

        #TODO: Removed extra "," at the end of the potion_type
        if (quantity != 0):
            return_lst.append(
                {
                    "sku": potion.sku,
                    "name": potion.name,
                    "quantity": quantity,
                    "price": potion.price,
                    "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]
                }
        )
        count += 1
    if (len(return_lst) == 0):
        return []
    return return_lst