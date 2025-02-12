from datetime import datetime as dt
import requests

# formats address chunks into whole address
def address_formatter(raw_address):
    if (("(" in raw_address) and (") " in raw_address)):
        formatted_address_array = raw_address.split(") ")[1]
        formatted_address_array = formatted_address_array.split(", ")
        formatted_address_array.pop()
        # print(formatted_address_array)
        formatted_address = ""
        for i in range(len(formatted_address_array) - 1):
            formatted_address += (formatted_address_array[i] + ", ")
        formatted_address += formatted_address_array[-1]
        formatted_address += ", USA"
    else:
        return False


    # Ex: "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
    # Make sure state is just 2 letters!
    return formatted_address

# print(address_formatter("(Westfield Montgomery) 7101 Democracy Blvd, Bethesda, MD 20852, United States"))

# gets latitude, longitude
def get_lat_long(google_api_key, raw_address):
    input_address = address_formatter(raw_address)
    # print(input_address)

    lat = None
    long = None
    place_id = None
    status = None
    api_key = google_api_key

    # generates json request
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    endpoint = f"{base_url}?address={input_address}&key={api_key}"

    r = requests.get(endpoint)
    # print(r)

    if r.status_code not in range(200, 299):
        # print("bob")
        return [None, None]
    
    # stores json file and attemps to retrieve latitude and longitude
    try:
        json_file = r.json()
        # print(json_file)
        results = json_file["results"][0]
        lat = results["geometry"]["location"]["lat"]
        long = results["geometry"]["location"]["lng"]
        status = json_file["status"]

        # NON-ERRORS:
        # "OK" indicates that no errors occurred; the address was successfully parsed and at least one geocode was returned
        if (status == "OK"):
            return [lat, long]

        # "ZERO_RESULTS" indicates that the geocode was successful but returned no results. This may occur if the geocoder was passed a non-existent address
        elif (status == "ZERO_RESULTS"):
            return [status, status]
        

        # ERRORS:
        # "REQUEST_DENIED" indicates that your request was denied.
        elif (status == "REQUEST_DENIED"):
            return [status, status]
        
        # "INVALID_REQUEST" generally indicates that the query (address, components or latlng) is missing.
        elif (status == "INVALID_REQUEST"):
            return [status, status]
        
        # "UNKNOWN_ERROR" indicates that the request could not be processed due to a server error. The request may succeed if you try again.
        elif (status == "UNKNOWN_ERROR"):
            return [status, status]

    # except case if json retrieval gives an error
    except:
        # Pass: https://www.google.com/search?q=pass+python+function&rlz=1C1SQJL_enUS806US806&oq=pass+python&aqs=chrome.2.69i57j0l6j69i65.2918j0j1&sourceid=chrome&ie=UTF-8 
        pass
        return [None, None]

# Searches for important buildings nearby, takes in API key, address parameters, and search search radius
def key_buildings_search(google_api_key, raw_address, search_radius):
    search_results = None
    important_types = ["airport", "amusement_park", "aquarium", "art_gallery", "bank", "casino", "clothing_store", 
    "convenience_store", "department_store", "drugstore", "movie_theater", "museum", "park", "pharmacy", "restaurant", "shopping_mall", "stadium", 
    "store", "subway_station", "supermarket", "tourist_attraction", "zoo", "lodging"]

    # not actually used but helps with visualization of data pipeline
    is_important = False
    # converts radius from miles to meters
    radius = 1609.34 * search_radius
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    # gets coordinates for given address
    geo_data = get_lat_long(google_api_key, raw_address)
    # print(geo_data)
    latitude = geo_data[0]
    longitude = geo_data[1]

    # sends json request
    endpoint = f"{base_url}?location={latitude}, {longitude}&radius={str(radius)}&opennow&rankby=prominence&key={google_api_key}"

    r = requests.get(endpoint)

    if r.status_code not in range(200, 299):
        return None

    # attempts to parse json, and find key locations within 0.5 mile radius, that meet important location types criteria, and gives a total number of them
    try:
        # sends a json request
        json_file = r.json()
        search_results = json_file["results"]
        raw_number = len(search_results)
        final_number = 0
        status = json_file["status"]

        # logic to get if a place is important or not by iterating through types within each resultant location within 0.5 mile radius
        i = 0
        k = 0
        already_true = False
        while (i<raw_number):
            is_important = False
            already_true = False
            types_length = len(search_results[i]["types"])
            k = 0
            while ((k < types_length) and (already_true == False)):
                if(search_results[i]["types"][k] in important_types):
                    is_important = True
                    already_true = True
                else:
                    is_important = False
                k = k + 1
            if((already_true == True)):
                final_number = final_number + 1
            i = i + 1
            

        # NON-ERRORS:
        # "OK" indicates that no errors occurred; the address was successfully parsed and at least one geocode was returned
        if (status == "OK"):
            # return [final_number, search_results]
            return final_number
        # "ZERO_RESULTS" indicates that the geocode was successful but returned no results. This may occur if the geocoder was passed a non-existent address
        elif (status == "ZERO_RESULTS"):
            return status
        

        # ERRORS:
        # "REQUEST_DENIED" indicates that your request was denied.
        elif (status == "REQUEST_DENIED"):
            return status
        
        # "INVALID_REQUEST" generally indicates that the query (address, components or latlng) is missing.
        elif (status == "INVALID_REQUEST"):
            return status
        
        # "UNKNOWN_ERROR" indicates that the request could not be processed due to a server error. The request may succeed if you try again.
        elif (status == "UNKNOWN_ERROR"):
            return status

    # except case
    except:
        # Pass: https://www.google.com/search?q=pass+python+function&rlz=1C1SQJL_enUS806US806&oq=pass+python&aqs=chrome.2.69i57j0l6j69i65.2918j0j1&sourceid=chrome&ie=UTF-8 
        pass
        return None

# converts raw number of important locations to relative scale with weightage based on max important location density and current hour, as a value from 0-100
def surrounding_risk_rating(raw_address, google_api_key, search_radius = 0.5):
    try:
        # gets number of important locations
        raw_value = int(key_buildings_search(google_api_key, raw_address, search_radius))
        # print("raw_value = " + str(raw_value))
        # gets current hour
        current_hour = int(dt.now().hour)
        # dictionary of weights from 0.0 to 1.0 based on hour of day on 24 hour system
        time_weights = {
            0: 0.2,
            1: 0.1,
            2: 0.1,
            3: 0.1,
            4: 0.1,
            5: 0.2,
            6: 0.3,
            7: 0.4,
            8: 0.5,
            9: 0.5,
            10: 0.5,
            11: 0.6,
            12: 0.6,
            13: 0.7,
            14: 0.7,
            15: 1.0,
            16: 1.0,
            17: 1.0,
            18: 0.8,
            19: 0.8,
            20: 0.8,
            21: 0.5,
            22: 0.5,
            23: 0.2
        }

        # max density * most popular time of day to create "total value" for percentage calculation
        max = 20 * 1.0
        # applies weights to raw number of important locations
        weighted_value = ((raw_value * time_weights[current_hour])/max) * 100
        # print(raw_value)
        # print(weighted_value)

        # assigns scale rating based on weighted_value & returns it
        if((type(weighted_value) == int) or (type(weighted_value) == float)):
            return weighted_value
        else:
            return "Error"

    # except case
    except:
        return "Error"

# tester code
# print(surrounding_risk_rating("(Westfield Montgomery) 7101 Democracy Blvd, Bethesda, MD 20852, United States"))