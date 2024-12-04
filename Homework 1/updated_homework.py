import datetime
import sqlite3
import requests
from bs4 import BeautifulSoup

DB_NAME="updated_stocks_database.db"
# Register custom adapters for datetime.date and datetime.datetime
def adapt_datetime(dt):
    return dt.isoformat()  # Convert datetime to ISO format string
def adapt_date(d):
    return d.isoformat()  # Convert date to ISO format string
# Register the adapters with sqlite3
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_adapter(datetime.date, adapt_date)

def fetch_issuers(): #fetching all the issuers
    url = 'https://www.mse.mk/en/stats/symbolhistory/kmb'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    select_element = soup.find('select', {'id': 'Code'})
    list_of_codes = []
    for option in select_element.find_all('option'):
        list_of_codes.append(option['value'])
    return list_of_codes

def has_numbers(input_string): #if numbers in issuer_code
    return any(char.isdigit() for char in input_string)

def filter_valid_issuers(all_issuers):
    filtered_issuers = []
    for issuer_code in all_issuers:
        if not has_numbers(issuer_code): #ignore all with numbers
            filtered_issuers.append(issuer_code)
    return filtered_issuers

def find_date(issuers):
    #return {'KMB': '09/09/2024', 'ALK': '10/10/2024'}
    issuer_and_date={} #empty_dictionary
    #get the current date for calculating "last 10 yrs"
    current_date=datetime.datetime.now()
    ten_years_ago=current_date-datetime.timedelta(days=365*10) 
    for issuer in issuers:
        #check last recorded date in db
        last_date=get_last_recorded_date(issuer)
        #if no data, use default start date(10yrs ago)
        if not last_date:
            issuer_and_date[issuer]=ten_years_ago.date()
        else:
            #if data, use last recorded date        
            issuer_and_date[issuer] = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()
    return issuer_and_date

def send_post_request(issuer_code, from_date, to_date):
    url = 'https://www.mse.mk/en/stats/symbolhistory/' + issuer_code
    data = {'FromDate': from_date, 'ToDate': to_date}
    # Send POST request with FORM data using the data parameter
    return requests.post(url, data=data)

# Python code to replace, with . and vice-versa
def Replace(str1):
    str1 = str1.replace(',', 'third')
    str1 = str1.replace('.', ',')
    str1 = str1.replace('third', '.')
    return str1

def get_data_for_issuer(issuer, from_date, to_date):
    print("Fetching data for ", issuer, "from ", from_date, " to ", to_date)
    response = send_post_request(issuer, from_date, to_date)
    if response.status_code==503:
        print("Response failed, retrying")
        response=send_post_request(issuer, from_date, to_date) #retry in case unavailable
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')  # Find the first table on the page
    if not table:
        return [] #if service is unavailable, table will be empty
    table_rows = table.find_all('tr')
    header_cells = table_rows[0].find_all('th')
    header_texts =  [i.text.strip() for i in header_cells]
    data = []
    for tr in table_rows[1:]:
        td = tr.find_all('td')
        row=[issuer]
        for header, i in zip(header_texts, td):
            if header=='Avg. Price' or header=='%chg.'  or header=='Total turnover in denars':
                continue #only fetching the columns we want
            if header=='Date':
                date_obj=datetime.datetime.strptime(i.text.strip(),'%m/%d/%Y').date()
                row.append(date_obj)
            else:
                row.append(Replace(i.text.strip()))
        # row = [i.text.strip() for i in td] 
        data.append(row)
    return data

def add_year(date_obj):
    date_obj+=datetime.timedelta(days=365)
    return date_obj

def is_more_than_a_year_ago(date_obj):
    today=datetime.date.today()
    time_difference=today-date_obj
    return time_difference.days > 365

def split_date_range(from_date):
    date_ranges = []
    while is_more_than_a_year_ago(from_date):
        year_later=add_year(from_date)
        date_ranges.append((from_date, year_later))
        from_date=year_later
    today=datetime.date.today()
    #today_formatted=today.strftime("%m/%d/%Y")
    date_ranges.append((from_date, today))
    return date_ranges

def get_latest_data(issuers_and_dates):
    latest_data = []
    for issuer, from_date in issuers_and_dates.items():
        for start_date, end_date in split_date_range(from_date):
            latest_data+=get_data_for_issuer(issuer, start_date, end_date)
    return latest_data

def create_table():
    # This function ensures that the table is created before any data is written
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions(
        issuer TEXT,
        date DATE, 
        last_trade_price FLOAT,
        max FLOAT,
        min FLOAT,
        volume INTEGER,
        turnover_best INTEGER,
        PRIMARY KEY (issuer, date)
    )
    ''')
    conn.commit()
    conn.close()

def write_to_db(data):
    # Ensure the table is created before any data insertion
    create_table()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany('INSERT OR REPLACE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)', data)
    conn.commit()
    conn.close()

def read_db():
    conn = sqlite3.connect(DB_NAME)    # Connect to the database
    cursor = conn.cursor() # Create a cursor object
    cursor.execute("SELECT * FROM transactions LIMIT 50") # Execute a SELECT query
    rows = cursor.fetchall() # Fetch all rows
    for row in rows: # Print the results
        print(row)
    conn.close() # Close the connection

def get_last_recorded_date(issuer_code):
    conn = sqlite3.connect(DB_NAME) #connect to db
    cursor = conn.cursor()
    cursor.execute('''
    SELECT MAX(date) FROM transactions WHERE issuer = ? 
    ''', (issuer_code,)) #query for last recorded date for issuer
    last_date=cursor.fetchone()[0] #fetch results, will return None if no records are found
    conn.close()
    return last_date

if __name__ == '__main__':
    before_execution=datetime.datetime.now()
    # Ensure the table is created before anything else
    create_table()
    # Get list of issuers
    all_issuers = fetch_issuers()  # Uncomment this line to fetch from the website
    #all_issuers = ['KMB', 'ALK', 'GTC', 'USJE']  # Test with a subset of issuer codes
    
    # Filter 1: Only valid issuers
    filtered_issuers = filter_valid_issuers(all_issuers) 
    #print(filtered_issuers)

    # Filter 2: Find the last available date for each issuer
    issuers_and_dates = find_date(filtered_issuers)
    for key, value in issuers_and_dates.items():
        print(key, value)

    # Filter 3: Get data for each issuer from the specified date
    entries = get_latest_data(issuers_and_dates)
    print("Number of entries fetched ", len(entries))

    before_writing=datetime.datetime.now()
    # Write data to the database
    write_to_db(entries)
    after_writing=datetime.datetime.now()
    running_time=after_writing-before_writing
    print("Writing time to DB took: ", running_time.seconds, "seconds")
    end_of_execution=datetime.datetime.now()
    execution_time=end_of_execution-before_execution
    print("Execution time took: ", execution_time.seconds, "seconds")
    # Read and print the data from the database
    #print("output from DB")
    #read_db()
