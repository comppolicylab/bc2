# RedactionApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getRedactionStatus**](RedactionApi.md#getRedactionStatus) | **GET** /redact/{jurisdictionId}/{caseId} | Get status of document redaction for a case. |
| [**redactDocument**](RedactionApi.md#redactDocument) | **POST** /redact | Redact a document |


<a name="getRedactionStatus"></a>
# **getRedactionStatus**
> RedactionStatus getRedactionStatus(jurisdictionId, caseId, defendantId)

Get status of document redaction for a case.

    Get the status of redaction for all documents in a case. This will return a list of document IDs and their redaction status.  Generally, the push mechanism provided by the callback URL passed to the &#x60;/redact&#x60; endpoint should be used to determine when the redaction process is completed. However, this endpoint can be used to poll for the status of redaction if necessary.

### Parameters

|Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **jurisdictionId** | **String**| The jurisdiction ID | [default to null] |
| **caseId** | **String**| The case ID | [default to null] |
| **defendantId** | **String**| Optionally, filter status by a specific defendant. | [optional] [default to null] |

### Return type

[**RedactionStatus**](../Models/RedactionStatus.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

<a name="redactDocument"></a>
# **redactDocument**
> redactDocument(RedactionRequest)

Redact a document

    Submit a document for redaction. Redaction happens asynchronously and may take some time. When finished, the redacted document will be posted to the provided callback URL.  A callback will be POSTed to the provided URL when the redaction process is completed for each input document. The callback will contain either &#x60;RedactionResultSuccess&#x60; or &#x60;RedactionResultError&#x60;.

### Parameters

|Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **RedactionRequest** | [**RedactionRequest**](../Models/RedactionRequest.md)|  | |

### Return type

null (empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined
