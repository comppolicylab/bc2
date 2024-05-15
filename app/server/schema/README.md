---
title: Blind Charging API v0.1.1
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
highlight_theme: darkula
headingLevel: 2

---

<!-- Generator: Widdershins v4.0.1 -->

<h1 id="blind-charging-api">Blind Charging API v0.1.1</h1>

> Scroll down for code samples, example requests and responses. Select a language for code samples from the tabs above or the mobile navigation menu.

Status: **DRAFT**

**_This is a draft specification. The objects and routes are subject to revision._**

This API lets an application communicate with the CPL Blind Charging module via an HTTP REST API.

Email: <a href="mailto:jnudell@hks.harvard.edu">Joe Nudell</a>
License: <a href="https://opensource.org/license/mit/">MIT License</a>

<h1 id="blind-charging-api-redaction">redaction</h1>

Operations related to document redaction.

## Redact a document

<a id="opIdredact-document"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /redact \
  -H 'Content-Type: application/json'

```

```http
POST /redact HTTP/1.1

Content-Type: application/json

```

```javascript
const inputBody = '{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendants": [
    {
      "defendantId": "string",
      "name": "string",
      "aliases": [
        "string"
      ]
    }
  ],
  "documents": [
    {
      "attachmentType": "LINK",
      "documentId": "string",
      "url": "http://example.com"
    }
  ],
  "callbackUrl": "http://example.com"
}';
const headers = {
  'Content-Type':'application/json'
};

fetch('/redact',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json'
}

result = RestClient.post '/redact',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json'
}

r = requests.post('/redact', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/redact', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/redact");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/redact", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /redact`

Submit a document for redaction. Redaction happens asynchronously and may take some time.
When finished, the redacted document will be posted to the provided callback URL.

A callback will be POSTed to the provided URL when the redaction process is completed for each input document.
The callback will contain either `RedactionResultSuccess` or `RedactionResultError`.

> Body parameter

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendants": [
    {
      "defendantId": "string",
      "name": "string",
      "aliases": [
        "string"
      ]
    }
  ],
  "documents": [
    {
      "attachmentType": "LINK",
      "documentId": "string",
      "url": "http://example.com"
    }
  ],
  "callbackUrl": "http://example.com"
}
```

<h3 id="redact-a-document-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[RedactionRequest](#schemaredactionrequest)|true|none|

<h3 id="redact-a-document-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Accepted|None|

### Callbacks

#### redactionComplete

**{$request.body#/callbackUrl}**

## Redact a document

> Code samples

```shell
# You can also use wget
curl -X POST /redact \
  -H 'Content-Type: application/json'

```

```http
POST /redact HTTP/1.1

Content-Type: application/json

```

```javascript
const inputBody = '{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "redactedDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "COMPLETE"
}';
const headers = {
  'Content-Type':'application/json'
};

fetch('/redact',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json'
}

result = RestClient.post '/redact',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json'
}

r = requests.post('/redact', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/redact', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/redact");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/redact", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /redact`

This callback is made for each input document when it is finished.

> Body parameter

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "redactedDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "COMPLETE"
}
```

<h3 id="redact-a-document-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[RedactionResultCompleted](#schemaredactionresultcompleted)|true|none|

<h3 id="redact-a-document-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Accepted|None|

<aside class="success">
This operation does not require authentication
</aside>

<aside class="success">
This operation does not require authentication
</aside>

## Get status of document redaction for a case.

<a id="opIdget-redaction-status"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /redact/{jurisdictionId}/{caseId} \
  -H 'Accept: application/json'

```

```http
GET /redact/{jurisdictionId}/{caseId} HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/redact/{jurisdictionId}/{caseId}',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/redact/{jurisdictionId}/{caseId}',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/redact/{jurisdictionId}/{caseId}', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/redact/{jurisdictionId}/{caseId}', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/redact/{jurisdictionId}/{caseId}");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/redact/{jurisdictionId}/{caseId}", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /redact/{jurisdictionId}/{caseId}`

Get the status of redaction for all documents in a case.
This will return a list of document IDs and their redaction status.

Generally, the push mechanism provided by the callback URL passed to the `/redact` endpoint should be used to determine when the redaction process is completed.
However, this endpoint can be used to poll for the status of redaction if necessary.

<h3 id="get-status-of-document-redaction-for-a-case.-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|jurisdictionId|path|string|true|The jurisdiction ID|
|caseId|path|string|true|The case ID|
|defendantId|query|string|false|Optionally, filter status by a specific defendant.|

> Example responses

> 200 Response

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "requests": [
    {
      "jurisdictionId": "string",
      "caseId": "string",
      "maskedDefendants": [
        {
          "defendantId": "string",
          "alias": "string"
        }
      ],
      "inputDocument": {
        "attachmentType": "LINK",
        "documentId": "string",
        "url": "http://example.com"
      },
      "redactedDocument": {
        "attachmentType": "LINK",
        "documentId": "string",
        "url": "http://example.com"
      },
      "status": "COMPLETE"
    }
  ]
}
```

<h3 id="get-status-of-document-redaction-for-a-case.-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|OK|[RedactionStatus](#schemaredactionstatus)|

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="blind-charging-api-review">review</h1>

Operations related to reviewing documents.

## Get information about blind review for a given case.

<a id="opIdget-blind-review-info"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /blindreview/{jurisdictionId}/{caseId} \
  -H 'Accept: application/json'

```

```http
GET /blindreview/{jurisdictionId}/{caseId} HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/blindreview/{jurisdictionId}/{caseId}',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/blindreview/{jurisdictionId}/{caseId}',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/blindreview/{jurisdictionId}/{caseId}', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/blindreview/{jurisdictionId}/{caseId}', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/blindreview/{jurisdictionId}/{caseId}");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/blindreview/{jurisdictionId}/{caseId}", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /blindreview/{jurisdictionId}/{caseId}`

This endpoint provides information about the blind review process for the given case.

The payload will indicate whether blind review is required for this case.

If blind review is required, this endpoint will also provide a list of redacted documents to present for review.

<h3 id="get-information-about-blind-review-for-a-given-case.-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|jurisdictionId|path|string|true|The jurisdiction ID|
|caseId|path|string|true|The case ID|
|defendantId|query|string|false|Optionally, a specific defendant ID to filter by|

> Example responses

> 200 Response

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "blindReviewRequired": true,
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "redactedDocuments": [
    {
      "attachmentType": "LINK",
      "documentId": "string",
      "url": "http://example.com"
    }
  ]
}
```

<h3 id="get-information-about-blind-review-for-a-given-case.-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|OK|[BlindReviewInfo](#schemablindreviewinfo)|
|424|[Failed Dependency](https://tools.ietf.org/html/rfc2518#section-10.5)|Documents are not processed yet|[Error](#schemaerror)|

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="blind-charging-api-experiments">experiments</h1>

Operations related to research experiments.

## Log an exposure event

<a id="opIdlog-exposure"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /exposure \
  -H 'Content-Type: application/json'

```

```http
POST /exposure HTTP/1.1

Content-Type: application/json

```

```javascript
const inputBody = '{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "protocol": "BLIND_REVIEW"
}';
const headers = {
  'Content-Type':'application/json'
};

fetch('/exposure',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json'
}

result = RestClient.post '/exposure',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json'
}

r = requests.post('/exposure', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/exposure', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/exposure");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/exposure", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /exposure`

This endpoint records which information is presented to attorneys and when, prior to them making a decision.

Sending "exposure" events is required for all cases involved in research experiments, _both for blind review and also final review_.

> Body parameter

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "protocol": "BLIND_REVIEW"
}
```

<h3 id="log-an-exposure-event-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[Exposure](#schemaexposure)|true|none|

<h3 id="log-an-exposure-event-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Accepted|None|

<aside class="success">
This operation does not require authentication
</aside>

## Log an outcome event

<a id="opIdlog-outcome"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /outcome \
  -H 'Content-Type: application/json'

```

```http
POST /outcome HTTP/1.1

Content-Type: application/json

```

```javascript
const inputBody = '{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "decision": {
    "protocol": "BLIND_REVIEW",
    "outcome": {
      "chargingDecision": "CHARGE_LIKELY",
      "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
      "additionalEvidence": "The defendant has a history of theft."
    }
  },
  "timestamps": {
    "pageOpen": "2019-08-24T14:15:22Z",
    "decision": "2019-08-24T14:15:22Z"
  }
}';
const headers = {
  'Content-Type':'application/json'
};

fetch('/outcome',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json'
}

result = RestClient.post '/outcome',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json'
}

r = requests.post('/outcome', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/outcome', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/outcome");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/outcome", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /outcome`

This endpoint records the charging decisions made by attorneys, both for blind review and final review.

Sending "outcome" events is required for all cases involved in research experiments, _regardless of whether the case is subject to blind review or not_.

> Body parameter

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "decision": {
    "protocol": "BLIND_REVIEW",
    "outcome": {
      "chargingDecision": "CHARGE_LIKELY",
      "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
      "additionalEvidence": "The defendant has a history of theft."
    }
  },
  "timestamps": {
    "pageOpen": "2019-08-24T14:15:22Z",
    "decision": "2019-08-24T14:15:22Z"
  }
}
```

<h3 id="log-an-outcome-event-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[Review](#schemareview)|true|none|

<h3 id="log-an-outcome-event-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Accepted|None|

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="blind-charging-api-operations">operations</h1>

Operations related to the overall operation of the API.

## Health check

<a id="opIdhealth-check"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /health \
  -H 'Accept: application/json'

```

```http
GET /health HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/health',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/health',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/health', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/health', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/health");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/health", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /health`

Check the health of the API.

> Example responses

> 200 Response

```json
{
  "detail": "string"
}
```

<h3 id="health-check-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|OK|[APIStatus](#schemaapistatus)|
|500|[Internal Server Error](https://tools.ietf.org/html/rfc7231#section-6.6.1)|Not OK|[APIStatus](#schemaapistatus)|

<aside class="success">
This operation does not require authentication
</aside>

# Schemas

<h2 id="tocS_Error">Error</h2>
<!-- backwards compatibility -->
<a id="schemaerror"></a>
<a id="schema_Error"></a>
<a id="tocSerror"></a>
<a id="tocserror"></a>

```json
{
  "message": "string"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|message|string|true|none|none|

<h2 id="tocS_DocumentLink">DocumentLink</h2>
<!-- backwards compatibility -->
<a id="schemadocumentlink"></a>
<a id="schema_DocumentLink"></a>
<a id="tocSdocumentlink"></a>
<a id="tocsdocumentlink"></a>

```json
{
  "attachmentType": "LINK",
  "documentId": "string",
  "url": "http://example.com"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|attachmentType|string|true|none|none|
|documentId|string|true|none|none|
|url|string(uri)|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|attachmentType|LINK|

<h2 id="tocS_DocumentText">DocumentText</h2>
<!-- backwards compatibility -->
<a id="schemadocumenttext"></a>
<a id="schema_DocumentText"></a>
<a id="tocSdocumenttext"></a>
<a id="tocsdocumenttext"></a>

```json
{
  "attachmentType": "TEXT",
  "documentId": "string",
  "content": "string"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|attachmentType|string|true|none|none|
|documentId|string|true|none|none|
|content|string|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|attachmentType|TEXT|

<h2 id="tocS_BlindReviewInfo">BlindReviewInfo</h2>
<!-- backwards compatibility -->
<a id="schemablindreviewinfo"></a>
<a id="schema_BlindReviewInfo"></a>
<a id="tocSblindreviewinfo"></a>
<a id="tocsblindreviewinfo"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "blindReviewRequired": true,
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "redactedDocuments": [
    {
      "attachmentType": "LINK",
      "documentId": "string",
      "url": "http://example.com"
    }
  ]
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|blindReviewRequired|boolean|true|none|none|
|maskedDefendants|[[MaskedDefendant](#schemamaskeddefendant)]|true|none|[Mapping between a defendant's ID to their alias.]|
|redactedDocuments|[[DocumentLink](#schemadocumentlink)]|true|none|none|

<h2 id="tocS_RedactionResultSuccess">RedactionResultSuccess</h2>
<!-- backwards compatibility -->
<a id="schemaredactionresultsuccess"></a>
<a id="schema_RedactionResultSuccess"></a>
<a id="tocSredactionresultsuccess"></a>
<a id="tocsredactionresultsuccess"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "redactedDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "COMPLETE"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|maskedDefendants|[[MaskedDefendant](#schemamaskeddefendant)]|true|none|[Mapping between a defendant's ID to their alias.]|
|inputDocument|[DocumentLink](#schemadocumentlink)|true|none|none|
|redactedDocument|[DocumentLink](#schemadocumentlink)|true|none|none|
|status|string|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|status|COMPLETE|

<h2 id="tocS_RedactionResultError">RedactionResultError</h2>
<!-- backwards compatibility -->
<a id="schemaredactionresulterror"></a>
<a id="schema_RedactionResultError"></a>
<a id="tocSredactionresulterror"></a>
<a id="tocsredactionresulterror"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "error": "string",
  "status": "ERROR"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|maskedDefendants|[[MaskedDefendant](#schemamaskeddefendant)]|true|none|[Mapping between a defendant's ID to their alias.]|
|inputDocument|[DocumentLink](#schemadocumentlink)|true|none|none|
|error|string|true|none|none|
|status|string|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|status|ERROR|

<h2 id="tocS_RedactionResultPending">RedactionResultPending</h2>
<!-- backwards compatibility -->
<a id="schemaredactionresultpending"></a>
<a id="schema_RedactionResultPending"></a>
<a id="tocSredactionresultpending"></a>
<a id="tocsredactionresultpending"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "QUEUED"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|maskedDefendants|[[MaskedDefendant](#schemamaskeddefendant)]|true|none|[Mapping between a defendant's ID to their alias.]|
|inputDocument|[DocumentLink](#schemadocumentlink)|true|none|none|
|status|string|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|status|QUEUED|
|status|PROCESSING|

<h2 id="tocS_RedactionResultCompleted">RedactionResultCompleted</h2>
<!-- backwards compatibility -->
<a id="schemaredactionresultcompleted"></a>
<a id="schema_RedactionResultCompleted"></a>
<a id="tocSredactionresultcompleted"></a>
<a id="tocsredactionresultcompleted"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "redactedDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "COMPLETE"
}

```

A completed redaction job. Similar to `RedactionResult`,
but where it is not possible to see a result in an incomplete (pending or queued) state.

### Properties

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[RedactionResultSuccess](#schemaredactionresultsuccess)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[RedactionResultError](#schemaredactionresulterror)|false|none|none|

<h2 id="tocS_RedactionResult">RedactionResult</h2>
<!-- backwards compatibility -->
<a id="schemaredactionresult"></a>
<a id="schema_RedactionResult"></a>
<a id="tocSredactionresult"></a>
<a id="tocsredactionresult"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "maskedDefendants": [
    {
      "defendantId": "string",
      "alias": "string"
    }
  ],
  "inputDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "redactedDocument": {
    "attachmentType": "LINK",
    "documentId": "string",
    "url": "http://example.com"
  },
  "status": "COMPLETE"
}

```

Information about a redaction job.

### Properties

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[RedactionResultSuccess](#schemaredactionresultsuccess)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[RedactionResultError](#schemaredactionresulterror)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[RedactionResultPending](#schemaredactionresultpending)|false|none|none|

<h2 id="tocS_RedactionStatus">RedactionStatus</h2>
<!-- backwards compatibility -->
<a id="schemaredactionstatus"></a>
<a id="schema_RedactionStatus"></a>
<a id="tocSredactionstatus"></a>
<a id="tocsredactionstatus"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "requests": [
    {
      "jurisdictionId": "string",
      "caseId": "string",
      "maskedDefendants": [
        {
          "defendantId": "string",
          "alias": "string"
        }
      ],
      "inputDocument": {
        "attachmentType": "LINK",
        "documentId": "string",
        "url": "http://example.com"
      },
      "redactedDocument": {
        "attachmentType": "LINK",
        "documentId": "string",
        "url": "http://example.com"
      },
      "status": "COMPLETE"
    }
  ]
}

```

The status of redaction for a case.

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|requests|[[RedactionResult](#schemaredactionresult)]|true|none|[Information about a redaction job.<br>]|

<h2 id="tocS_HumanName">HumanName</h2>
<!-- backwards compatibility -->
<a id="schemahumanname"></a>
<a id="schema_HumanName"></a>
<a id="tocShumanname"></a>
<a id="tocshumanname"></a>

```json
{
  "firstName": "string",
  "lastName": "string",
  "middleName": "string",
  "suffix": "string"
}

```

A structured representation of someone's name.

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|firstName|string|true|none|none|
|lastName|string|false|none|none|
|middleName|string|false|none|none|
|suffix|string|false|none|none|

<h2 id="tocS_MaskedDefendant">MaskedDefendant</h2>
<!-- backwards compatibility -->
<a id="schemamaskeddefendant"></a>
<a id="schema_MaskedDefendant"></a>
<a id="tocSmaskeddefendant"></a>
<a id="tocsmaskeddefendant"></a>

```json
{
  "defendantId": "string",
  "alias": "string"
}

```

Mapping between a defendant's ID to their alias.

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|defendantId|string|true|none|none|
|alias|string|true|none|none|

<h2 id="tocS_Defendant">Defendant</h2>
<!-- backwards compatibility -->
<a id="schemadefendant"></a>
<a id="schema_Defendant"></a>
<a id="tocSdefendant"></a>
<a id="tocsdefendant"></a>

```json
{
  "defendantId": "string",
  "name": "string",
  "aliases": [
    "string"
  ]
}

```

Mapping between a defendant's ID to their name(s).

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|defendantId|string|true|none|none|
|name|any|true|none|none|

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[HumanName](#schemahumanname)|false|none|A structured representation of someone's name.|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|aliases|[oneOf]|false|none|none|

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[HumanName](#schemahumanname)|false|none|A structured representation of someone's name.|

<h2 id="tocS_RedactionRequest">RedactionRequest</h2>
<!-- backwards compatibility -->
<a id="schemaredactionrequest"></a>
<a id="schema_RedactionRequest"></a>
<a id="tocSredactionrequest"></a>
<a id="tocsredactionrequest"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendants": [
    {
      "defendantId": "string",
      "name": "string",
      "aliases": [
        "string"
      ]
    }
  ],
  "documents": [
    {
      "attachmentType": "LINK",
      "documentId": "string",
      "url": "http://example.com"
    }
  ],
  "callbackUrl": "http://example.com"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|defendants|[[Defendant](#schemadefendant)]|true|none|[Mapping between a defendant's ID to their name(s).]|
|documents|[oneOf]|true|none|none|

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[DocumentLink](#schemadocumentlink)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[DocumentText](#schemadocumenttext)|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|callbackUrl|string(uri)|true|none|none|

<h2 id="tocS_ReviewTimestamps">ReviewTimestamps</h2>
<!-- backwards compatibility -->
<a id="schemareviewtimestamps"></a>
<a id="schema_ReviewTimestamps"></a>
<a id="tocSreviewtimestamps"></a>
<a id="tocsreviewtimestamps"></a>

```json
{
  "pageOpen": "2019-08-24T14:15:22Z",
  "decision": "2019-08-24T14:15:22Z"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|pageOpen|string(date-time)|true|none|none|
|decision|string(date-time)|true|none|none|

<h2 id="tocS_FinalChargeOutcome">FinalChargeOutcome</h2>
<!-- backwards compatibility -->
<a id="schemafinalchargeoutcome"></a>
<a id="schema_FinalChargeOutcome"></a>
<a id="tocSfinalchargeoutcome"></a>
<a id="tocsfinalchargeoutcome"></a>

```json
{
  "chargingDecision": "CHARGE",
  "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods."
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|chargingDecision|string|true|none|The final charging decision.|
|chargingDecisionExplanation|string|false|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|chargingDecision|CHARGE|
|chargingDecision|DECLINE|

<h2 id="tocS_BlindChargeOutcome">BlindChargeOutcome</h2>
<!-- backwards compatibility -->
<a id="schemablindchargeoutcome"></a>
<a id="schema_BlindChargeOutcome"></a>
<a id="tocSblindchargeoutcome"></a>
<a id="tocsblindchargeoutcome"></a>

```json
{
  "chargingDecision": "CHARGE_LIKELY",
  "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
  "additionalEvidence": "The defendant has a history of theft."
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|chargingDecision|string|true|none|none|
|chargingDecisionExplanation|string|true|none|none|
|additionalEvidence|string|false|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|chargingDecision|CHARGE_LIKELY|
|chargingDecision|CHARGE_MAYBE|
|chargingDecision|DECLINE_MAYBE|
|chargingDecision|DECLINE_LIKELY|

<h2 id="tocS_DisqualifyOutcome">DisqualifyOutcome</h2>
<!-- backwards compatibility -->
<a id="schemadisqualifyoutcome"></a>
<a id="schema_DisqualifyOutcome"></a>
<a id="tocSdisqualifyoutcome"></a>
<a id="tocsdisqualifyoutcome"></a>

```json
{
  "outcomeType": "DISQUALIFY",
  "disqualifyingReason": "CASE_TYPE_INELIGIBLE",
  "disqualifyingReasonExplanation": "I have prior knowledge of the individuals involved in this case."
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|outcomeType|string|true|none|none|
|disqualifyingReason|string|true|none|none|
|disqualifyingReasonExplanation|string|false|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|outcomeType|DISQUALIFY|
|disqualifyingReason|ASSIGNED_TO_UNBLIND|
|disqualifyingReason|CASE_TYPE_INELIGIBLE|
|disqualifyingReason|PRIOR_KNOWLEDGE_BIAS|
|disqualifyingReason|NARRATIVE_INCOMPLETE|
|disqualifyingReason|REDACTION_MISSING|
|disqualifyingReason|REDACTION_ILLEGIBLE|
|disqualifyingReason|OTHER|

<h2 id="tocS_ReviewProtocol">ReviewProtocol</h2>
<!-- backwards compatibility -->
<a id="schemareviewprotocol"></a>
<a id="schema_ReviewProtocol"></a>
<a id="tocSreviewprotocol"></a>
<a id="tocsreviewprotocol"></a>

```json
"BLIND_REVIEW"

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|string|false|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|*anonymous*|BLIND_REVIEW|
|*anonymous*|FINAL_REVIEW|

<h2 id="tocS_BlindReviewDecision">BlindReviewDecision</h2>
<!-- backwards compatibility -->
<a id="schemablindreviewdecision"></a>
<a id="schema_BlindReviewDecision"></a>
<a id="tocSblindreviewdecision"></a>
<a id="tocsblindreviewdecision"></a>

```json
{
  "protocol": "BLIND_REVIEW",
  "outcome": {
    "chargingDecision": "CHARGE_LIKELY",
    "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
    "additionalEvidence": "The defendant has a history of theft."
  }
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|protocol|string|true|none|none|
|outcome|any|true|none|none|

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[BlindChargeOutcome](#schemablindchargeoutcome)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[DisqualifyOutcome](#schemadisqualifyoutcome)|false|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|protocol|BLIND_REVIEW|

<h2 id="tocS_FinalReviewDecision">FinalReviewDecision</h2>
<!-- backwards compatibility -->
<a id="schemafinalreviewdecision"></a>
<a id="schema_FinalReviewDecision"></a>
<a id="tocSfinalreviewdecision"></a>
<a id="tocsfinalreviewdecision"></a>

```json
{
  "protocol": "FINAL_REVIEW",
  "outcome": {
    "chargingDecision": "CHARGE",
    "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods."
  }
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|protocol|string|true|none|none|
|outcome|[FinalChargeOutcome](#schemafinalchargeoutcome)|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|protocol|FINAL_REVIEW|

<h2 id="tocS_ReviewDecision">ReviewDecision</h2>
<!-- backwards compatibility -->
<a id="schemareviewdecision"></a>
<a id="schema_ReviewDecision"></a>
<a id="tocSreviewdecision"></a>
<a id="tocsreviewdecision"></a>

```json
{
  "protocol": "BLIND_REVIEW",
  "outcome": {
    "chargingDecision": "CHARGE_LIKELY",
    "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
    "additionalEvidence": "The defendant has a history of theft."
  }
}

```

### Properties

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[BlindReviewDecision](#schemablindreviewdecision)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|[FinalReviewDecision](#schemafinalreviewdecision)|false|none|none|

<h2 id="tocS_Exposure">Exposure</h2>
<!-- backwards compatibility -->
<a id="schemaexposure"></a>
<a id="schema_Exposure"></a>
<a id="tocSexposure"></a>
<a id="tocsexposure"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "protocol": "BLIND_REVIEW"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|defendantId|string|true|none|none|
|reviewingAttorneyUserId|string|true|none|none|
|documentIds|[string]|true|none|none|
|protocol|[ReviewProtocol](#schemareviewprotocol)|true|none|none|

<h2 id="tocS_Review">Review</h2>
<!-- backwards compatibility -->
<a id="schemareview"></a>
<a id="schema_Review"></a>
<a id="tocSreview"></a>
<a id="tocsreview"></a>

```json
{
  "jurisdictionId": "string",
  "caseId": "string",
  "defendantId": "string",
  "reviewingAttorneyUserId": "string",
  "documentIds": [
    "string"
  ],
  "decision": {
    "protocol": "BLIND_REVIEW",
    "outcome": {
      "chargingDecision": "CHARGE_LIKELY",
      "chargingDecisionExplanation": "The defendant was caught on camera with the stolen goods.",
      "additionalEvidence": "The defendant has a history of theft."
    }
  },
  "timestamps": {
    "pageOpen": "2019-08-24T14:15:22Z",
    "decision": "2019-08-24T14:15:22Z"
  }
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|jurisdictionId|string|true|none|none|
|caseId|string|true|none|none|
|defendantId|string|true|none|none|
|reviewingAttorneyUserId|string|true|none|none|
|documentIds|[string]|true|none|none|
|decision|[ReviewDecision](#schemareviewdecision)|true|none|none|
|timestamps|[ReviewTimestamps](#schemareviewtimestamps)|true|none|none|

<h2 id="tocS_APIStatus">APIStatus</h2>
<!-- backwards compatibility -->
<a id="schemaapistatus"></a>
<a id="schema_APIStatus"></a>
<a id="tocSapistatus"></a>
<a id="tocsapistatus"></a>

```json
{
  "detail": "string"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|detail|string|true|none|none|
