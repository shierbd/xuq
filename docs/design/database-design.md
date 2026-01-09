# Database Design Documentation

## Table of Contents
1. [Database Overview](#database-overview)
2. [Table Definitions](#table-definitions)
3. [Table Relationships](#table-relationships)
4. [Indexes and Constraints](#indexes-and-constraints)
5. [Data Dictionary](#data-dictionary)
6. [ER Diagram](#er-diagram)

---

## Database Overview

### Supported Databases
- **MySQL/MariaDB**: Production environment with native ENUM support
- **SQLite**: Development/testing environment with CHECK constraints

### Database Features
- **ORM Framework**: SQLAlchemy
- **Character Encoding**: UTF-8 (utf8mb4 for MySQL)
- **Connection Pooling**: Enabled with health checks
- **Auto-increment**: All primary keys use auto-increment
- **Timestamps**: Automatic creation and update tracking

### Database Configuration
```python
# MySQL Example
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/dbname?charset=utf8mb4"

# SQLite Example
DATABASE_URL = "sqlite:///./data/database.db"
```

### Compatibility Strategy
The system uses a custom `enum_column()` function to ensure compatibility:
- **MySQL**: Uses native `ENUM` type
- **SQLite**: Uses `String(50)` with `CheckConstraint`

---

## Table Definitions

### 1. phrases - 短语总库

**Purpose**: Stores all search keyword phrases collected from various sources.

**Table Name**: `phrases`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `phrase_id` | BigInteger | PRIMARY KEY, AUTO_INCREMENT | Unique phrase identifier |
| `phrase` | String(255) | UNIQUE, NOT NULL, INDEX | The actual phrase text |
| `seed_word` | String(100) | NULL | Source seed word used for expansion |
| `source_type` | ENUM/String(50) | INDEX | Source of phrase: 'semrush', 'dropdown', 'related_search' |
| `first_seen_round` | Integer | NOT NULL, INDEX | Round number when first discovered |
| `frequency` | BigInteger | DEFAULT 1 | Occurrence frequency |
| `volume` | BigInteger | DEFAULT 0 | Search volume |
| `cluster_id_A` | Integer | INDEX | Large cluster group ID |
| `cluster_id_B` | Integer | NULL | Small cluster subgroup ID |
| `mapped_demand_id` | Integer | INDEX | Associated demand card ID |
| `processed_status` | ENUM/String(50) | INDEX, DEFAULT 'unseen' | Processing status: 'unseen', 'reviewed', 'assigned', 'archived' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |

**Key Features**:
- Central repository for all collected phrases
- Tracks phrase lifecycle from discovery to demand mapping
- Supports hierarchical clustering (A/B levels)
- Links to seed words and demand cards

---

### 2. demands - 需求卡片

**Purpose**: Stores user demand cards extracted from phrase clusters.

**Table Name**: `demands`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `demand_id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique demand identifier |
| `title` | String(255) | NOT NULL | Demand title/summary |
| `description` | Text | NULL | Detailed demand description |
| `user_scenario` | Text | NULL | User scenario/use case |
| `demand_type` | ENUM/String(50) | INDEX | Type: 'tool', 'content', 'service', 'education', 'other' |
| `source_cluster_A` | Integer | INDEX | Source large cluster ID |
| `source_cluster_B` | Integer | NULL | Source small cluster ID |
| `related_phrases_count` | Integer | DEFAULT 0 | Number of related phrases |
| `business_value` | ENUM/String(50) | INDEX, DEFAULT 'unknown' | Value: 'high', 'medium', 'low', 'unknown' |
| `status` | ENUM/String(50) | INDEX, DEFAULT 'idea' | Status: 'idea', 'validated', 'in_progress', 'archived' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |

**Key Features**:
- Represents actionable user demands
- Links back to source clusters
- Tracks business value and implementation status
- Supports demand lifecycle management

---

### 3. tokens - Token词库

**Purpose**: Stores demand framework vocabulary (intent words, action words, object words, etc.).

**Table Name**: `tokens`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `token_id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique token identifier |
| `token_text` | String(100) | UNIQUE, NOT NULL, INDEX | The token text |
| `token_type` | ENUM/String(50) | NOT NULL, INDEX | Type: 'intent', 'action', 'object', 'attribute', 'condition', 'other' |
| `in_phrase_count` | Integer | DEFAULT 0, INDEX | Number of phrases containing this token |
| `first_seen_round` | Integer | NOT NULL | Round when first discovered |
| `verified` | Boolean | DEFAULT FALSE, INDEX | Whether token is verified |
| `notes` | Text | NULL | Additional notes |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Key Features**:
- Vocabulary for demand framework analysis
- Categorizes tokens by semantic role
- Tracks token usage across phrases
- Supports manual verification workflow

---

### 4. word_segments - 分词结果

**Purpose**: Stores word segmentation results with frequency statistics.

**Table Name**: `word_segments`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `word_id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique word identifier |
| `word` | String(255) | UNIQUE, NOT NULL, INDEX | Word or phrase text |
| `frequency` | Integer | DEFAULT 1, INDEX | Occurrence frequency |
| `word_count` | Integer | DEFAULT 1, INDEX | Number of words (1=word, >1=phrase) |
| `pos_tag` | String(20) | NULL | Detailed POS tag (e.g., NN, VBG) |
| `pos_category` | String(20) | INDEX | POS category (e.g., Noun, Verb) |
| `pos_chinese` | String(50) | NULL | Chinese POS name |
| `translation` | String(200) | NULL | Chinese translation |
| `is_root` | Boolean | DEFAULT FALSE, INDEX | Whether this is a root word |
| `root_round` | Integer | NULL | Round when marked as root |
| `root_source` | String(50) | NULL | Root source: 'initial_import', 'user_selected' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |

**Key Features**:
- Stores both individual words and multi-word phrases
- Includes linguistic metadata (POS tags)
- Supports root word identification
- Tracks word frequency for analysis

---

### 5. segmentation_batches - 分词批次

**Purpose**: Records metadata for each segmentation batch run.

**Table Name**: `segmentation_batches`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `batch_id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique batch identifier |
| `batch_date` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Batch execution date |
| `phrase_count` | Integer | NULL | Number of phrases processed |
| `word_count` | Integer | NULL | Total words generated |
| `new_word_count` | Integer | NULL | New words added |
| `duration_seconds` | Integer | NULL | Execution duration in seconds |
| `status` | ENUM/String(50) | INDEX, DEFAULT 'in_progress' | Status: 'completed', 'failed', 'in_progress' |
| `notes` | Text | NULL | Additional notes |

**Key Features**:
- Tracks segmentation job history
- Monitors performance metrics
- Supports batch processing audit trail

---

### 6. seed_words - 词根管理

**Purpose**: Manages all seed words with classification, definitions, and relationships.

**Table Name**: `seed_words`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `seed_id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Unique seed word identifier |
| `seed_word` | String(100) | UNIQUE, NOT NULL, INDEX | The seed word text |
| `token_types` | Text | NULL | JSON array of token types: ["intent", "action"] |
| `primary_token_type` | ENUM/String(50) | INDEX | Primary type: 'intent', 'action', 'object', 'other' |
| `definition` | Text | NULL | Word definition/meaning |
| `business_value` | Text | NULL | Business value description |
| `user_scenario` | Text | NULL | User scenario description |
| `parent_seed_word` | String(100) | INDEX | Parent seed word for hierarchy |
| `level` | Integer | DEFAULT 1 | Hierarchy level (1=root, 2=child, ...) |
| `expansion_count` | Integer | DEFAULT 0 | Number of expanded phrases |
| `total_volume` | BigInteger | DEFAULT 0 | Total search volume of related phrases |
| `avg_frequency` | Integer | DEFAULT 0 | Average frequency |
| `status` | ENUM/String(50) | INDEX, DEFAULT 'active' | Status: 'active', 'paused', 'archived' |
| `priority` | ENUM/String(50) | INDEX, DEFAULT 'medium' | Priority: 'high', 'medium', 'low' |
| `related_demand_ids` | Text | NULL | JSON array of related demand IDs |
| `primary_demand_id` | Integer | INDEX | Primary associated demand ID |
| `tags` | Text | NULL | JSON array of custom tags |
| `source` | String(100) | NULL | Source: 'initial_import', 'user_created', 'ai_suggested' |
| `first_seen_round` | Integer | NULL | Round when first seen |
| `verified` | Boolean | DEFAULT FALSE, INDEX | Whether verified by human |
| `confidence` | ENUM/String(50) | DEFAULT 'medium' | Confidence: 'high', 'medium', 'low' |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |
| `notes` | Text | NULL | Additional notes |

**Key Features**:
- Comprehensive seed word management
- Token framework classification
- Hierarchical relationships (parent-child)
- Business value and demand linking
- Flexible tagging system
- Status and priority tracking

---

### 7. cluster_meta - 聚类元数据

**Purpose**: Stores metadata and statistics for phrase clusters (both A and B levels).

**Table Name**: `cluster_meta`

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `cluster_id` | Integer | PRIMARY KEY | Cluster identifier |
| `cluster_level` | ENUM/String(50) | PRIMARY KEY | Level: 'A' (large), 'B' (small) |
| `parent_cluster_id` | Integer | NULL | Parent cluster ID (for level B only) |
| `size` | Integer | NULL | Number of phrases in cluster |
| `total_frequency` | BigInteger | NULL | Total frequency of all phrases |
| `example_phrases` | Text | NULL | Representative phrases (semicolon-separated) |
| `main_theme` | String(255) | NULL | AI-generated theme label |
| `is_selected` | Boolean | DEFAULT FALSE, INDEX | Whether cluster is selected |
| `selection_score` | Integer | NULL | Manual score (1-5) |
| `quality_score` | Integer | INDEX | Overall quality score (0-100) |
| `size_score` | Integer | NULL | Size score (0-100) |
| `diversity_score` | Integer | NULL | Diversity score (0-100) |
| `consistency_score` | Integer | NULL | Consistency score (0-100) |
| `quality_level` | ENUM/String(50) | INDEX | Level: 'excellent', 'good', 'fair', 'poor' |
| `llm_summary` | Text | NULL | LLM-generated cluster summary |
| `llm_value_assessment` | Text | NULL | LLM value assessment |
| `llm_label` | String(100) | NULL | Short semantic label |
| `primary_demand_type` | ENUM/String(50) | INDEX | Primary type: 'tool', 'content', 'service', 'education', 'other' |
| `secondary_demand_types` | Text | NULL | JSON array of secondary types |
| `labeling_confidence` | Integer | NULL | Labeling confidence (0-100) |
| `labeling_timestamp` | TIMESTAMP | NULL | When labeled |
| `dominant_intent` | String(50) | INDEX | Dominant intent category |
| `dominant_intent_confidence` | Integer | NULL | Intent confidence (0-100) |
| `intent_distribution` | Text | NULL | JSON intent distribution |
| `is_intent_balanced` | Boolean | DEFAULT FALSE | Whether intents are balanced |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Composite Primary Key**: (`cluster_id`, `cluster_level`)

**Key Features**:
- Supports two-level clustering (A and B)
- Automatic quality scoring system
- LLM-powered semantic labeling
- Intent analysis and classification
- Selection and prioritization support

---

## Table Relationships

### Entity Relationship Overview

```
seed_words (1) ----< (N) phrases
    |
    | (1:N)
    v
demands (1) ----< (N) phrases
    ^
    |
    | (1:N)
cluster_meta (1) ----< (N) phrases

phrases (N) >---- (1) cluster_meta [A level]
phrases (N) >---- (1) cluster_meta [B level]

word_segments (independent, derived from phrases)
tokens (independent, vocabulary reference)
segmentation_batches (independent, audit log)
```

### Detailed Relationships

#### 1. seed_words → phrases
- **Type**: One-to-Many
- **Foreign Key**: `phrases.seed_word` → `seed_words.seed_word`
- **Description**: Each seed word can generate multiple phrases through expansion
- **Cardinality**: 1:N

#### 2. demands → phrases
- **Type**: One-to-Many
- **Foreign Key**: `phrases.mapped_demand_id` → `demands.demand_id`
- **Description**: Each demand can be associated with multiple phrases
- **Cardinality**: 1:N

#### 3. cluster_meta → phrases (Level A)
- **Type**: One-to-Many
- **Foreign Key**: `phrases.cluster_id_A` → `cluster_meta.cluster_id` (where `cluster_level='A'`)
- **Description**: Each large cluster contains multiple phrases
- **Cardinality**: 1:N

#### 4. cluster_meta → phrases (Level B)
- **Type**: One-to-Many
- **Foreign Key**: `phrases.cluster_id_B` → `cluster_meta.cluster_id` (where `cluster_level='B'`)
- **Description**: Each small cluster contains multiple phrases
- **Cardinality**: 1:N

#### 5. cluster_meta (A) → cluster_meta (B)
- **Type**: One-to-Many (Hierarchical)
- **Foreign Key**: `cluster_meta.parent_cluster_id` → `cluster_meta.cluster_id`
- **Description**: Large clusters (A) contain multiple small clusters (B)
- **Cardinality**: 1:N

#### 6. demands → cluster_meta
- **Type**: Many-to-One
- **Foreign Keys**:
  - `demands.source_cluster_A` → `cluster_meta.cluster_id`
  - `demands.source_cluster_B` → `cluster_meta.cluster_id`
- **Description**: Demands are derived from clusters
- **Cardinality**: N:1

#### 7. seed_words → demands
- **Type**: Many-to-Many (via JSON)
- **Foreign Key**: `seed_words.related_demand_ids` (JSON array)
- **Description**: Seed words can relate to multiple demands
- **Cardinality**: M:N

#### 8. Independent Tables
- **word_segments**: Derived from phrases but no direct FK relationship
- **tokens**: Reference vocabulary, no direct FK relationship
- **segmentation_batches**: Audit log, no direct FK relationship

---

## Indexes and Constraints

### Primary Keys

| Table | Primary Key | Type |
|-------|-------------|------|
| phrases | phrase_id | BigInteger AUTO_INCREMENT |
| demands | demand_id | Integer AUTO_INCREMENT |
| tokens | token_id | Integer AUTO_INCREMENT |
| word_segments | word_id | Integer AUTO_INCREMENT |
| segmentation_batches | batch_id | Integer AUTO_INCREMENT |
| seed_words | seed_id | Integer AUTO_INCREMENT |
| cluster_meta | (cluster_id, cluster_level) | Composite |

### Unique Constraints

| Table | Column | Purpose |
|-------|--------|---------|
| phrases | phrase | Prevent duplicate phrases |
| tokens | token_text | Prevent duplicate tokens |
| word_segments | word | Prevent duplicate words/phrases |
| seed_words | seed_word | Prevent duplicate seed words |

### Single-Column Indexes

#### phrases
- `phrase` (UNIQUE INDEX)
- `source_type`
- `first_seen_round`
- `cluster_id_A`
- `mapped_demand_id`
- `processed_status`

#### demands
- `demand_type`
- `source_cluster_A`
- `business_value`
- `status`

#### tokens
- `token_text` (UNIQUE INDEX)
- `token_type`
- `in_phrase_count`
- `verified`

#### word_segments
- `word` (UNIQUE INDEX)
- `frequency`
- `word_count`
- `pos_category`
- `is_root`

#### segmentation_batches
- `status`

#### seed_words
- `seed_word` (UNIQUE INDEX)
- `primary_token_type`
- `parent_seed_word`
- `status`
- `priority`
- `primary_demand_id`
- `verified`

#### cluster_meta
- `is_selected`
- `quality_score`
- `quality_level`
- `primary_demand_type`
- `dominant_intent`

### Composite Indexes

#### cluster_meta
- `idx_level_selected`: (`cluster_level`, `is_selected`)
  - **Purpose**: Optimize queries filtering by level and selection status

### Check Constraints (SQLite Only)

All ENUM columns in SQLite use CHECK constraints to enforce valid values:

```sql
-- Example for phrases.source_type
CHECK (source_type IN ('semrush', 'dropdown', 'related_search'))

-- Example for phrases.processed_status
CHECK (processed_status IN ('unseen', 'reviewed', 'assigned', 'archived'))
```

---

## Data Dictionary

### Enumeration Types

#### source_type (phrases)
| Value | Description |
|-------|-------------|
| semrush | Phrase from SEMrush API |
| dropdown | Phrase from search dropdown suggestions |
| related_search | Phrase from related search results |

#### processed_status (phrases)
| Value | Description |
|-------|-------------|
| unseen | Not yet reviewed |
| reviewed | Reviewed but not assigned |
| assigned | Assigned to a demand |
| archived | Archived/deprecated |

#### demand_type (demands, cluster_meta)
| Value | Description |
|-------|-------------|
| tool | Tool/software demand |
| content | Content/information demand |
| service | Service demand |
| education | Educational/learning demand |
| other | Other types |

#### business_value (demands)
| Value | Description |
|-------|-------------|
| high | High business value |
| medium | Medium business value |
| low | Low business value |
| unknown | Not yet assessed |

#### demand_status (demands)
| Value | Description |
|-------|-------------|
| idea | Initial idea stage |
| validated | Validated demand |
| in_progress | Implementation in progress |
| archived | Archived |

#### token_type (tokens, seed_words)
| Value | Description |
|-------|-------------|
| intent | User intent word (e.g., "free", "best") |
| action | Action verb (e.g., "download", "create") |
| object | Object noun (e.g., "tool", "template") |
| attribute | Attribute/modifier (e.g., "online", "professional") |
| condition | Conditional word (e.g., "without", "for") |
| other | Other types |

#### batch_status (segmentation_batches)
| Value | Description |
|-------|-------------|
| completed | Successfully completed |
| failed | Failed with errors |
| in_progress | Currently running |

#### seed_status (seed_words)
| Value | Description |
|-------|-------------|
| active | Active seed word |
| paused | Temporarily paused |
| archived | Archived |

#### seed_priority (seed_words)
| Value | Description |
|-------|-------------|
| high | High priority |
| medium | Medium priority |
| low | Low priority |

#### seed_confidence (seed_words)
| Value | Description |
|-------|-------------|
| high | High confidence in classification |
| medium | Medium confidence |
| low | Low confidence, needs review |

#### cluster_level (cluster_meta)
| Value | Description |
|-------|-------------|
| A | Large cluster group |
| B | Small cluster subgroup |

#### quality_level (cluster_meta)
| Value | Description |
|-------|-------------|
| excellent | Quality score 80-100 |
| good | Quality score 60-79 |
| fair | Quality score 40-59 |
| poor | Quality score 0-39 |

### JSON Field Formats

#### seed_words.token_types
```json
["intent", "action"]
```

#### seed_words.related_demand_ids
```json
[1, 5, 12]
```

#### seed_words.tags
```json
["high-volume", "commercial", "trending"]
```

#### cluster_meta.secondary_demand_types
```json
["content", "education"]
```

#### cluster_meta.intent_distribution
```json
{
  "informational": 0.45,
  "transactional": 0.35,
  "navigational": 0.20
}
```

### Common Field Patterns

#### Timestamps
- **created_at**: Automatically set on record creation
- **updated_at**: Automatically updated on record modification
- **Format**: UTC timestamp

#### Frequency/Count Fields
- **frequency**: Occurrence count (Integer/BigInteger)
- **volume**: Search volume (BigInteger)
- **count**: Generic count (Integer)

#### Score Fields
- **Range**: 0-100 (Integer)
- **quality_score**: Overall quality
- **size_score**: Size-based score
- **diversity_score**: Diversity metric
- **consistency_score**: Consistency metric
- **confidence**: Confidence level (0-100)

#### Boolean Flags
- **is_selected**: Selection status
- **is_root**: Root word flag
- **verified**: Verification status
- **is_intent_balanced**: Balance flag

---

## ER Diagram

### Conceptual ER Diagram

```
┌─────────────────┐
│   seed_words    │
│  (词根管理)      │
└────────┬────────┘
         │ 1
         │ generates
         │ N
         ▼
┌─────────────────┐         ┌─────────────────┐
│    phrases      │    N    │  cluster_meta   │
│   (短语总库)     │◄────────┤   (聚类元数据)   │
└────────┬────────┘  belongs│                 │
         │              to  │  Level A & B    │
         │ N                └────────┬────────┘
         │                           │
         │ mapped to                 │ 1
         │ 1                         │ sources
         ▼                           │ N
┌─────────────────┐                 │
│    demands      │◄────────────────┘
│   (需求卡片)     │
└─────────────────┘

┌─────────────────┐     ┌──────────────────────┐
│     tokens      │     │   word_segments      │
│   (Token词库)    │     │    (分词结果)         │
└─────────────────┘     └──────────────────────┘
        ▲                         ▲
        │                         │
        │ reference               │ derived from
        │                         │
        └─────────────────────────┘
                phrases

┌──────────────────────┐
│ segmentation_batches │
│    (分词批次)         │
└──────────────────────┘
         ▲
         │ logs
         │
    (audit trail)
```

### Detailed Relationship Diagram

```
seed_words (1) ──generates──> (N) phrases
    │                            │
    │                            │ belongs_to
    │                            ▼
    │                      cluster_meta (A)
    │                            │
    │                            │ contains
    │                            ▼
    │                      cluster_meta (B)
    │                            │
    │                            │ sources
    │                            ▼
    └──relates_to──> (N) demands (N) <──mapped_from── phrases


phrases ──segments_to──> word_segments (derived)
phrases ──references──> tokens (vocabulary)
phrases ──logged_by──> segmentation_batches (audit)
```

### Hierarchical Cluster Structure

```
cluster_meta (Level A)
    │
    ├── cluster_meta (Level B1)
    │       └── phrases (N)
    │
    ├── cluster_meta (Level B2)
    │       └── phrases (N)
    │
    └── cluster_meta (Level B3)
            └── phrases (N)
```

### Data Flow Diagram

```
1. Seed Word Expansion
   seed_words → [API/Scraping] → phrases

2. Phrase Segmentation
   phrases → [NLP Processing] → word_segments
                              → tokens

3. Clustering
   phrases → [Clustering Algorithm] → cluster_meta (A & B)

4. Demand Extraction
   cluster_meta → [Analysis] → demands
   demands ← [Mapping] ← phrases

5. Audit Trail
   [Segmentation Jobs] → segmentation_batches
```

---

## Database Operations

### Common Query Patterns

#### 1. Get all phrases for a seed word
```sql
SELECT * FROM phrases
WHERE seed_word = 'free'
ORDER BY frequency DESC;
```

#### 2. Get cluster hierarchy
```sql
SELECT
    a.cluster_id as cluster_a,
    a.main_theme as theme_a,
    b.cluster_id as cluster_b,
    b.main_theme as theme_b,
    b.size
FROM cluster_meta a
LEFT JOIN cluster_meta b ON b.parent_cluster_id = a.cluster_id
WHERE a.cluster_level = 'A' AND b.cluster_level = 'B'
ORDER BY a.cluster_id, b.cluster_id;
```

#### 3. Get demand with related phrases
```sql
SELECT
    d.*,
    COUNT(p.phrase_id) as phrase_count
FROM demands d
LEFT JOIN phrases p ON p.mapped_demand_id = d.demand_id
GROUP BY d.demand_id
ORDER BY phrase_count DESC;
```

#### 4. Get high-frequency root words
```sql
SELECT * FROM word_segments
WHERE is_root = TRUE
ORDER BY frequency DESC
LIMIT 100;
```

#### 5. Get seed word statistics
```sql
SELECT
    sw.*,
    COUNT(p.phrase_id) as actual_expansions
FROM seed_words sw
LEFT JOIN phrases p ON p.seed_word = sw.seed_word
GROUP BY sw.seed_id
ORDER BY actual_expansions DESC;
```

### Performance Considerations

#### Indexing Strategy
- **High-cardinality columns**: phrase, token_text, word, seed_word
- **Filter columns**: status fields, type fields, boolean flags
- **Join columns**: All foreign key references
- **Sort columns**: frequency, created_at, scores

#### Query Optimization Tips
1. Use indexes for WHERE, JOIN, and ORDER BY clauses
2. Avoid SELECT * in production queries
3. Use LIMIT for large result sets
4. Consider pagination for UI queries
5. Use composite indexes for multi-column filters

#### Data Maintenance
1. Regular VACUUM (SQLite) or OPTIMIZE TABLE (MySQL)
2. Monitor index usage and remove unused indexes
3. Archive old segmentation_batches records
4. Update aggregate statistics in seed_words periodically

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-08 | Initial comprehensive documentation |

---

## References

- **Source Code**: `storage/models.py`
- **ORM Framework**: SQLAlchemy
- **Database Engines**: MySQL/MariaDB, SQLite
- **Character Encoding**: UTF-8 (utf8mb4)
