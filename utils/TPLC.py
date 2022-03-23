import base64
import requests
import json
import re
from urllib.parse import urlencode
from .config import TPL_ID, TPL_SECRET, TPL_GUID, TPL_USERID



#----------------------------------------------------------------------------------------------
def billboard():
    url = "https://secure-wms.com/billboard"
    response = requests.get(url=url)
    top_level = response.json()

    billboard = {'root': "https://secure-wms.com", 'billboard': 'https://secure-wms.com/billboard'}
    for level in top_level.get("_links"):
        service = level["Rel"].split("/")[-1]
        href = level["Href"][1:]
        
        url = billboard["billboard"] + href
        response = requests.get(url=url)
        data = response.json()

        items = {'root': data.get("RootUri")}
        for link in data.get("_links"):
            item = link["Rel"].split("/")[-1]
            matches = re.match(r'(.*){\?(.*)}', link["Href"])
            if matches:
                endpoint = matches[1]
                options = matches[2].split(',')
            else:
                endpoint = link["Href"]
                options = None

            items[item] = {'url': billboard.get("root") + endpoint, 'endpoint': endpoint, 'options': options}

        billboard[service] = items

    return billboard

def get_access_token(tpl_id, tpl_secret, tpl_guid, tpl_user_id):

    secret_key = f'{tpl_id}:{tpl_secret}'.encode('utf-8')
    secret_key = base64.b64encode(secret_key).decode('utf-8')

    url = "https://secure-wms.com/AuthServer/api/Token"

    headers = {
        "Authorization": f"Basic {secret_key}",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }

    data = json.dumps({
        "grant_type" : "client_credentials",
        "tpl" : f"{tpl_guid}",
        "user_login_id" : f"{tpl_user_id}"
    })

    response = requests.post(url=url, headers=headers, data=data)
    print(f"GetAccessToken() called.\tStatus Code: {response.status_code}")

    return response.json()["access_token"]

def get_receipts(detail="All",rql=""):
    options = {
        "detail": detail,
        "rql": rql
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f'{base_url}/inventory/receivers?{options}'
    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()
    receipts = data["_embedded"]["http://api.3plCentral.com/rels/inventory/receiver"] if data.get("_embedded") else []
    while data.get("_links").get("next"):

        url = f'{base_url}{data.get("_links").get("next").get("href")}'
        response = requests.get(url=url, headers=headers)
        data = response.json()
        receipts += data["_embedded"]["http://api.3plCentral.com/rels/inventory/receiver"]

    receipts = {r["readOnly"]["receiverId"]:r for r in receipts}
    return receipts

def get_stock_status(customer_id):
    base_url = "https://secure-wms.com"
    url = f"{base_url}/inventory/stockdetails?customerid={customer_id}&facilityid=2&pgsiz=100"
    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    } 

    response = requests.get(url=url, headers=headers)

    while True:
        data_dict = response.json()
        if data_dict.get("_embedded"):
            inventory = {item["receiveItemId"]:item for item in data_dict["_embedded"]["item"]}

        next_page = data_dict["_links"].get("next").get("href") if data_dict["_links"].get("next") else None
        if next_page:
            response = requests.get(url=f"{base_url}{next_page}", headers=headers)
        else:
            break
         
    return inventory

def get_inventory(pgsiz=100, pgnum=1, rql="", sort="", senameorvaluecontains="" ):
    options = {
        "pgsiz": pgsiz,
        "pgnum": pgnum,
        "rql": rql,
        "sort": sort,
        "senameorvaluecontains": senameorvaluecontains
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/inventory?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()

    total_results = data["totalResults"]
    current_progress = 0
    items = []

    while True:

        print(f'Gathering page {pgnum}.\t{current_progress} out of {total_results} [{current_progress/total_results:2.2%}]')

        response = requests.get(url=url, headers=headers)
        
        if response.status_code != 200:
            raise Exception

        data = response.json()
        items += data['_embedded']['item']

        current_progress += pgsiz
        pgnum += 1
    
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break

    return items

# TODO: finish writing this function 
def get_location_info(id=2, pgsiz=100, pgnum=1, rql="", sort="", excludeInAudit=False ):
    options = {
        "pgsiz": pgsiz,
        "pgnum": pgnum,
        "rql": rql,
        "sort": sort,
        "excludeInAudit": excludeInAudit
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/inventory/facilities/{id}/locations?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()

    total_results = data["totalResults"]
    current_progress = 0
    items = []

    return items

def get_items(customer_id, pgsiz=100, pgnum=1, rql="", sort=""):
    options = {
        "pgsiz": pgsiz,
        "pgnum": pgnum,
        "rql": rql,
        "sort": sort,
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/customers/{customer_id}/items?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()

    total_results = data["totalResults"]
    current_progress = 0
    items = []

    while True:

        print(f'Gathering page {pgnum}.\t{current_progress} out of {total_results} [{current_progress/total_results:2.2%}]')

        response = requests.get(url=url, headers=headers)
        
        if response.status_code != 200:
            raise Exception

        data = response.json()
        items += data['_embedded']['http://api.3plCentral.com/rels/customers/item']

        current_progress += pgsiz
        pgnum += 1
    
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break

    return items

def get_item(customer_id, item_id):
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/customers/{customer_id}/items/{item_id}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        raise Exception

    item = response.json()

    return (item, response.headers["ETag"])

def update_item(customer_id, item_id, etag, payload):
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/customers/{customer_id}/items/{item_id}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}",
        "If-Match"          : f"{etag}"
    }

    try:
        del payload["_links"]
        del payload["_embedded"]
    except:
        pass

    response = requests.put(url=url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        raise Exception


    return True

def get_customers(pgsiz=100, pgnum=1, rql="", sort="", facilityId=""):
    options = {
        "pgsiz": pgsiz,
        "pgnum": pgnum,
        "rql": rql,
        "sort": sort,
        "facilityId": facilityId
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/customers?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()

    total_results = data["totalResults"]
    current_progress = 0
    customers = []

    while True:

        print(f'Gathering page {pgnum}.\t{current_progress} out of {total_results} [{current_progress/total_results:2.2%}]')

        response = requests.get(url=url, headers=headers)
        
        if response.status_code != 200:
            raise Exception

        data = response.json()
        customers += data['_embedded']['http://api.3plCentral.com/rels/customers/customer']

        current_progress += pgsiz
        pgnum += 1
    
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break

    return customers

def get_locations(pgsiz=100, pgnum=1, rql="", sort="", beginlocationid="", endlocationid=""):
    options = {
        "pgsiz": pgsiz,
        "pgnum": pgnum,
        "rql": rql,
        "sort": sort,
        "beginlocationid": beginlocationid,
        "endlocationid": endlocationid
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/properties/facilities/locations?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }


    current_progress = 0
    locations = []

    while True:

        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            raise Exception

        data = response.json()
        total_results = data["totalResults"]
        locations += data['_embedded']['http://api.3plCentral.com/rels/properties/location']

        print(f'Gathering page {pgnum}.\t{current_progress} out of {total_results} [{current_progress/total_results:2.2%}]')

        current_progress += pgsiz
        pgnum += 1
    
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break

    return locations

def get_orders(pgsiz: int=100,pgnum: int=1,rql: str="",sort: str="",detail: str="",itemdetail: str="") -> dict:
    """Get a list of orders from the 3plCentral API.

    Keyword arguments:
    pgsiz       -- The number of results to return per page
    pgnum       -- The page number to return
    rql         -- A query string to filter the results
    sort        -- A string to sort the results by
    detail      -- A string to return the detail level of the results
    itemdetail  -- A string to return the detail level of the items
    """
    options = {
        "pgsiz"     : pgsiz,
        "pgnum"     : pgnum,
        "rql"       : rql,
        "sort"      : sort,
        "detail"    : detail,
        "itemdetail": itemdetail
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/orders?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    orders = []
    while True:
        response = requests.get(url=url, headers=headers)
        data = response.json()
        orders += data["_embedded"]["http://api.3plCentral.com/rels/orders/order"]
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break


    orders = {o["readOnly"]["orderId"]:o for o in orders}
    return orders

def get_order_summary(pgsiz=100,pgnum=1,rql="",sort="",orderidcontains="",receiverid=""):
    options = {
        "pgsiz"     : pgsiz,
        "pgnum"     : pgnum,
        "rql"       : rql,
        "sort"      : sort,
        "orderidcontains"    : orderidcontains,
        "receiverid": receiverid
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/orders/summaries?{options}"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    orders = []
    while True:
        response = requests.get(url=url, headers=headers)
        data = response.json()
        orders += data["_embedded"]["http://api.3plCentral.com/rels/orders/order"]
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break


    orders = {o["readOnly"]["orderId"]:o for o in orders}
    return orders

def get_package():
    pass

def get_purcharse_orders(pgsiz="1000", rql=""):
    options = {
        "pgsiz": pgsiz,
        "rql": rql
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)
    base_url = f"https://secure-wms.com"
    url = f"{base_url}/inventory/pos?{options}"
    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }


    purchase_orders = []
    while True:
        response = requests.get(url=url, headers=headers)
        data = response.json()
        purchase_orders += data["_embedded"]["http://api.3plCentral.com/rels/inventory/purchaseorder"]
        if data.get("_links").get("next"):
            url = f'{base_url}{data.get("_links").get("next").get("href")}'
        else:
            break

    purchase_orders = {po["purchaseOrderNumber"]: po for po in purchase_orders}

    return purchase_orders

def get_pucharse_order(id=""):

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/inventory/pos/{id}"
    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    data = response.json()

    return data

def get_base_reports():

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/reportdefs/ssrs/names"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    response = requests.get(url=url, headers=headers)
    reports = response.json()

    return reports

def run_custom_report(base_report_name, custom_report_name, for_customer="", customerid="",  parameters=""):
    print(f"Custom report {custom_report_name} ran with parameters: {parameters}")

    if for_customer == "":
        for_customer = "TplOnly"

    options = {
        "parameters": parameters,
        "customerid": customerid
    }
    options = {k:v for k,v in options.items() if v}
    options = urlencode(options)

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/reportdefs/ssrs/{base_report_name}/{for_customer}/{custom_report_name}/runner?{options}"
    #/reportdefs/ssrs/{name}/{for}/{customname}/runner{?parameters,customerid}
    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "text/csv",
        "Accept"            : "text/csv;header=absent;separator=comma;excelmode=false",
        "Authorization"     : f"Bearer {access_token}"
    }
    
    response = requests.get(url=url, headers=headers)
    data = response.text
    data = data[3:len(data)-2]

    return data

def create_order():

    base_url = f"https://secure-wms.com"
    url = f"{base_url}/orders"

    headers = {
        "Host"              : "secure-wms.com",
        "Content-Type"      : "application/hal+json; charset=utf-8",
        "Accept"            : "application/hal+json",
        "Authorization"     : f"Bearer {access_token}"
    }

    data = {
        "customerIdentifier": {
            "id": "1077"
        },
        "facilityIdentifier": {
            "id": "2"
        },
        "referenceNum": "3150",
        "billingCode": "Prepaid",
        "routingInfo": {
            "carrier": "UPS",
            "mode": "92",
        },
        "shipTo": {
            "name":"Test Company",
            "address1":"1207 Washington Ave 2",
            "city":"Golden",
            "state":"CO",
            "zip":"80401",
            "country":"US"
        },
        "orderItems": [
            {
                "itemIdentifier": {
                    "sku": "FER-1234-0001"
                },
                "qty": 1
            }
        ]
    }
    
    response = requests.post(url=url, headers=headers, data=data)
    reports = response.json()
    return 0


global access_token
access_token = get_access_token(TPL_ID, TPL_SECRET, TPL_GUID, TPL_USERID)


# testing code below
if __name__ == '__main__':

    print()
