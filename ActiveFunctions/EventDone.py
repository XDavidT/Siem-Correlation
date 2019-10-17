from ActionsHandlers.EmailHandler import AlertOnEmail
import datetime

def SuccessEvent(client, log_document,b_setting):
    semi_collection = client[b_setting['policy-db-name']][b_setting["semi-alert-collection-name"]]
    success_collection = client[b_setting['policy-db-name']][b_setting['success-alert-collection-name']]
    log_document['offense-close-time'] = datetime.datetime.now()  # Discover time

    # Add to new collection, but only if it done, make the delete
    try:
        success_collection.insert_one(log_document)
        try:
            semi_collection.delete_one({'_id':log_document['_id']})

            # if(log_document['alert']['email']):
            #     AlertOnEmail(log_document)
            AlertOnEmail(log_document)

        except Exception as e:
            print ("Error to remove from semi-collection")
            print(e)
    except Exception as e:
        print("Error to add to success DB the new offense")
        print(e)

def FailEvent(client,log_document,b_setting):
    semi_collection = client[b_setting['policy-db-name']][b_setting['semi-alert-collection-name']]
    fail_collection = client[b_setting['policy-db-name']][b_setting['fail-alert-collection-name']]
    log_document['offense-close-time'] = datetime.datetime.now()
    try:
        fail_collection.insert_one(log_document)
        try:
            semi_collection.delete_one(log_document)
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)