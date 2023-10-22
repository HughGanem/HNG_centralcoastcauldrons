import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        potion_result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(quantity) AS potion_quantity,
            SUM(gold) AS gold_cost
            FROM potion_ledger;
            """
        )).first()
    potion_amount = potion_result.potion_quantity
    potion_gold = potion_result.gold_cost
    
    with db.engine.begin() as connection:
        ml_result = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_ml + green_ml + blue_ml + dark_ml) AS total_ml,
            SUM(gold) AS gold_cost
            FROM ml_ledger;
            """
        )).first()
    ml_amount = ml_result.total_ml
    ml_gold = ml_result.gold_cost

    
    if (potion_amount is None):
        potion_amount = 0
    
    if (potion_gold is None):
        potion_gold = 0

    if (ml_amount is None):
        ml_amount = 0
    
    if (ml_gold is None):
        ml_gold = 0
    

    return {"number_of_potions": potion_amount, "ml_in_barrels": ml_amount, "gold": potion_gold + ml_gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
