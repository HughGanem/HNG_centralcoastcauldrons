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
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions WHERE quantity != 0;")).all()

    return_lst = []
    count = 0
    for potion in potions:
        if count >= 20:
            break

        return_lst.append(
            {
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": potion.potion_type,
            }
        )
        count += 1
    return return_lst