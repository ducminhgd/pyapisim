# Installation

## Dependency

```
Django==1.11.28
djangorestframework==3.9.1
soaplib==2.0.0b2
```

You can run `pip install -r requirements.txt` to install dependencies.

## Database

You can delete the sample database and create your own one.

Default account for admin site: username=`admin`, password=`admin`.


# Usage

## Create Simulator group

Groups are used for filtering responses

## Create Simulator response

1. Group
2. Route: unique, this route is used for determine which response we need.
3. Name: for management.
4. Descritpion: for detail information
5. Headers: headers of response, example `content-type: application/json`, each line is a header.
6. Sleep second: number of delay seconds.
7. Http Status code: Status code for response.
8. Body: response body.

## Calling API

For RESTFul API: `http://127.0.0.1:8000/rest/simple-response-route`, where `simple-response-route` is the route field of the simulator response.

For SOAP API: `http://127.0.0.1:8000/soap/?wsdl`
