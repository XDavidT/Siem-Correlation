from ActiveFunctions.Headers import *
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# TODO: Separate type local/global
def LogsTracker_service():
    print("LogsTracker_service - Flag 1#")
    # Getting all data from Cache (from db sync)
    setting = Load_Setting()
    events = Load_Events(setting)
    rules = Load_Rules(setting)

    # Get cursor to mongo collection - Client manager -> logs
    client = Mongo_Connection()
    logs_collection = client[setting['logs-db-name']][setting['logs-collection-name']]
    last_time_delta = datetime.datetime.now() - datetime.timedelta(hours=setting['logs-from-X-hours']) # Time Delta

    for event in events:                                          # Search for each event
        devices = []
        rule = rules[str(events[event]['rules'][0]['rule_id'])]  # Check only FIRST rule from each event
        print("Looking for:      " + rule['field'] + ' :  ' + str(rule['value']))  # Dev printing

        results = logs_collection.find(                 # Build the query
            {'insert_time': {'$gte': last_time_delta},  # Time delta ( X time back )
             rule['field']: rule['value']})             # User first rule field:value


        # -- Local -- #
        if events[event]['type'] == 'local':                # Log is LOCAL only, and need to watch it.
            for log in results:
                if log[setting['local_based_on']] not in devices:   # Based on Host/MAC/IP by prefer
                    devices.append(log[setting['local_based_on']])  # Using list check that no double log will be
                    DumpDocumentToMongo(client, events[event], log,device_name=log[setting['local_based_on']])

        # -- Global -- #
        elif events[event]['type'] == "global":             # Log is GLOBAL, and need to get the scale
            logs = []
            for log in results:                             # We only care how much Devices have the log
                if log[setting['local_based_on']] not in devices:   # No double event from same device
                    devices.append(log[setting['local_based_on']])
                    logs.append(log)
            DumpDocumentToMongo(client, events[event], logs, devices=devices)

        # -- Unknown -- #
        else:
            print('no event type')

    client.close()
    print("Flag 1# is done")

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////// #
# Only occur once when first rule detect in event - Not Async - run_until_complete
def DumpDocumentToMongo(client, event, log, device_name = None,devices = None):
    print("Flag 3#")
    setting = Load_Setting()

    log_dump = {
        'event': event['_id'],
        'step': 0,  # Mean rule['0'] occur,
        'curr_repeat': 0,
        'type': event['type'],
        'log': [log],
        'rules': event['rules']
    }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Log Dump Customization ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#S
    # One rule & one repeat, we done
    if (len(event['rules']) == 1 and event['rules'][0]['repeated'] == 1):
        log_dump['curr_repeat'] = 1

    # If the current rule need to be repeat
    elif(event['rules'][0]['repeated'] > 1):
        log_dump['curr_repeat'] = 1

    # Or we need to go next rule
    elif(len(event['rules']) > 1):
        log_dump['step'] = 1


    # Check for global/ local
    if(event['type'] == "global"):
        log_dump['device'] = devices
    # But if it's local, it's need one device per each semi-event
    else:
        log_dump['device'] = device_name

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Log Dump Customization ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#E

    try:
        semi_open = client[setting['policy-db-name']]['semi-open'] # TODO: add to setting semi-open-local
        '''
        We need to check that no duplicate will be in our semi-event DB
        by this statement we can assure this type of event & this device aren't there
        '''
        if ( event['type'] == "local"
                and
                (semi_open.find_one({'event':event['_id'], 'device':device_name}) is not None) ):
            print("Already in handle...")
            return
        else:
            semi_open.insert_one(log_dump)
            print('Insert Log Status: OK.')           # Dev print
    except Exception as e:
        print("Insert Log Status: Error -> "+str(e))  # Dev print


# When finish do nothing, the service that check Semi - will find it in db.

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////// #


# logs_collection = client[setting['logs-db-name']][setting['logs-collection-name']]
# semi_collection = client[setting['policy-db-name']][setting['semi-alert-collection-name']]
