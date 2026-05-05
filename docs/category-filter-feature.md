# Category Filter Feature

## Overview
A simple category filtering system has been added to the Purchase Requisition endpoints. Categories are automatically extracted from item names, so no additional database schema changes are required.

## How It Works

### Category Extraction
Categories are extracted from `item_name` fields by:
1. Splitting item names by spaces, hyphens, and underscores
2. Extracting unique keywords (words longer than 2 characters)
3. Returning them as potential categories

**Example:**
- Item name: "Laptop Dell XPS 15"
- Extracted categories: ["dell", "laptop", "xps"]

- Item name: "Printer_HP_LaserJet"
- Extracted categories: ["hp", "laserjet", "printer"]

## API Endpoints

### 1. Get Available Categories

#### For Requesters
```
GET /api/v1/requisitions/categories
```
Returns categories from the current user's PRs only.

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "categories": ["dell", "keyboard", "laptop", "monitor", "mouse"]
  }
}
```

#### For Admins
```
GET /api/v1/requisitions/admin/categories
```
Returns categories from all PRs in the system.

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "categories": ["dell", "hp", "keyboard", "laptop", "monitor", "mouse", "printer"]
  }
}
```

### 2. Filter PRs by Category

#### For Requesters
```
GET /api/v1/requisitions?category=laptop
```
Returns PRs that contain line items with "laptop" in the item name (case-insensitive).

**Query Parameters:**
- `category` (optional): Keyword to search in item names
- `status` (optional): Filter by PR status
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Examples:**
```
GET /api/v1/requisitions?category=laptop
GET /api/v1/requisitions?category=dell&status=APPROVED
GET /api/v1/requisitions?category=printer&page=2&per_page=20
```

#### For Admins
```
GET /api/v1/requisitions/admin?category=laptop
```
Returns all PRs that contain line items with "laptop" in the item name.

**Query Parameters:**
- `category` (optional): Keyword to search in item names
- `status` (optional): Filter by PR status
- `requester_id` (optional): Filter by requester ID
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Examples:**
```
GET /api/v1/requisitions/admin?category=laptop
GET /api/v1/requisitions/admin?category=hp&status=SUBMITTED
GET /api/v1/requisitions/admin?category=monitor&requester_id=5
```

## Usage Examples

### Frontend Integration

#### 1. Fetch Available Categories
```typescript
// In requester view
const response = await api.get('/requisitions/categories');
const categories = response.data.data.categories;

// In admin view
const response = await api.get('/requisitions/admin/categories');
const categories = response.data.data.categories;
```

#### 2. Filter PRs by Category
```typescript
// Filter requester's PRs by category
const response = await api.get('/requisitions', {
  params: {
    category: 'laptop',
    page: 1,
    per_page: 10
  }
});

// Filter admin PRs by category
const response = await api.get('/requisitions/admin', {
  params: {
    category: 'dell',
    status: 'APPROVED'
  }
});
```

### cURL Examples

```bash
# Get categories (requester)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/requisitions/categories

# Get categories (admin)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/requisitions/admin/categories

# Filter by category (requester)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/requisitions?category=laptop"

# Filter by category and status (admin)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/requisitions/admin?category=printer&status=SUBMITTED"
```

## Benefits

✅ **No Database Changes Required** - Works with existing schema
✅ **Automatic Category Discovery** - Categories are extracted from existing data
✅ **Flexible Search** - Case-insensitive partial matching
✅ **Simple Implementation** - Easy to understand and maintain
✅ **Combined Filters** - Can be used with status and other filters

## Notes

- Category matching is case-insensitive (e.g., "Laptop" matches "laptop")
- Partial matching is supported (e.g., "lap" will match "laptop")
- Only words longer than 2 characters are considered as categories
- The feature works seamlessly with existing pagination and filtering
