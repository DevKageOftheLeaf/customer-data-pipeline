# Confluence REST API Documentation for Knowledge Transition

## Overview
This document provides end-to-end guidance for using Confluence REST APIs to facilitate knowledge transition (migration, synchronization, or integration) between Confluence instances or with other systems. Focuses on Confluence Cloud REST API v2.

## Authentication
Confluence Cloud uses API token-based authentication:

### Generating API Token
1. Log in to Atlassian account
2. Go to Security → API tokens → Create API token
3. Copy the generated token (only shown once)

### Authentication Header
```
Authorization: Basic <base64-encoded email:api_token>
```
Or using curl:
```bash
curl -u "email@example.com:your_api_token" https://your-domain.atlassian.net/wiki/rest/api/...
```

## Key API Endpoints for Knowledge Transition

### 1. Space Operations
- **Get all spaces**: `GET /wiki/rest/api/space`
- **Get space details**: `GET /wiki/rest/api/space/{spaceKey}`
- **Get space content**: `GET /wiki/rest/api/space/{spaceKey}/content`

### 2. Content Operations (Pages, Blog Posts)
- **Get content**: `GET /wiki/rest/api/content/{id}`
- **Search content**: `GET /wiki/rest/api/content?title=~"search term"&spaceKey=KEY&type=page`
- **Create content**: `POST /wiki/rest/api/content`
- **Update content**: `PUT /wiki/rest/api/content/{id}`
- **Delete content**: `DELETE /wiki/rest/api/content/{id}`

### 3. Attachment Operations
- **Get attachments**: `GET /wiki/rest/api/content/{id}/child/attachment`
- **Upload attachment**: `POST /wiki/rest/api/content/{id}/child/attachment`
- **Download attachment**: `GET /wiki/rest/api/content/{id}/child/attachment/{attachmentId}/download`

### 4. Label Operations
- **Get labels**: `GET /wiki/rest/api/content/{id}/label`
- **Add label**: `POST /wiki/rest/api/content/{id}/label`
- **Remove label**: `DELETE /wiki/rest/api/content/{id}/label/{labelName}`

### 5. Version Operations
- **Get versions**: `GET /wiki/rest/api/content/{id}/version`
- **Restore version**: `POST /wiki/rest/api/content/{id}/version/{versionNumber}/restore`

## End-to-End Knowledge Transition Workflow

### Phase 1: Discovery & Planning
1. Identify source spaces and content types
2. Map space hierarchies and permissions
3. Inventory attachments and labels
4. Determine migration strategy (full export vs incremental)

### Phase 2: Data Extraction (Source Instance)
```bash
# Get all spaces
curl -u "email:token" "https://source.atlassian.net/wiki/rest/api/space?limit=100"

# For each space, get all content
curl -u "email:token" "https://source.atlassian.net/wiki/rest/api/content?spaceKey=SPACEKEY&type=page&limit=100&expand=body.storage,version,metadata.labels"

# Get attachments for each content item
curl -u "email:token" "https://source.atlassian.net/wiki/rest/api/content/{contentId}/child/attachment"
```

### Phase 3: Data Transformation
- Convert storage format if needed (Confluence storage format to target format)
- Map user mentions and links
- Handle space key differences
- Preserve version history if required

### Phase 4: Data Loading (Target Instance)
```bash
# Create space if needed
curl -u "email:token" -X POST "https://target.atlassian.net/wiki/rest/api/space" \
  -H "Content-Type: application/json" \
  -d '{"key":"NEWSPACE","name":"Migrated Space","description":{"plain":{"value":"Migrated from source"}}}'

# Create page
curl -u "email:token" -X POST "https://target.atlassian.net/wiki/rest/api/content" \
  -H "Content-Type: application/json" \
  -d '{
    "type":"page",
    "title":"Migrated Page",
    "space":{"key":"NEWSPACE"},
    "body":{"storage":{"value":"<p>Content here</p>","representation":"storage"}}
  }'

# Add attachment
curl -u "email:token" -X POST "https://target.atlassian.net/wiki/rest/api/content/{pageId}/child/attachment" \
  -H "X-Atlassian-Token: no-check" \
  -F "file=@localfile.pdf"

# Add labels
curl -u "email:token" -X POST "https://target.atlassian.net/wiki/rest/api/content/{pageId}/label" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"global","name":"migrated"}'
```

## Important Considerations

### Pagination
All list endpoints use pagination:
- Default limit: 25 items
- Maximum limit: 100 items (use `limit=100`)
- Use `_start` parameter or `next` links in response for pagination

### Expansions
Minimize bandwidth by requesting only needed fields:
```
&expand=body.storage,version,metadata.labels,space
```

### Rate Limits
- Confluence Cloud: 100 requests per 10 seconds per user
- Implement exponential backoff for 429 responses
- Consider batching operations where possible

### Error Handling
Common HTTP status codes:
- 200: Success
- 201: Created
- 204: No Content (successful delete)
- 400: Bad Request (validation error)
- 401: Unauthorized (auth issue)
- 403: Forbidden (permission issue)
- 404: Not Found
- 409: Conflict (version mismatch)
- 429: Too Many Requests (rate limit)
- 500: Internal Server Error

### Attachment Handling
- Attachments are binary; use multipart/form-data for upload
- Preserve original filenames and MIME types
- Consider attachment size limits (typically 100MB)

### Permissions
- API token must have appropriate permissions in both source and target
- Space admin permissions needed for space creation
- Content permissions needed for read/write operations

## Sample Migration Script Outline (Python)
```python
import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
SOURCE_INSTANCE = "https://source.atlassian.net"
TARGET_INSTANCE = "https://target.atlassian.net"
EMAIL = "user@example.com"
API_TOKEN = "your_api_token"
SOURCE_SPACE_KEY = "SOURCE"
TARGET_SPACE_KEY = "TARGET"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

def get_all_pages(space_key):
    """Retrieve all pages from a space with pagination"""
    pages = []
    start = 0
    limit = 100
    
    while True:
        url = f"{SOURCE_INSTANCE}/wiki/rest/api/content?spaceKey={space_key}&type=page&limit={limit}&start={start}&expand=body.storage,version,metadata.labels"
        response = requests.get(url, auth=auth, headers=headers)
        data = response.json()
        
        pages.extend(data['results'])
        
        if '_links' in data and 'next' in data['_links']:
            start += limit
        else:
            break
            
    return pages

def migrate_page(page_data):
    """Migrate a single page to target instance"""
    # Prepare payload for target
    payload = {
        "type": "page",
        "title": page_data['title'],
        "space": {"key": TARGET_SPACE_KEY},
        "body": {
            "storage": {
                "value": page_data['body']['storage']['value'],
                "representation": "storage"
            }
        }
    }
    
    # Create page in target
    url = f"{TARGET_INSTANCE}/wiki/rest/api/content"
    response = requests.post(url, auth=auth, headers={**headers, "Content-Type": "application/json"}, json=payload)
    
    if response.status_code == 201:
        new_page = response.json()
        page_id = new_page['id']
        
        # Migrate labels
        for label in page_data.get('metadata', {}).get('labels', {}).get('results', []):
            label_url = f"{TARGET_INSTANCE}/wiki/rest/api/content/{page_id}/label"
            requests.post(label_url, auth=auth, headers=headers, 
                         json={"prefix": "global", "name": label['name']})
        
        return page_id
    else:
        print(f"Failed to create page: {response.status_code} - {response.text}")
        return None

# Main migration process
if __name__ == "__main__":
    print("Fetching pages from source space...")
    pages = get_all_pages(SOURCE_SPACE_KEY)
    print(f"Found {len(pages)} pages to migrate")
    
    for i, page in enumerate(pages):
        print(f"Migrating page {i+1}/{len(pages)}: {page['title']}")
        new_page_id = migrate_page(page)
        if new_page_id:
            print(f"  -> Created as page ID: {new_page_id}")
```

## Best Practices for Knowledge Transition

1. **Test in Staging**: Always test migration procedures in a non-production environment first
2. **Incremental Migration**: For large spaces, migrate in batches with verification steps
3. **Preserve Metadata**: Maintain labels, attachments, and version history when required
4. **Handle Links Carefully**: Update internal links to point to new locations in target instance
5. **Document Changes**: Keep detailed logs of what was migrated and any transformations applied
6. **Verify Integrity**: After migration, compare content counts and spot-check key pages
7. **Consider Timing**: Perform migrations during low-usage periods to minimize disruption
8. **Backup First**: Ensure both source and target instances have recent backups before starting

## Common Challenges and Solutions

### Challenge: Broken Links After Migration
**Solution**: 
- Use page IDs instead of titles in links when possible
- Implement a link mapping table during migration
- Run a post-migration link checker script

### Challenge: Large Attachments
**Solution**:
- Chunk large file uploads if needed
- Consider external storage for very large attachments
- Notify users about size limits in advance

### Challenge: Permission Mapping
**Solution**:
- Map source groups/users to target equivalents
- Use bulk permission APIs where available
- Document permission changes for user communication

### Challenge: Version History Preservation
**Solution**:
- For critical documents, migrate as separate versions
- Use the version endpoint to restore historical versions
- Note that perfect version history migration may require app-based solutions

## References
- Confluence Cloud REST API v2 Documentation: https://developer.atlassian.com/cloud/confluence/rest/v2/
- API Rate Limits: https://developer.atlassian.com/cloud/confluence/rate-limets/
- Authentication Guide: https://developer.atlassian.com/cloud/conference/authentication/
- Storage Format Guide: https://developer.atlassian.com/cloud/confluence/storage-format/

---
*Documentation generated for knowledge transition projects using Confluence APIs*