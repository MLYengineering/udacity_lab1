from azure.storage.blob import BlobServiceClient
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry, Region
from msrest.authentication import ApiKeyCredentials
import pandas as pd
connect_str = os.getenv('connect_str')
container_name = "lab1"  # Der Name deines Containers
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
AZURE_FORM_RECOGNIZER_KEY = os.getenv('AZURE_FORM_RECOGNIZER_KEY')
endpoint = AZURE_FORM_RECOGNIZER_ENDPOINT
key = AZURE_FORM_RECOGNIZER_KEY
form_recognizer_client = FormRecognizerClient(endpoint=endpoint, credential=AzureKeyCredential(key))
document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

def get_manifest():
    blob_client = container_client.get_blob_client('FlightManifest_mod.csv')
    with open("FlightManifest_mod.csv", "wb") as download_file:
        download_stream = blob_client.download_blob()
        download_file.write(download_stream.readall())
    flight_manifest = pd.read_csv("FlightManifest_mod.csv", sep=';')
    print(flight_manifest.head())
    return flight_manifest


def get_blob_url(blob_name):

    # Blob-Client erstellen
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # URL des Blobs abrufen
    url = blob_client.url
    
    return url

def list_blobs_in_subfolder(subfolder_name):

    # Liste der Blobs im Subfolder abrufen
    blob_list = container_client.list_blobs(name_starts_with=subfolder_name)

    # Nur die Namen der Blobs extrahieren
    blob_names = [blob.name for blob in blob_list]

    return blob_names

def add_to_session_dict(request, key, value):
    if 'session_dict' not in request.session:
        request.session['session_dict'] = {}
    
    session_dict = request.session['session_dict']
    session_dict[key] = value
    
    request.session['session_dict'] = session_dict
    print(session_dict)


def get_id_card_details (id_link):

    blob_client = container_client.get_blob_client(id_link)
    download_stream = blob_client.download_blob()
    file_content = download_stream.readall()
    poller = form_recognizer_client.begin_recognize_identity_documents(file_content)
    id_result = poller.result()
    id_extraction = {
        'first_name' : id_result[0].fields.get("FirstName").value,
        'last_name' : id_result[0].fields.get("LastName").value,
        'dob' : pd.to_datetime(id_result[0].fields.get("DateOfBirth").value).date(),        
        'sex' : id_result[0].fields.get("Sex").value
    }
    
    for item in id_extraction.items():
        print(item)
    return id_extraction

def message_id_fail():
    messages = [
        'Dear Sir/Madam,',
        'Some of the information on your ID card does not match the flight manifest data, so you cannot board the plane.',
        'Please see a customer service representative'
    ]
    return "\n".join(messages)
    
def message_boardingpass_fail():
    messages = [
        'Dear Sir/Madam,',
        'some of the information on your boarding pass does not match the flight manifest data, so you cannot board the plane.',
        'Please see a customer service representative'
    ]
    return "\n".join(messages)

def message_passenger(passenger_row):
    df_output = passenger_row
    if df_output.loc[0,'Sex'] == 'M':
        salutation = 'Mr.'
    elif df_output.loc[0,'Sex'] == 'F':
        salutation = 'Ms.'
    else:
        salutation = ''
    
    messages = [
        f"Dear {salutation} {df_output.loc[0, 'Passanger Name']},",
        f"you are welcome to flight #{df_output.loc[0, 'Flight No.']} from {df_output.loc[0, 'From']} to {df_output.loc[0, 'To']}.",
        f"Your seat number is {df_output.loc[0, 'Seat']} and it is confirmed."
    ]
    
    #if df_output.loc[0, 'Baggage'] == 'No':
    #    messages.append('We did not find a prohibited item (lighter) in your carry-on baggage.')
    #    messages.append('Thanks for following the procedure.')
    #else:
    #    messages.append('We have found a prohibited item in your carry-on baggage, and it is flagged for removal.')
    #messages.append('Your identity could not be verified. Please see a customer service representative.')
    
    return "\n".join(messages)


def get_boardingpass_details(boarding_pass_link):
    model_id = "boardingpass_validation"
    blob_client = container_client.get_blob_client(boarding_pass_link)
    download_stream = blob_client.download_blob()
    file_content = download_stream.readall()
    poller = document_analysis_client.begin_analyze_document(model_id=model_id, document=file_content)
    result = poller.result()
    
    expected_fields = ["FirstName", "LastName", "Seat", "Date", "Flightnumber", "Carrier", "Origin", "Destination"]
    
    boardingpass_details = {"Fields": {}}  # Init dictionary for return
    
    for document in result.documents:
        for name, field in document.fields.items():
            field_value = field.value if field.value else field.content
            boardingpass_details["Fields"][name] = {
                "Value": field_value,
                "ValueType": field.value_type,
                "Confidence": field.confidence
            }
    
    # Check if all requested fields are found
    found_fields = boardingpass_details["Fields"].keys()
    missing_fields = [field for field in expected_fields if field not in found_fields]
    
    if missing_fields:
        print("Missing fields:", missing_fields)
        
    for field_name, field_info in boardingpass_details["Fields"].items():
        print(f"Field: {field_name}")
        print(f"  Value: {field_info['Value']}")
        print(f"  ValueType: {field_info['ValueType']}")
        print(f"  Confidence: {field_info['Confidence']}")
        print("-----------------------------------")
    
    return boardingpass_details

def validation_id_manifest(flight_manifest,id_card):
    validation_id_status = 0
    
    # ----- perform name check -----
    mask_name = ((flight_manifest['FirstName'].str.lower() == id_card['first_name'].lower()) &
                 (flight_manifest['LastName'].str.lower() == id_card['last_name'].lower()))
    matched_rows_name = flight_manifest.loc[mask_name]
    if not matched_rows_name.empty:
        #print("name validation ID to manifest: positive check by passender:")
        #for index, row in matched_rows_name.iterrows():
        #    print(f"Passagier Name: {row['Passanger Name']}, Ticket No.: {row['Ticket No.']}")
        validation_id_status = 1
    else:
        print("name validation ID to manifest: negative check:")
        
    # ----- perform DoB check -----
    flight_manifest['DoB'] = pd.to_datetime(flight_manifest['DoB'])
    mask_dob = (flight_manifest['DoB'] == pd.to_datetime(id_card['dob']))
    matched_rows_dob = flight_manifest.loc[mask_dob]
    if not matched_rows_dob.empty:
        #print("DoB validation ID to manifest: positive check by passender:")
        flight_manifest.loc[mask_dob, 'DoBValidation'] = True
        #for index, row in matched_rows_dob.iterrows():
        #    print(f"Passagier Name: {row['Passanger Name']}, Ticket No.: {row['Ticket No.']}")
        
    return validation_id_status

def validation_boardingpass_manifest(flight_manifest,boardingpass):
    validation_boardingpass_status = 0
    flight_manifest['Date'] = pd.to_datetime(flight_manifest['Date'])
    mask = (
        (flight_manifest['Passanger Name'].str.contains(f"{boardingpass['Fields']['FirstName']['Value']} {boardingpass['Fields']['LastName']['Value']}")) & 
        (flight_manifest['Seat'] == boardingpass['Fields']['Seat']['Value']) & 
        (flight_manifest['Date'] == boardingpass['Fields']['Date']['Value']) &
        (flight_manifest['Flight No.'] == int(boardingpass['Fields']['Flightnumber']['Value']))& 
        (flight_manifest['Carrier '] == boardingpass['Fields']['Carrier']['Value']) &
        (flight_manifest['From'] == boardingpass['Fields']['Origin']['Value']) & 
        (flight_manifest['To'] == boardingpass['Fields']['Destination']['Value'])
    )
    matched_rows = flight_manifest.loc[mask]
    if not matched_rows.empty:
        #print("validation boardingpass to manifest: positive check by passender:")
        
        # setting BoardingPassValidation to true
        flight_manifest.loc[mask, 'BoardingPassValidation'] = True
        
        #for index, row in matched_rows.iterrows():
        #    print(f"Passagier Name: {row['Passanger Name']}, Ticket No.: {row['Ticket No.']}")
        validation_boardingpass_status = 1
   
    return validation_boardingpass_status

def validation_boardingpass_id(boardingpass, id_card):
    validation_boardingpass_id_status = 0
    boarding_name=(f"{boardingpass['Fields']['FirstName']['Value']} {boardingpass['Fields']['LastName']['Value']}").lower() 
    id_name=f"{id_card['first_name']} {id_card['last_name']}".lower()
    if boarding_name == id_name:
        validation_boardingpass_id_status = 1
    return validation_boardingpass_id_status


def luggage_check(suitcase):
    if suitcase == 'https://aicourselab1.blob.core.windows.net/lab1/suitcases/no_luggage.png':
        message = ['We did not find a prohibited item (lighter) in your carry-on baggage. Thanks for following the procedure']
    else:
        suitcase = suitcase[48:]
        # prediction ressources
        PREDICTION_ENDPOINT = os.getenv('PREDICTION_ENDPOINT')
        #https://www.customvision.ai/
        prediction_key = os.getenv('prediction_key')
        #  custom vision - gearwheel - prediction ressources
        prediction_resource_id = os.getenv('prediction_resource_id')
        prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
        predictor = CustomVisionPredictionClient(PREDICTION_ENDPOINT, prediction_credentials)
        project_id = '3bfe4c00-0957-4030-aef1-5992ff7dce36'
        publish_iteration_name = 'Iteration2'
        blob_client = container_client.get_blob_client(suitcase)
        download_stream = blob_client.download_blob()
        file_content = download_stream.readall()
        results = predictor.detect_image(project_id, publish_iteration_name, file_content)
        for prediction in results.predictions[0:1]:
            probability = "\t" + prediction.tag_name +" {0:.2f}%".format(prediction.probability * 100)
        message = f"We found a forbidden item in your luggage: {probability}"

    return message


def process_person_documents(id, boardingpass, flight_manifest, suitcase):
    validation_name_status = 0
    id_link = id
    boarding_pass_link = boardingpass
    suitcase = suitcase
    
    #------ 3 Way name validation, DoB Validation, Boarding Pass Validation ------
    ## validation_name_status = int for 2 step process
    #------ Extraction of id details ------
    if id_link:
        id_card = get_id_card_details (id_link)
        ## in validation_id_manifest DoB Validation is included
        validation_name_status = validation_id_manifest(flight_manifest,id_card)
        if validation_name_status == 0:
            return message_id_fail()
    
    #------ Extraction of boardingpass details ------
    if boarding_pass_link:
        boardingpass = get_boardingpass_details (boarding_pass_link)
        ## in validation_id_manifest Boarding Pass Validation is included
        validation_name_status = validation_name_status + validation_boardingpass_manifest(flight_manifest,boardingpass)
        validation_name_status = validation_name_status + validation_boardingpass_id(boardingpass, id_card)
        if validation_name_status == 1:
            return message_boardingpass_fail()
        elif validation_name_status == 2:
            return message_boardingpass_fail()
 
    # check if both name valids are positive
    
    if validation_name_status == 3:
        mask_name = ((flight_manifest['FirstName'].str.lower() == id_card['first_name'].lower()) &
                 (flight_manifest['LastName'].str.lower() == id_card['last_name'].lower()))
        matched_rows_name = flight_manifest.loc[mask_name]
        if not matched_rows_name.empty:
            flight_manifest.loc[mask_name, 'NameValidation'] = True
            passenger_row = flight_manifest.loc[mask_name].reset_index()
            message_luggage = luggage_check(suitcase)
            message = message_passenger(passenger_row)

            messages = [
                message,
                message_luggage,
                'Your identity could not be verified. Please see a customer service representative.'
            ]
            final_message = "\n".join(messages)
    
            return final_message
            
    