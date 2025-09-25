
# Prompt Parsing System API

**Version:** 1.0.0  
**Description:** API with required EndPoints - Structured

All endpoints require an API key in the header:

```bash
X-API-KEY: YOUR\_API\_KEY
```

---

## LLM Endpoints

### 1. Extract Brand Mentions
- **Method:** GET  
- **Endpoint:** /api/llm/extract-brand-info  
- **Description:** Extract brand mentions from a prompt.  
- **Query Parameters:**
  - `prompt_id` (string, required): Prompt ID
  - `s3_key` (string, required): S3 Key of the content
- **Responses:**
  - 200: Successful Response
  - 404: Not Found
  - 422: Validation Error

**Example cURL:**
```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/llm/extract-brand-info?prompt_id=123&s3_key=myfile.json"
````

---

### 2. Get Process Status

* **Method:** GET
* **Endpoint:** /api/llm/get-process-status
* **Description:** Returns the status of a running process.
* **Query Parameters:**

  * `prompt_id` (string, required): Prompt ID
  * `process_id` (string, required): Process ID
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/llm/get-process-status?prompt_id=123&process_id=456"
```

---

## Logs Endpoints

### 3. Get Logs

* **Method:** GET
* **Endpoint:** /api/logs/{prompt\_id}
* **Description:** Retrieve logs for a specific prompt.
* **Path Parameters:**

  * `prompt_id` (string, required): Prompt ID
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/logs/123"
```

---

## Metrics Endpoints (Frontend Endpoints)

### 4. Get Brand Mentions

* **Method:** GET
* **Endpoint:** /api/metrics/brand-mentions
* **Description:** Retrieve mentions of a specific brand.
* **Query Parameters:**

  * `prompt_id` (string, required)
  * `brand` (string, required)
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/metrics/brand-mentions?prompt_id=123&brand=Nike"
```

---

### 5. Get Brand Share of Voice

* **Method:** GET
* **Endpoint:** /api/metrics/brand-share-of-voice
* **Description:** Returns the share of voice for a brand.
* **Query Parameters:** Same as Brand Mentions
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/metrics/brand-share-of-voice?prompt_id=123&brand=Nike"
```

---

### 6. Get Brand Coverage

* **Method:** GET
* **Endpoint:** /api/metrics/brand-coverage
* **Description:** Returns the coverage of a brand.
* **Query Parameters:** Same as Brand Mentions
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/metrics/brand-coverage?prompt_id=123&brand=Nike"
```

---

### 7. Get Brand Position

* **Method:** GET
* **Endpoint:** /api/metrics/brand-position
* **Description:** Returns the position of a brand.
* **Query Parameters:** Same as Brand Mentions
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/metrics/brand-position?prompt_id=123&brand=Nike"
```

---

### 8. Get Brand Ranking

* **Method:** GET
* **Endpoint:** /api/metrics/metrics/brand-ranking
* **Description:** Returns the ranking of brands for a prompt.
* **Query Parameters:**

  * `prompt_id` (string, required)
* **Responses:** Same as above

**Example cURL:**

```bash
curl -H "X-API-KEY: YOUR_API_KEY" \
"https://your-api-domain.com/api/metrics/metrics/brand-ranking?prompt_id=123"
```

---

## Error Model

### HTTPValidationError

```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

