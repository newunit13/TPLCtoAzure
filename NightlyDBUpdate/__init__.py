import datetime
import logging
import pandas as pd
import azure.functions as func

from utils import TPLC, sql
from copy import deepcopy


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    raw_data = TPLC.get_inventory()


    clean_data = []
    for d in raw_data:
        datum = deepcopy(d)
        datum['customerIdentifier'] = datum.get('customerIdentifier').get('name')
        datum['facilityIdentifier'] = datum.get('facilityIdentifier').get('name')
        datum['itemIdentifier'] = datum.get('itemIdentifier').get('sku')
        datum['inventoryUnitOfMeasureIdentifier'] = datum.get('inventoryUnitOfMeasureIdentifier').get('name')

        if datum.get('locationIdentifier'):
            datum['locationIdentifier']  = datum.get('locationIdentifier').get('nameKey').get('name')
        else:
            datum['locationIdentifier'] = None

        if datum.get('palletIdentifier') :
            datum['palletIdentifier'] = datum.get('palletIdentifier').get('nameKey').get('name')
        else:
            datum['palletIdentifier'] = None
        
        clean_data.append(datum)


    df = pd.DataFrame(clean_data)
    

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
