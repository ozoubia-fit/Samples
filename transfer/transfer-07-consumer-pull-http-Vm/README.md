# Implement a simple "Consumer Pull" Http transfer flow between (host - VM)

This Example builds upon [Consumer Pull Http transfer flow](https://github.com/Think-iT-Labs/EDC-Samples/tree/feature%231580_create_samples_for_the_HttpData_proxy_flow/transfer/transfer-06-consumer-pull-http) in which the data transfer in that example was locally on the same machine, while in this example the transfer happens between two machines (a host machine and a Virtual machine)
To demonstrate the functionality, as well building a simple API in the provider side to serve the data which is located in the provider machine (only tested with 1 file for the sake of simplicity). 


The sample code is contains the following parts:
* `http-pull-connector`: contains the configuration for both the consumer and provider connectors.
* `backend-consumer`: contains the backend service where the consumer connector will send the
  EndpointDataReference to access the data.
* `backend-provider`: contains a simple backend for the provider, which only contains a GET method that retrieves a text file to be transfered.
* `http-pull-consumer`: contains configuration files for the consumer. 
* `http-pull-provider`: contains configuration files for the provider.

To run the sample we need a working virtual machine. in which Java +11 must be installed.

Since the two connectors are running on different machines, we need to configure their IP addresses; they need have different IP address 
but still be able to communicate between each other (can be tested by pinging). In this Example let's assume that the IP address for each are as follows:
* Consumer: 192.168.0.6
* Provider: 192.168.0.5

The same steps were followed from the [Consumer Pull Http transfer flow](https://github.com/Think-iT-Labs/EDC-Samples/tree/feature%231580_create_samples_for_the_HttpData_proxy_flow/transfer/transfer-06-consumer-pull-http) Example.
Therefore it's kept short here. 

# Building a connector

The first step is to build the connector on both machine sides. we can do it by using this command.

```bash
./gradlew transfer:transfer-07-consumer-pull-http-Vm:http-pull-connector:build
```

### 1. Run a provider

To run a provider on the first machine, the following command is executed.

```bash
java -Dedc.keystore=transfer/transfer-07-consumer-pull-http-Vm/certs/cert.pfx -Dedc.keystore.password=123456 -Dedc.vault=transfer/transfer-07-consumer-pull-http-Vm/http-pull-provider/provider-vault.properties -Dedc.fs.config=transfer/transfer-07-consumer-pull-http-Vm/http-pull-provider/provider-configuration.properties -jar transfer/transfer-07-consumer-pull-http-Vm/http-pull-connector/build/libs/http-pull-connector.jar
```

### 2. Run a consumer

To run a consumer on the second machine, the following command is executed.

```bash
java -Dedc.keystore=transfer/transfer-07-consumer-pull-http-Vm/certs/cert.pfx -Dedc.keystore.password=123456 -Dedc.vault=transfer/transfer-07-consumer-pull-http-Vm/http-pull-consumer/consumer-vault.properties -Dedc.fs.config=transfer/transfer-07-consumer-pull-http-Vm/http-pull-consumer/consumer-configuration.properties -jar transfer/transfer-07-consumer-pull-http-Vm/http-pull-connector/build/libs/http-pull-connector.jar
```


The port number are left unchanged from the previous example, the consumer will listen on the
ports `29191`, `29192` (management API) and `29292` (IDS API) and the provider will listen on the
ports `12181`, `19182` (management API) and `19282` (IDS API).

# Starting the Sample execution

### 1. Register data plane instance for provider on machine 1

We have to register a data plane instance on the first machine using the following command; the IP address of the machine need to be changed in the command accordingly.

```bash
curl -H 'Content-Type: application/json' \
     -d '{
   "edctype": "dataspaceconnector:dataplaneinstance",
   "id": "http-pull-provider-dataplane",
   "url": "http://192.168.0.5:19292/control/transfer",
   "allowedSourceTypes": [ "HttpData" ],
   "allowedDestTypes": [ "HttpProxy", "HttpData" ],
   "properties": {
     "publicApiUrl": "http://192.168.0.5:19291/public/"
   }
 }' \
     -X POST "http://192.168.0.5:19193/api/v1/data/instances"
```

### 2. Register data plane instance for consumer on machine 2

A data plane instance is registered as well for the consumer on machine 2 using the corresponding IP address in the command as follows.

```bash
curl -H 'Content-Type: application/json' \
     -d '{
   "edctype": "dataspaceconnector:dataplaneinstance",
   "id": "http-pull-consumer-dataplane",
   "url": "http://192.168.0.6:29292/control/transfer",
   "allowedSourceTypes": [ "HttpData" ],
   "allowedDestTypes": [ "HttpProxy", "HttpData" ],
   "properties": {
     "publicApiUrl": "http://192.168.0.6:29291/public/"
   }
 }' \
     -X POST "http://192.168.0.6:29193/api/v1/data/instances"
```

### 3. Create a backend API on the provider side that serves that data

In this step, a simple backend API on the provider side was created using FastAPI, It only serves one data called test.txt when called.
this data is then used for the transfer to the consumer.
Python, FastAPI and Uvicorn needs be installed on the provider machine for the backend to work.
We also need to start it on the host machine with the same IP address.

To Start the consumer backend API we use the following command. 

```bash
uvicorn main:app --reload --host 192.168.0.5
```

### 4. Create an Asset on the provider side

After starting the backend API on the provider side, now we can proceed to creating an Asset that is served from that backend as follows
in the BaseUrl we include our backend api url. and we change the IP address of the provider again.
the result of the backend api call on : https://192.168.0.5/api/ would get the test.txt file.

```bash
curl -d '{
           "asset": {
             "properties": {
               "asset:prop:id": "assetId",
               "asset:prop:name": "product description",
               "asset:prop:contenttype": "application/json"
             }
           },
           "dataAddress": {
             "properties": {
               "name": "Test asset",
               "baseUrl": "https://192.168.0.5/api/",
               "type": "HttpData"
             }
           }
         }' -H 'content-type: application/json' http://192.168.0.5:19193/api/v1/data/assets \
         -s | jq
```


### 5. Create a Policy on the provider

We run this command to issue a policy on the provider machine. changing the IP address according again.

```bash
curl -d '{
           "id": "aPolicy",
           "policy": {
             "uid": "231802-bb34-11ec-8422-0242ac120002",
             "permissions": [
               {
                 "target": "assetId",
                 "action": {
                   "type": "USE"
                 },
                 "edctype": "dataspaceconnector:permission"
               }
             ],
             "@type": {
               "@policytype": "set"
             }
           }
         }' -H 'content-type: application/json' http://192.168.0.5:19193/api/v1/data/policydefinitions \
         -s | jq
```

### 6. Create a contract definition on Provider

We create a contract definition on the provider side for the data.

```bash
curl -d '{
           "id": "1",
           "accessPolicyId": "aPolicy",
           "contractPolicyId": "aPolicy",
           "criteria": []
         }' -H 'content-type: application/json' http://192.168.0.5:19193/api/v1/data/contractdefinitions \
         -s | jq
```

### 7. Fetching the catalog from the Consumer machine

In this step we move to the consumer machine and we run the following command to get the catalog, in this case we have to include the providerUrl which contains the IP address of the provider as well.

```bash
curl http://192.168.0.6:29193/api/v1/data/catalog\?providerUrl\=http://192.168.0.5:19194/api/v1/ids/data
```

Sample output:

```json
{
  "id": "default",
  "contractOffers": [
    {
      "id": "1:11dd1ed3-0309-49f0-b3b9-dceb3d75bdbe",
      "policy": {
        "permissions": [
          {
            "edctype": "dataspaceconnector:permission",
            "uid": null,
            "target": "assetId",
            "action": {
              "type": "USE",
              "includedIn": null,
              "constraint": null
            },
            "assignee": null,
            "assigner": null,
            "constraints": [],
            "duties": []
          }
        ],
        "prohibitions": [],
        "obligations": [],
        "extensibleProperties": {},
        "inheritsFrom": null,
        "assigner": null,
        "assignee": null,
        "target": "assetId",
        "@type": {
          "@policytype": "set"
        }
      },
      "asset": {
        "id": "assetId",
        "createdAt": 1674578271345,
        "properties": {
          "asset:prop:byteSize": null,
          "asset:prop:name": "product description",
          "asset:prop:contenttype": "application/json",
          "asset:prop:id": "assetId",
          "asset:prop:fileName": null
        }
      },
      "provider": "urn:connector:http-pull-provider",
      "consumer": "urn:connector:http-pull-consumer",
      "offerStart": null,
      "offerEnd": null,
      "contractStart": null,
      "contractEnd": null
    }
  ]
}
```

### 8. Negotiate a contract

The contract negociation is then initiated from the consumer machine, IP address of both connectors are specified as follows.

```bash
curl -d '{
           "connectorId": "http-pull-provider",
           "connectorAddress": "http://192.168.0.5:19194/api/v1/ids/data",
           "protocol": "ids-multipart",
           "offer": {
             "offerId": "1:50f75a7a-5f81-4764-b2f9-ac258c3628e2",
             "assetId": "assetId",
             "policy": {
               "uid": "231802-bb34-11ec-8422-0242ac120002",
               "permissions": [
                 {
                   "target": "assetId",
                   "action": {
                     "type": "USE"
                   },
                   "edctype": "dataspaceconnector:permission"
                 }
               ],
               "@type": {
                 "@policytype": "set"
               }
             }
           }
         }' -X POST -H 'content-type: application/json' http://192.168.0.6:29193/api/v1/data/contractnegotiations \
         -s | jq
```

Sample output:

```json
{
  "createdAt": 1674585892398,
  "id": "8ce50f33-25f3-42df-99e7-d6d72d83032c"
}
```

### 9. Getting the contract agreement id from the consumer machine

After the contract negociation is finished we can get the contract agreement Id from the following command.

```bash
curl -X GET "http://192.168.0.6:29193/api/v1/data/contractnegotiations/<contract negotiation id, returned by the negotiation call>" \
    --header 'Content-Type: application/json' \
    -s | jq
```

Sample output:

```json
{
  "createdAt": 1674585892398,
  "updatedAt": 1674585897476,
  "contractAgreementId": "1:307a028a-b2b3-495e-ab6c-f6dad24dd098",
  "counterPartyAddress": "http://192.168.0.5:19194/api/v1/ids/data",
  "errorDetail": null,
  "id": "8ce50f33-25f3-42df-99e7-d6d72d83032c",
  "protocol": "ids-multipart",
  "state": "CONFIRMED",
  "type": "CONSUMER"
}
```

### 10. Start the transfer from the consumer machine

As per [Consumer Pull Http transfer flow](https://github.com/Think-iT-Labs/EDC-Samples/tree/feature%231580_create_samples_for_the_HttpData_proxy_flow/transfer/transfer-06-consumer-pull-http) example, a backend service on the consumer side needs to be running, we need to build and start it using the following command. 

```bash
./gradlew transfer:transfer-07-consumer-pull-http-Vm:backend-consumer:build
java -jar transfer/transfer-07-consumer-pull-http-vm/backend-consumer/build/libs/backend-service.jar 
```

After the backend has started we can start the transfer using the following command.

```bash
curl -X POST "http://192.168.0.6:29193/api/v1/data/transferprocess" \
    --header "Content-Type: application/json" \
    --data '{
                "connectorId": "http-pull-provider",
                "connectorAddress": "http://192.168.0.5:19194/api/v1/ids/data",
                "contractId": "<contract agreement id>",
                "assetId": "assetId",
                "managedResources": "false",
                "dataDestination": { "type": "HttpProxy" }
            }' \
    -s | jq
```

Then, we will get a UUID in the response. This time, this is the ID of the `TransferProcess` (
process id) created on the consumer
side, because like the contract negotiation, the data transfer is handled in a state machine and
performed asynchronously.

Sample output:

```json
 {
  "createdAt": 1674078357807,
  "id": "591bb609-1edb-4a6b-babe-50f1eca3e1e9"
}
```

### 11. Check the transfer status

Due to the nature of the transfer, it will be very fast and most likely already done by the time you
read the UUID.

```bash
curl http://192.168.0.5:19193/api/v1/data/transferprocess/<transfer process id>
```

### 11. Pull the data

At this step, if you look at the backend service logs, you will have a json representing
the data useful for reading the data. This is presented in the following section.

Sample log for the Backend Service:

```json
{
  "id": "77a3551b-08da-4f81-b61d-fbc0c86c1069",
  "endpoint": "http://192.168.0.6:29291/public/",
  "authKey": "Authorization",
  "authCode": "eyJhbGciOiJSUzI1NiJ9.eyJkYWQiOiJ7XCJwcm9wZXJ0aWVzXCI6e1wiYXV0aEtleVwiOlwiQXV0aG9yaXphdGlvblwiLFwiYmFzZVVybFwiOlwiaHR0cDpcL1wvbG9jYWxob3N0OjE5MjkxXC9wdWJsaWNcL1wiLFwiYXV0aENvZGVcIjpcImV5SmhiR2NpT2lKU1V6STFOaUo5LmV5SmtZV1FpT2lKN1hDSndjbTl3WlhKMGFXVnpYQ0k2ZTF3aVltRnpaVlZ5YkZ3aU9sd2lhSFIwY0hNNlhDOWNMMnB6YjI1d2JHRmpaV2h2YkdSbGNpNTBlWEJwWTI5a1pTNWpiMjFjTDNWelpYSnpYQ0lzWENKdVlXMWxYQ0k2WENKVVpYTjBJR0Z6YzJWMFhDSXNYQ0owZVhCbFhDSTZYQ0pJZEhSd1JHRjBZVndpZlgwaUxDSmxlSEFpT2pFMk56UTFPRGcwTWprc0ltTnBaQ0k2SWpFNk1XVTBOemc1TldZdE9UQXlOUzAwT1dVeExUazNNV1F0WldJNE5qVmpNemhrTlRRd0luMC5ITFJ6SFBkT2IxTVdWeWdYZi15a0NEMHZkU3NwUXlMclFOelFZckw5eU1tQjBzQThwMHFGYWV0ZjBYZHNHMG1HOFFNNUl5NlFtNVU3QnJFOUwxSE5UMktoaHFJZ1U2d3JuMVhGVUhtOERyb2dSemxuUkRlTU9ZMXowcDB6T2MwNGNDeFJWOEZoemo4UnVRVXVFODYwUzhqbU4wZk5sZHZWNlFpUVFYdy00QmRTQjNGYWJ1TmFUcFh6bDU1QV9SR2hNUGphS2w3RGsycXpJZ0ozMkhIdGIyQzhhZGJCY1pmRk12aEM2anZ2U1FieTRlZXU0OU1hclEydElJVmFRS1B4ajhYVnI3ZFFkYV95MUE4anNpekNjeWxyU3ljRklYRUV3eHh6Rm5XWmczV2htSUxPUFJmTzhna2RtemlnaXRlRjVEcmhnNjZJZzJPR0Eza2dBTUxtc3dcIixcInByb3h5TWV0aG9kXCI6XCJ0cnVlXCIsXCJwcm94eVF1ZXJ5UGFyYW1zXCI6XCJ0cnVlXCIsXCJwcm94eUJvZHlcIjpcInRydWVcIixcInR5cGVcIjpcIkh0dHBEYXRhXCIsXCJwcm94eVBhdGhcIjpcInRydWVcIn19IiwiZXhwIjoxNjc0NTg4NDI5LCJjaWQiOiIxOjFlNDc4OTVmLTkwMjUtNDllMS05NzFkLWViODY1YzM4ZDU0MCJ9.WhbTzERmM75mNMUG2Sh-8ZW6uDQCus_5uJPvGjAX16Ucc-2rDcOhAxrHjR_AAV4zWjKBHxQhYk2o9jD-9OiYb8Urv8vN4WtYFhxJ09A0V2c6lB1ouuPyCA_qKqJEWryTbturht4vf7W72P37ERo_HwlObOuJMq9CS4swA0GBqWupZHAnF-uPIQckaS9vLybJ-gqEhGxSnY4QAZ9-iwSUhkrH8zY2GCDkzAWIPmvtvRhAs9NqVkoUswG-ez1SUw5bKF0hn2OXv_KhfR8VsKKYUbKDQf5Wagk7rumlYbXMPNAEEagI4R0xiwKWVTfwwZPy_pYnHE7b4GQECz3NjhgdIw",
  "properties": {
    "cid": "1:1e47895f-9025-49e1-971d-eb865c38d540"
  }
}
```

Once this json is read, use a tool like postman or curl to execute the following query, to read the
data

```bash
curl --location --request GET 'http://192.168.0.6:29291/public/' \
--header 'Authorization: <auth code>'
```

we can check if the file is successfuly transfered.