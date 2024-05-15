# ReviewApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getBlindReviewInfo**](ReviewApi.md#getBlindReviewInfo) | **GET** /blindreview/{jurisdictionId}/{caseId} | Get information about blind review for a given case. |


<a name="getBlindReviewInfo"></a>
# **getBlindReviewInfo**
> BlindReviewInfo getBlindReviewInfo(jurisdictionId, caseId, defendantId)

Get information about blind review for a given case.

    This endpoint provides information about the blind review process for the given case.  The payload will indicate whether blind review is required for this case.  If blind review is required, this endpoint will also provide a list of redacted documents to present for review.

### Parameters

|Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **jurisdictionId** | **String**| The jurisdiction ID | [default to null] |
| **caseId** | **String**| The case ID | [default to null] |
| **defendantId** | **String**| Optionally, a specific defendant ID to filter by | [optional] [default to null] |

### Return type

[**BlindReviewInfo**](../Models/BlindReviewInfo.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json
