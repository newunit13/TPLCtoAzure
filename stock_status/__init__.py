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

    logging.info('Getting Inventory Data from TPLC')
    raw_data = TPLC.get_inventory()

    logging.info('Cleaning Inventory Data')
    clean_data = []
    for d in raw_data:
        datum = deepcopy(d)
        datum['customerIdentifier'] = datum.get('customerIdentifier').get('name')
        datum['facilityIdentifier'] = datum.get('facilityIdentifier').get('name')
        datum['itemIdentifier'] = datum.get('itemIdentifier').get('sku')
        datum['inventoryUnitOfMeasureIdentifier'] = datum.get('inventoryUnitOfMeasureIdentifier').get('name')
        datum['timestamp'] = utc_timestamp

        datum['locationIdentifier'] = datum.get('locationIdentifier').get('nameKey').get('name') if datum.get('locationIdentifier') else None
        datum['palletIdentifier'] = datum.get('palletIdentifier').get('nameKey').get('name') if datum.get('palletIdentifier') else None
        datum['onHoldUserIdentifier']  = datum.get('onHoldUserIdentifier').get('name') if datum.get('onHoldUserIdentifier') else None

        clean_data.append(datum)


    logging.info('Inserting Inventory Data')
    df = pd.DataFrame(clean_data)
    df.drop(['_links'], axis=1, inplace=True)
    df.drop(['savedElements'], axis=1, inplace=True)
    df.drop(['secondaryUnitOfMeasureIdentifier'], axis=1, inplace=True)
    df.to_sql('Stock_Status', sql.engine, if_exists='append', index=False, chunksize=100, method=None)
    

    logging.info('stock_status timer function ran at %s', utc_timestamp)
