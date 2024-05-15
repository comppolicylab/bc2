# ExperimentsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**logExposure**](ExperimentsApi.md#logExposure) | **POST** /exposure | Log an exposure event |
| [**logOutcome**](ExperimentsApi.md#logOutcome) | **POST** /outcome | Log an outcome event |


<a name="logExposure"></a>
# **logExposure**
> logExposure(Exposure)

Log an exposure event

    This endpoint records which information is presented to attorneys and when, prior to them making a decision.  Sending \&quot;exposure\&quot; events is required for all cases involved in research experiments, _both for blind review and also final review_.

### Parameters

|Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **Exposure** | [**Exposure**](../Models/Exposure.md)|  | |

### Return type

null (empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

<a name="logOutcome"></a>
# **logOutcome**
> logOutcome(Review)

Log an outcome event

    This endpoint records the charging decisions made by attorneys, both for blind review and final review.  Sending \&quot;outcome\&quot; events is required for all cases involved in research experiments, _regardless of whether the case is subject to blind review or not_.

### Parameters

|Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **Review** | [**Review**](../Models/Review.md)|  | |

### Return type

null (empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined
