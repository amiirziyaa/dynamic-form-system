# Database Schema Documentation
## Dynamic Forms System

---

## Table of Contents
1. [User Management](#1-user-management)
2. [Category Management](#2-category-management)
3. [Form Management](#3-form-management)
4. [Process Management](#4-process-management)
5. [Submission & Response Management](#5-submission--response-management)
6. [Analytics & Tracking](#6-analytics--tracking)
7. [Indexes & Performance](#7-indexes--performance)
8. [Data Types Reference](#8-data-types-reference)

---

## 1. User Management

### Table: `user`
**Purpose**: Stores user account information and authentication details.

**Relationships**:
- One-to-Many with `form`, `process`, `category`, `form_submission`, `process_progress`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the user |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address (used for login) |
| `password` | VARCHAR(128) | NOT NULL | Hashed password (Django's password hasher) |
| `first_name` | VARCHAR(150) | NULL | User's first name |
| `last_name` | VARCHAR(150) | NULL | User's last name |
| `phone_number` | VARCHAR(20) | NULL | Phone number for OTP authentication |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether the account is active |
| `is_staff` | BOOLEAN | DEFAULT FALSE | Admin/staff access flag |
| `email_verified` | BOOLEAN | DEFAULT FALSE | Email verification status |
| `created_at` | TIMESTAMP | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `last_login` | TIMESTAMP | NULL | Last login timestamp |

**Notes**:
- Compatible with Django's built-in authentication system
- `password` should be hashed using Django's `make_password()`
- `phone_number` is optional but required for OTP feature
- `email_verified` prevents unauthorized email usage

---

## 2. Category Management

### Table: `category`
**Purpose**: Organizational containers for grouping forms and processes.

**Relationships**:
- Many-to-One with `user` (owner)
- One-to-Many with `form`, `process`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the category |
| `user_id` | UUID | FOREIGN KEY, NOT NULL | Owner of the category (references `user.id`) |
| `name` | VARCHAR(255) | NOT NULL | Category name (e.g., "HR Forms", "Surveys") |
| `description` | TEXT | NULL | Optional description of the category |
| `color` | VARCHAR(7) | NULL | Hex color code for UI display (e.g., "#FF5733") |
| `created_at` | TIMESTAMP | NOT NULL | Category creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Notes**:
- Categories are user-specific (each user has their own categories)
- `color` helps with visual organization in UI
- Deleting a category should NOT delete forms/processes (set to NULL)

---

## 3. Form Management

### Table: `form`
**Purpose**: Core table storing form definitions and metadata.

**Relationships**:
- Many-to-One with `user` (creator)
- Many-to-One with `category` (optional)
- One-to-Many with `form_field`, `form_submission`, `form_view`
- Many-to-Many with `process` (through `process_step`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the form |
| `user_id` | UUID | FOREIGN KEY, NOT NULL | Form creator (references `user.id`) |
| `category_id` | UUID | FOREIGN KEY, NULL | Category assignment (references `category.id`) |
| `title` | VARCHAR(255) | NOT NULL | Form title/name |
| `description` | TEXT | NULL | Detailed description of the form's purpose |
| `unique_slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly identifier (e.g., "customer-feedback-2024") |
| `visibility` | ENUM | NOT NULL | Access level: 'public' or 'private' |
| `access_password` | VARCHAR(128) | NULL | Encrypted password for private forms |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether the form accepts new submissions |
| `settings` | JSON | NULL | Additional settings (theme, notifications, etc.) |
| `created_at` | TIMESTAMP | NOT NULL | Form creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last modification timestamp |
| `published_at` | TIMESTAMP | NULL | When the form was first published |

**Notes**:
- `unique_slug` must be generated to be globally unique (used in URLs)
- `access_password` should be encrypted (not hashed) to allow verification
- `visibility='private'` requires password to access
- `settings` JSON example: `{"theme": "dark", "allow_multiple": false, "send_email": true}`
- `is_active=false` means form is archived/disabled

**Example `settings` JSON**:
```json
{
  "theme": "default",
  "allow_multiple_submissions": false,
  "show_progress_bar": true,
  "redirect_url": "https://example.com/thank-you",
  "send_confirmation_email": true,
  "collect_ip_address": false
}
```

---

### Table: `form_field`
**Purpose**: Individual questions/inputs within a form.

**Relationships**:
- Many-to-One with `form`
- One-to-Many with `field_option` (for select/radio/checkbox)
- One-to-Many with `submission_answer`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the field |
| `form_id` | UUID | FOREIGN KEY, NOT NULL | Parent form (references `form.id`) |
| `field_type` | ENUM | NOT NULL | Type of input (text, number, email, select, checkbox, radio, textarea, date, file) |
| `label` | VARCHAR(255) | NOT NULL | Question/field label displayed to users |
| `description` | TEXT | NULL | Helper text or additional instructions |
| `is_required` | BOOLEAN | DEFAULT FALSE | Whether the field must be filled |
| `order_index` | INTEGER | NOT NULL | Display order (0-based, allows reordering) |
| `validation_rules` | JSON | NULL | Custom validation logic |
| `settings` | JSON | NULL | Field-specific configuration |
| `created_at` | TIMESTAMP | NOT NULL | Field creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last modification timestamp |

**Notes**:
- `order_index` determines display order (lower = earlier)
- `field_type` values: text, number, email, select, checkbox, radio, textarea, date, file
- Cascade delete when parent form is deleted

**Example `validation_rules` JSON**:
```json
{
  "min": 5,
  "max": 100,
  "pattern": "^[A-Za-z]+$",
  "min_length": 10,
  "max_length": 500,
  "allowed_extensions": [".pdf", ".docx"],
  "max_file_size": 5242880
}
```

**Example `settings` JSON**:
```json
{
  "placeholder": "Enter your name",
  "default_value": "",
  "help_text": "Please use your legal name",
  "prefix": "$",
  "suffix": "USD",
  "rows": 5,
  "columns": 80,
  "multiple": true
}
```

---

### Table: `field_option`
**Purpose**: Options for select, radio, and checkbox fields.

**Relationships**:
- Many-to-One with `form_field`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the option |
| `field_id` | UUID | FOREIGN KEY, NOT NULL | Parent field (references `form_field.id`) |
| `label` | VARCHAR(255) | NOT NULL | Display text for the option |
| `value` | VARCHAR(255) | NOT NULL | Actual value stored when selected |
| `order_index` | INTEGER | NOT NULL | Display order within the field |
| `created_at` | TIMESTAMP | NOT NULL | Option creation timestamp |

**Notes**:
- Only relevant for `field_type` in (select, radio, checkbox)
- `label` is what users see, `value` is what's stored
- Example: label="Very Satisfied", value="5"

---

## 4. Process Management

### Table: `process`
**Purpose**: Multi-step workflows composed of multiple forms.

**Relationships**:
- Many-to-One with `user` (creator)
- Many-to-One with `category` (optional)
- One-to-Many with `process_step`, `process_progress`, `process_view`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the process |
| `user_id` | UUID | FOREIGN KEY, NOT NULL | Process creator (references `user.id`) |
| `category_id` | UUID | FOREIGN KEY, NULL | Category assignment (references `category.id`) |
| `title` | VARCHAR(255) | NOT NULL | Process name |
| `description` | TEXT | NULL | Description of the process workflow |
| `unique_slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly identifier |
| `visibility` | ENUM | NOT NULL | Access level: 'public' or 'private' |
| `access_password` | VARCHAR(128) | NULL | Encrypted password for private processes |
| `process_type` | ENUM | NOT NULL | Workflow type: 'linear' or 'free' |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether the process accepts new entries |
| `settings` | JSON | NULL | Additional configuration |
| `created_at` | TIMESTAMP | NOT NULL | Process creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last modification timestamp |
| `published_at` | TIMESTAMP | NULL | First publication timestamp |

**Notes**:
- `process_type='linear'`: Steps must be completed in order
- `process_type='free'`: Steps can be completed in any order
- Similar structure to `form` table for consistency

**Example `settings` JSON**:
```json
{
  "allow_save_progress": true,
  "show_step_numbers": true,
  "completion_message": "Thank you for completing the process!",
  "completion_redirect_url": "https://example.com/success",
  "send_completion_email": true,
  "session_timeout_minutes": 60
}
```

---

### Table: `process_step`
**Purpose**: Individual steps/stages within a process (links to forms).

**Relationships**:
- Many-to-One with `process`
- Many-to-One with `form` (the form used in this step)
- One-to-Many with `process_step_completion`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the step |
| `process_id` | UUID | FOREIGN KEY, NOT NULL | Parent process (references `process.id`) |
| `form_id` | UUID | FOREIGN KEY, NOT NULL | Form used in this step (references `form.id`) |
| `title` | VARCHAR(255) | NOT NULL | Step name (e.g., "Personal Information") |
| `description` | TEXT | NULL | Instructions for this step |
| `order_index` | INTEGER | NOT NULL | Step sequence (0-based) |
| `is_required` | BOOLEAN | DEFAULT TRUE | Whether step must be completed |
| `conditions` | JSON | NULL | Conditional logic for step visibility/requirement |
| `created_at` | TIMESTAMP | NOT NULL | Step creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last modification timestamp |

**Notes**:
- Forms can be reused across multiple processes
- `order_index` only matters for `process_type='linear'`
- `conditions` enables branching logic (future feature)

**Example `conditions` JSON**:
```json
{
  "show_if": {
    "field_id": "uuid-here",
    "operator": "equals",
    "value": "yes"
  },
  "required_if": {
    "step_id": "uuid-here",
    "completed": true
  }
}
```

---

## 5. Submission & Response Management

### Table: `form_submission`
**Purpose**: Tracks individual form submissions (user responses).

**Relationships**:
- Many-to-One with `form`
- Many-to-One with `user` (nullable for anonymous)
- Many-to-One with `process_progress` (nullable)
- One-to-Many with `submission_answer`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the submission |
| `form_id` | UUID | FOREIGN KEY, NOT NULL | Form being submitted (references `form.id`) |
| `user_id` | UUID | FOREIGN KEY, NULL | Authenticated user (references `user.id`, null for anonymous) |
| `process_progress_id` | UUID | FOREIGN KEY, NULL | Associated process progress (references `process_progress.id`) |
| `session_id` | VARCHAR(255) | NOT NULL | Browser session identifier (for anonymous tracking) |
| `status` | ENUM | NOT NULL | Submission status: 'draft', 'submitted', 'archived' |
| `metadata` | JSON | NULL | Additional tracking data (IP, user agent, etc.) |
| `submitted_at` | TIMESTAMP | NULL | When submission was finalized (null for drafts) |
| `created_at` | TIMESTAMP | NOT NULL | Initial creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last modification timestamp |

**Notes**:
- `user_id` NULL means anonymous submission
- `session_id` used to track anonymous users across requests
- `status='draft'` allows saving progress
- `process_progress_id` links submission to a process workflow

**Example `metadata` JSON**:
```json
{
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "referer": "https://google.com",
  "language": "en-US",
  "device_type": "desktop",
  "browser": "Chrome",
  "submission_duration_seconds": 145
}
```

---

### Table: `submission_answer`
**Purpose**: Individual field responses within a submission.

**Relationships**:
- Many-to-One with `form_submission`
- Many-to-One with `form_field`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the answer |
| `submission_id` | UUID | FOREIGN KEY, NOT NULL | Parent submission (references `form_submission.id`) |
| `field_id` | UUID | FOREIGN KEY, NOT NULL | Field being answered (references `form_field.id`) |
| `text_value` | TEXT | NULL | Text-based answers (text, textarea, email) |
| `numeric_value` | DECIMAL(20,6) | NULL | Number-based answers |
| `boolean_value` | BOOLEAN | NULL | Boolean/checkbox answers |
| `date_value` | DATE/DATETIME | NULL | Date/time answers |
| `array_value` | JSON | NULL | Multiple selections (checkboxes, multi-select) |
| `file_url` | VARCHAR(500) | NULL | File upload path/URL |
| `created_at` | TIMESTAMP | NOT NULL | Answer creation timestamp |

**Notes**:
- **Only ONE value column should be populated** per answer (based on `field_type`)
- `text_value`: for text, textarea, email field types
- `numeric_value`: for number field types
- `boolean_value`: for single checkbox
- `date_value`: for date/datetime field types
- `array_value`: for multiple checkboxes, multi-select (stores JSON array)
- `file_url`: for file uploads (store S3 URL or relative path)
- This design allows efficient querying and aggregation by data type

**Example `array_value` JSON**:
```json
["option1", "option3", "option5"]
```

---

### Table: `process_progress`
**Purpose**: Tracks user's journey through a multi-step process.

**Relationships**:
- Many-to-One with `process`
- Many-to-One with `user` (nullable for anonymous)
- One-to-Many with `process_step_completion`, `form_submission`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the progress record |
| `process_id` | UUID | FOREIGN KEY, NOT NULL | Process being tracked (references `process.id`) |
| `user_id` | UUID | FOREIGN KEY, NULL | Authenticated user (null for anonymous) |
| `session_id` | VARCHAR(255) | NOT NULL | Session identifier for tracking |
| `status` | ENUM | NOT NULL | Progress status: 'in_progress', 'completed', 'abandoned' |
| `current_step_index` | INTEGER | NOT NULL | Current step position (0-based) |
| `completion_percentage` | DECIMAL(5,2) | DEFAULT 0.00 | Progress percentage (0.00 to 100.00) |
| `started_at` | TIMESTAMP | NOT NULL | When process was started |
| `completed_at` | TIMESTAMP | NULL | When process was completed (null if not finished) |
| `last_activity_at` | TIMESTAMP | NOT NULL | Last interaction timestamp |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Notes**:
- Enables "resume where you left off" functionality
- `completion_percentage` calculated as: (completed_steps / total_steps) * 100
- `last_activity_at` used to detect abandoned processes
- `status='abandoned'` can be set automatically after inactivity period

---

### Table: `process_step_completion`
**Purpose**: Tracks completion status of individual steps within a process.

**Relationships**:
- Many-to-One with `process_progress`
- Many-to-One with `process_step`
- Many-to-One with `form_submission` (nullable)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the completion record |
| `progress_id` | UUID | FOREIGN KEY, NOT NULL | Associated progress (references `process_progress.id`) |
| `step_id` | UUID | FOREIGN KEY, NOT NULL | Step being tracked (references `process_step.id`) |
| `submission_id` | UUID | FOREIGN KEY, NULL | Form submission for this step (references `form_submission.id`) |
| `status` | ENUM | NOT NULL | Completion status: 'pending', 'completed', 'skipped' |
| `completed_at` | TIMESTAMP | NULL | When step was completed |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Notes**:
- One record per step per process progress
- `status='pending'`: Not yet started
- `status='completed'`: Step finished
- `status='skipped'`: Step bypassed (for `is_required=false` steps)
- Links to `form_submission` when step is completed

---

## 6. Analytics & Tracking

### Table: `form_view`
**Purpose**: Tracks each view/visit to a form (for analytics).

**Relationships**:
- Many-to-One with `form`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the view record |
| `form_id` | UUID | FOREIGN KEY, NOT NULL | Form being viewed (references `form.id`) |
| `session_id` | VARCHAR(255) | NOT NULL | Browser session identifier |
| `ip_address` | VARCHAR(45) | NULL | Visitor IP address (IPv6 compatible) |
| `metadata` | JSON | NULL | Additional tracking information |
| `viewed_at` | TIMESTAMP | NOT NULL | Timestamp of the view |

**Notes**:
- Lightweight table for tracking views
- No foreign key to `user` (privacy and performance)
- Can be partitioned by date for performance
- `ip_address` stored for abuse prevention (optional based on privacy policy)

**Example `metadata` JSON**:
```json
{
  "user_agent": "Mozilla/5.0...",
  "referer": "https://google.com/search?q=survey",
  "language": "en-US",
  "device_type": "mobile",
  "browser": "Safari",
  "os": "iOS"
}
```

---

### Table: `process_view`
**Purpose**: Tracks each view/visit to a process (for analytics).

**Relationships**:
- Many-to-One with `process`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the view record |
| `process_id` | UUID | FOREIGN KEY, NOT NULL | Process being viewed (references `process.id`) |
| `session_id` | VARCHAR(255) | NOT NULL | Browser session identifier |
| `ip_address` | VARCHAR(45) | NULL | Visitor IP address |
| `metadata` | JSON | NULL | Additional tracking information |
| `viewed_at` | TIMESTAMP | NOT NULL | Timestamp of the view |

**Notes**:
- Same structure as `form_view` for consistency
- Used for calculating view count and conversion rates
- Separate table allows independent partitioning/archiving

---

## 7. Indexes & Performance

### Critical Indexes

**User Table**:
```sql
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_active ON user(is_active) WHERE is_active = TRUE;
```

**Form Table**:
```sql
CREATE INDEX idx_form_user ON form(user_id);
CREATE INDEX idx_form_slug ON form(unique_slug);
CREATE INDEX idx_form_category ON form(category_id) WHERE category_id IS NOT NULL;
CREATE INDEX idx_form_visibility_active ON form(visibility, is_active);
CREATE INDEX idx_form_created ON form(created_at DESC);
```

**FormField Table**:
```sql
CREATE INDEX idx_field_form_order ON form_field(form_id, order_index);
```

**FormSubmission Table**:
```sql
CREATE INDEX idx_submission_form ON form_submission(form_id);
CREATE INDEX idx_submission_user ON form_submission(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_submission_session ON form_submission(session_id);
CREATE INDEX idx_submission_status ON form_submission(status);
CREATE INDEX idx_submission_date ON form_submission(submitted_at DESC) WHERE submitted_at IS NOT NULL;
CREATE INDEX idx_submission_process ON form_submission(process_progress_id) WHERE process_progress_id IS NOT NULL;
```

**SubmissionAnswer Table**:
```sql
CREATE INDEX idx_answer_submission ON submission_answer(submission_id);
CREATE INDEX idx_answer_field ON submission_answer(field_id);
-- For reporting/aggregation
CREATE INDEX idx_answer_numeric ON submission_answer(field_id, numeric_value) WHERE numeric_value IS NOT NULL;
```

**Process Table**:
```sql
CREATE INDEX idx_process_user ON process(user_id);
CREATE INDEX idx_process_slug ON process(unique_slug);
CREATE INDEX idx_process_type ON process(process_type);
```

**ProcessStep Table**:
```sql
CREATE INDEX idx_step_process_order ON process_step(process_id, order_index);
CREATE INDEX idx_step_form ON process_step(form_id);
```

**ProcessProgress Table**:
```sql
CREATE INDEX idx_progress_process ON process_progress(process_id);
CREATE INDEX idx_progress_user ON process_progress(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_progress_session ON process_progress(session_id);
CREATE INDEX idx_progress_status ON process_progress(status);
CREATE INDEX idx_progress_activity ON process_progress(last_activity_at DESC);
```

**View Tracking Tables**:
```sql
CREATE INDEX idx_form_view_date ON form_view(form_id, viewed_at DESC);
CREATE INDEX idx_process_view_date ON process_view(process_id, viewed_at DESC);
```

---

## 8. Data Types Reference

### ENUM Types

**visibility**:
- `public`: Accessible to anyone with the link
- `private`: Requires password to access

**field_type**:
- `text`: Short text input
- `textarea`: Long text input
- `number`: Numeric input
- `email`: Email validation
- `select`: Dropdown selection (single)
- `checkbox`: Multiple selections
- `radio`: Single selection from options
- `date`: Date picker
- `file`: File upload

**process_type**:
- `linear`: Sequential steps (must complete in order)
- `free`: Non-sequential (complete in any order)

**submission_status**:
- `draft`: Incomplete submission (saved progress)
- `submitted`: Completed and finalized
- `archived`: Soft-deleted or archived

**process_progress_status**:
- `in_progress`: Currently being completed
- `completed`: All required steps finished
- `abandoned`: User stopped without completing

**step_completion_status**:
- `pending`: Not yet started
- `completed`: Step finished
- `skipped`: Bypassed (for optional steps)

---

## 9. Constraints & Business Rules

### Unique Constraints
- `user.email` - One email per account
- `form.unique_slug` - Globally unique form URLs
- `process.unique_slug` - Globally unique process URLs
- `(form_field.form_id, form_field.order_index)` - No duplicate positions
- `(process_step.process_id, process_step.order_index)` - No duplicate positions

### Cascade Rules
- **DELETE CASCADE**: When deleting form → delete form_fields, form_submissions
- **DELETE CASCADE**: When deleting process → delete process_steps
- **SET NULL**: When deleting category → set category_id to NULL in forms/processes
- **RESTRICT**: Cannot delete form if referenced in process_step

### Check Constraints
```sql
-- Completion percentage must be 0-100
ALTER TABLE process_progress ADD CONSTRAINT check_completion_percentage 
  CHECK (completion_percentage >= 0 AND completion_percentage <= 100);

-- Order index must be non-negative
ALTER TABLE form_field ADD CONSTRAINT check_order_index 
  CHECK (order_index >= 0);

-- At least one value column must be populated in submission_answer
ALTER TABLE submission_answer ADD CONSTRAINT check_answer_value
  CHECK (
    (text_value IS NOT NULL)::int +
    (numeric_value IS NOT NULL)::int +
    (boolean_value IS NOT NULL)::int +
    (date_value IS NOT NULL)::int +
    (array_value IS NOT NULL)::int +
    (file_url IS NOT NULL)::int = 1
  );
```

---

## 10. Privacy & Security Considerations

### Personal Data Fields
- `user.email`, `user.phone_number`, `user.first_name`, `user.last_name`
- `form_view.ip_address`, `process_view.ip_address`
- `form_submission.metadata` (may contain IP)

### Encryption Requirements
- `form.access_password` - Encrypted (AES-256)
- `process.access_password` - Encrypted (AES-256)
- `user.password` - Hashed (Django's PBKDF2)

### GDPR Compliance
- Implement soft deletes (add `deleted_at` timestamp)
- Support data export (all user data)
- Support data anonymization (replace PII with anonymized values)
- Maintain audit logs for sensitive operations

### Retention Policies
- `form_view` / `process_view`: Archive after 1 year
- `form_submission` (draft): Delete after 30 days of inactivity
- `process_progress` (abandoned): Archive after 90 days

---

## 11. JSON Field Schemas

### form.settings
```json
{
  "type": "object",
  "properties": {
    "theme": {"type": "string", "enum": ["default", "dark", "light"]},
    "allow_multiple_submissions": {"type": "boolean"},
    "show_progress_bar": {"type": "boolean"},
    "redirect_url": {"type": "string", "format": "uri"},
    "send_confirmation_email": {"type": "boolean"},
    "collect_ip_address": {"type": "boolean"},
    "auto_save_draft": {"type": "boolean"},
    "require_authentication": {"type": "boolean"}
  }
}
```

### form_field.validation_rules
```json
{
  "type": "object",
  "properties": {
    "min": {"type": "number"},
    "max": {"type": "number"},
    "min_length": {"type": "integer"},
    "max_length": {"type": "integer"},
    "pattern": {"type": "string"},
    "allowed_extensions": {"type": "array", "items": {"type": "string"}},
    "max_file_size": {"type": "integer"},
    "custom_error_message": {"type": "string"}
  }
}
```

### form_field.settings
```json
{
  "type": "object",
  "properties": {
    "placeholder": {"type": "string"},
    "default_value": {"type": "string"},
    "help_text": {"type": "string"},
    "prefix": {"type": "string"},
    "suffix": {"type": "string"},
    "rows": {"type": "integer"},
    "columns": {"type": "integer"},
    "multiple": {"type": "boolean"},
    "autocomplete": {"type": "boolean"}
  }
}
```

### process.settings
```json
{
  "type": "object",
  "properties": {
    "allow_save_progress": {"type": "boolean"},
    "show_step_numbers": {"type": "boolean"},
    "completion_message": {"type": "string"},
    "completion_redirect_url": {"type": "string", "format": "uri"},
    "send_completion_email": {"type": "boolean"},
    "session_timeout_minutes": {"type": "integer"}
  }
}
```

---

## 12. Migration Strategy

### Initial Migration Order
1. Create `user` table (independent)
2. Create `category` table (depends on user)
3. Create `form` table (depends on user, category)
4. Create `form_field` table (depends on form)
5. Create `field_option` table (depends on form_field)
6. Create `process` table (depends on user, category)
7. Create `process_step` table (depends on process, form)
8. Create `form_submission` table (depends on form, user)
9. Create `submission_answer` table (depends on form_submission, form_field)
10. Create `process_progress` table (depends on process, user)
11. Create `process_step_completion` table (depends on process_progress, process_step, form_submission)
12. Create `form_view` table (depends on form)
13. Create `process_view` table (depends on process)

### Adding Columns (Non-breaking)
- Always add new columns as nullable
- Provide default values for existing rows
- Backfill data if necessary

### Removing Columns (Breaking)
1. Mark column as deprecated (documentation)
2. Stop writing to column
3. Wait for migration period (1-2 releases)
4. Drop column in next major version

---

## 13. Common Queries & Optimization

### Query Examples

#### Get all forms with submission count
```sql
SELECT 
    f.id,
    f.title,
    f.unique_slug,
    COUNT(DISTINCT fs.id) as submission_count,
    COUNT(DISTINCT fv.id) as view_count
FROM form f
LEFT JOIN form_submission fs ON f.id = fs.form_id AND fs.status = 'submitted'
LEFT JOIN form_view fv ON f.id = fv.form_id
WHERE f.user_id = :user_id
GROUP BY f.id, f.title, f.unique_slug
ORDER BY f.created_at DESC;
```

#### Get form with all fields and options
```sql
SELECT 
    f.*,
    json_agg(
        json_build_object(
            'id', ff.id,
            'field_type', ff.field_type,
            'label', ff.label,
            'is_required', ff.is_required,
            'order_index', ff.order_index,
            'options', (
                SELECT json_agg(
                    json_build_object(
                        'id', fo.id,
                        'label', fo.label,
                        'value', fo.value,
                        'order_index', fo.order_index
                    ) ORDER BY fo.order_index
                )
                FROM field_option fo
                WHERE fo.field_id = ff.id
            )
        ) ORDER BY ff.order_index
    ) as fields
FROM form f
LEFT JOIN form_field ff ON f.id = ff.form_id
WHERE f.unique_slug = :slug
GROUP BY f.id;
```

#### Get submission with all answers
```sql
SELECT 
    fs.*,
    json_agg(
        json_build_object(
            'field_id', sa.field_id,
            'field_label', ff.label,
            'field_type', ff.field_type,
            'text_value', sa.text_value,
            'numeric_value', sa.numeric_value,
            'boolean_value', sa.boolean_value,
            'date_value', sa.date_value,
            'array_value', sa.array_value,
            'file_url', sa.file_url
        )
    ) as answers
FROM form_submission fs
LEFT JOIN submission_answer sa ON fs.id = sa.submission_id
LEFT JOIN form_field ff ON sa.field_id = ff.id
WHERE fs.id = :submission_id
GROUP BY fs.id;
```

#### Get process with steps and completion status
```sql
SELECT 
    p.*,
    json_agg(
        json_build_object(
            'step_id', ps.id,
            'title', ps.title,
            'order_index', ps.order_index,
            'form_slug', f.unique_slug,
            'is_completed', COALESCE(psc.status = 'completed', false)
        ) ORDER BY ps.order_index
    ) as steps
FROM process p
LEFT JOIN process_step ps ON p.id = ps.process_id
LEFT JOIN form f ON ps.form_id = f.id
LEFT JOIN process_progress pp ON p.id = pp.process_id 
    AND pp.session_id = :session_id
LEFT JOIN process_step_completion psc ON ps.id = psc.step_id 
    AND psc.progress_id = pp.id
WHERE p.unique_slug = :slug
GROUP BY p.id;
```

#### Aggregate report for numeric field
```sql
SELECT 
    ff.label as field_name,
    COUNT(sa.numeric_value) as response_count,
    AVG(sa.numeric_value) as average_value,
    MIN(sa.numeric_value) as min_value,
    MAX(sa.numeric_value) as max_value,
    STDDEV(sa.numeric_value) as std_deviation
FROM form_field ff
JOIN submission_answer sa ON ff.id = sa.field_id
JOIN form_submission fs ON sa.submission_id = fs.id
WHERE ff.form_id = :form_id
    AND ff.field_type = 'number'
    AND fs.status = 'submitted'
    AND sa.numeric_value IS NOT NULL
GROUP BY ff.id, ff.label;
```

#### Aggregate report for select/radio field
```sql
SELECT 
    ff.label as field_name,
    sa.text_value as option_value,
    COUNT(*) as selection_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY ff.id), 2) as percentage
FROM form_field ff
JOIN submission_answer sa ON ff.id = sa.field_id
JOIN form_submission fs ON sa.submission_id = fs.id
WHERE ff.form_id = :form_id
    AND ff.field_type IN ('select', 'radio')
    AND fs.status = 'submitted'
    AND sa.text_value IS NOT NULL
GROUP BY ff.id, ff.label, sa.text_value
ORDER BY ff.label, selection_count DESC;
```

#### Process completion funnel analysis
```sql
SELECT 
    ps.order_index,
    ps.title as step_name,
    COUNT(DISTINCT pp.id) as started_count,
    COUNT(DISTINCT CASE WHEN psc.status = 'completed' THEN pp.id END) as completed_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN psc.status = 'completed' THEN pp.id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT pp.id), 0), 
        2
    ) as completion_rate
FROM process_step ps
LEFT JOIN process_step_completion psc ON ps.id = psc.step_id
LEFT JOIN process_progress pp ON psc.progress_id = pp.id
WHERE ps.process_id = :process_id
GROUP BY ps.id, ps.order_index, ps.title
ORDER BY ps.order_index;
```

#### Find abandoned processes (no activity in 24 hours)
```sql
SELECT 
    pp.id,
    pp.session_id,
    u.email,
    p.title as process_name,
    pp.completion_percentage,
    pp.last_activity_at,
    EXTRACT(EPOCH FROM (NOW() - pp.last_activity_at))/3600 as hours_inactive
FROM process_progress pp
JOIN process p ON pp.process_id = p.id
LEFT JOIN "user" u ON pp.user_id = u.id
WHERE pp.status = 'in_progress'
    AND pp.last_activity_at < NOW() - INTERVAL '24 hours'
ORDER BY pp.last_activity_at ASC;
```

### Materialized Views for Performance

#### Form Statistics Materialized View
```sql
CREATE MATERIALIZED VIEW form_statistics AS
SELECT 
    f.id as form_id,
    f.unique_slug,
    f.title,
    COUNT(DISTINCT fv.id) as total_views,
    COUNT(DISTINCT fs.id) FILTER (WHERE fs.status = 'submitted') as total_submissions,
    COUNT(DISTINCT fs.id) FILTER (WHERE fs.status = 'draft') as draft_count,
    ROUND(
        COUNT(DISTINCT fs.id) FILTER (WHERE fs.status = 'submitted') * 100.0 / 
        NULLIF(COUNT(DISTINCT fv.id), 0),
        2
    ) as conversion_rate,
    MAX(fs.submitted_at) as last_submission_at,
    MAX(fv.viewed_at) as last_view_at
FROM form f
LEFT JOIN form_view fv ON f.id = fv.form_id
LEFT JOIN form_submission fs ON f.id = fs.form_id
GROUP BY f.id, f.unique_slug, f.title;

-- Refresh periodically (e.g., every hour via cron/celery)
REFRESH MATERIALIZED VIEW CONCURRENTLY form_statistics;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX idx_form_stats_form_id ON form_statistics(form_id);
```

#### Process Statistics Materialized View
```sql
CREATE MATERIALIZED VIEW process_statistics AS
SELECT 
    p.id as process_id,
    p.unique_slug,
    p.title,
    COUNT(DISTINCT pv.id) as total_views,
    COUNT(DISTINCT pp.id) as total_started,
    COUNT(DISTINCT pp.id) FILTER (WHERE pp.status = 'completed') as total_completed,
    COUNT(DISTINCT pp.id) FILTER (WHERE pp.status = 'abandoned') as total_abandoned,
    ROUND(
        COUNT(DISTINCT pp.id) FILTER (WHERE pp.status = 'completed') * 100.0 / 
        NULLIF(COUNT(DISTINCT pp.id), 0),
        2
    ) as completion_rate,
    AVG(
        EXTRACT(EPOCH FROM (pp.completed_at - pp.started_at))
    ) FILTER (WHERE pp.status = 'completed') as avg_completion_time_seconds
FROM process p
LEFT JOIN process_view pv ON p.id = pv.process_id
LEFT JOIN process_progress pp ON p.id = pp.process_id
GROUP BY p.id, p.unique_slug, p.title;

CREATE UNIQUE INDEX idx_process_stats_process_id ON process_statistics(process_id);
```

---

## 14. Database Partitioning Strategy

### Time-based Partitioning for View Tables

#### Partition form_view by month
```sql
-- Convert to partitioned table
CREATE TABLE form_view_partitioned (
    LIKE form_view INCLUDING ALL
) PARTITION BY RANGE (viewed_at);

-- Create partitions for each month
CREATE TABLE form_view_2024_10 PARTITION OF form_view_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE form_view_2024_11 PARTITION OF form_view_partitioned
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

-- Create index on each partition
CREATE INDEX idx_form_view_2024_10_form ON form_view_2024_10(form_id);
CREATE INDEX idx_form_view_2024_11_form ON form_view_2024_11(form_id);

-- Automatic partition creation (using pg_partman or custom script)
```

#### Benefits of Partitioning
- **Query Performance**: Queries with date filters scan only relevant partitions
- **Maintenance**: Can drop old partitions instead of DELETE (much faster)
- **Archiving**: Easy to move old partitions to slower storage
- **Backup**: Can backup recent partitions more frequently

### When to Partition
- Tables with > 10 million rows
- Time-series data (views, submissions)
- Clear partition key (date/time)
- Queries frequently filter on partition key

---

## 15. Caching Strategy

### Redis Cache Keys Structure

```
# User data
user:{user_id}:profile
user:{user_id}:forms:list
user:{user_id}:processes:list
user:{user_id}:categories:list

# Form data
form:{slug}:definition
form:{slug}:fields
form:{slug}:submissions:count
form:{slug}:views:count
form:{slug}:stats

# Process data
process:{slug}:definition
process:{slug}:steps
process:{slug}:stats

# Session data
session:{session_id}:form_draft:{form_slug}
session:{session_id}:process_progress:{process_slug}

# Statistics (TTL: 5 minutes)
stats:forms:recent
stats:processes:recent
stats:dashboard:{user_id}

# Real-time data (pub/sub)
realtime:form:{slug}:submissions
realtime:process:{slug}:progress
```

### Cache Invalidation Rules

**Invalidate on**:
- Form update → `form:{slug}:*`
- New submission → `form:{slug}:submissions:count`, `form:{slug}:stats`
- Process update → `process:{slug}:*`
- Category change → `user:{user_id}:forms:list`, `user:{user_id}:processes:list`

### Cache TTL (Time To Live)

```python
CACHE_TTL = {
    'user_profile': 3600,           # 1 hour
    'form_definition': 1800,        # 30 minutes
    'form_list': 300,               # 5 minutes
    'form_stats': 300,              # 5 minutes
    'process_definition': 1800,     # 30 minutes
    'dashboard_stats': 300,         # 5 minutes
    'session_draft': 86400,         # 24 hours
}
```

---

## 16. Backup & Recovery Strategy

### Backup Schedule

**Full Backups**: Daily at 2 AM
```bash
pg_dump -h localhost -U postgres -Fc dynamic_forms > backup_full_$(date +%Y%m%d).dump
```

**Incremental Backups**: Every 6 hours (using WAL archiving)
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

**Point-in-Time Recovery**: Keep WAL files for 7 days

### Backup Retention
- **Daily backups**: Keep for 30 days
- **Weekly backups**: Keep for 3 months
- **Monthly backups**: Keep for 1 year
- **Yearly backups**: Keep indefinitely

### Critical Data Priority
1. **Highest**: `user`, `form_submission`, `submission_answer`
2. **High**: `form`, `process`, `process_progress`
3. **Medium**: `form_field`, `process_step`, `category`
4. **Low**: `form_view`, `process_view` (can be regenerated)

### Disaster Recovery Plan
1. Restore latest full backup
2. Apply WAL files up to failure point
3. Verify data integrity
4. Update DNS/load balancer to new instance
5. Monitor application logs

---

## 17. Monitoring & Alerts

### Key Metrics to Monitor

#### Database Health
- Connection pool usage
- Query execution time (slow query log)
- Table sizes and growth rate
- Index usage and efficiency
- Replication lag (if using replicas)

#### Application Metrics
- Submission success rate
- Average form completion time
- Process abandonment rate
- API response times
- Cache hit/miss ratio

### Alert Thresholds

```yaml
alerts:
  - metric: slow_queries
    threshold: > 1 second
    action: Log and notify team
    
  - metric: failed_submissions
    threshold: > 5% in 5 minutes
    action: Page on-call engineer
    
  - metric: database_connections
    threshold: > 80% of max
    action: Scale up or investigate leak
    
  - metric: disk_usage
    threshold: > 85%
    action: Urgent notification
    
  - metric: cache_miss_rate
    threshold: > 40%
    action: Review cache strategy
```

### Query Performance Monitoring

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION pg_stat_statements;

-- Find slowest queries
SELECT 
    query,
    calls,
    total_exec_time / 1000 as total_time_seconds,
    mean_exec_time / 1000 as mean_time_seconds,
    max_exec_time / 1000 as max_time_seconds
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## 18. Data Archival Strategy

### Archive Rules

#### form_view / process_view
- Archive records older than 12 months
- Move to separate `*_archive` table or cold storage
- Keep aggregated statistics

```sql
-- Create archive table
CREATE TABLE form_view_archive (
    LIKE form_view INCLUDING ALL
);

-- Move old data (run monthly)
WITH moved_rows AS (
    DELETE FROM form_view
    WHERE viewed_at < NOW() - INTERVAL '12 months'
    RETURNING *
)
INSERT INTO form_view_archive SELECT * FROM moved_rows;
```

#### form_submission (draft status)
- Delete drafts older than 30 days with no activity
```sql
DELETE FROM form_submission
WHERE status = 'draft'
    AND updated_at < NOW() - INTERVAL '30 days';
```

#### process_progress (abandoned)
- Mark as abandoned after 7 days of inactivity
- Archive after 90 days
```sql
-- Mark as abandoned
UPDATE process_progress
SET status = 'abandoned'
WHERE status = 'in_progress'
    AND last_activity_at < NOW() - INTERVAL '7 days';

-- Archive old abandoned processes
WITH moved_rows AS (
    DELETE FROM process_progress
    WHERE status = 'abandoned'
        AND last_activity_at < NOW() - INTERVAL '90 days'
    RETURNING *
)
INSERT INTO process_progress_archive SELECT * FROM moved_rows;
```

---

## 19. Testing Data

### Test Data Generation Scripts

```sql
-- Insert test users
INSERT INTO "user" (id, email, password, first_name, last_name, is_active, email_verified, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'test1@example.com', 'hashed_password', 'John', 'Doe', true, true, NOW(), NOW()),
    (gen_random_uuid(), 'test2@example.com', 'hashed_password', 'Jane', 'Smith', true, true, NOW(), NOW());

-- Insert test form
INSERT INTO form (id, user_id, title, description, unique_slug, visibility, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM "user" WHERE email = 'test1@example.com'),
    'Customer Feedback Survey',
    'Help us improve our services',
    'customer-feedback-2024',
    'public',
    true,
    NOW(),
    NOW()
);

-- Insert test fields
INSERT INTO form_field (id, form_id, field_type, label, is_required, order_index, created_at, updated_at)
VALUES 
    (gen_random_uuid(), (SELECT id FROM form WHERE unique_slug = 'customer-feedback-2024'), 'text', 'Full Name', true, 0, NOW(), NOW()),
    (gen_random_uuid(), (SELECT id FROM form WHERE unique_slug = 'customer-feedback-2024'), 'email', 'Email Address', true, 1, NOW(), NOW()),
    (gen_random_uuid(), (SELECT id FROM form WHERE unique_slug = 'customer-feedback-2024'), 'select', 'Satisfaction Level', true, 2, NOW(), NOW());

-- Insert select options
INSERT INTO field_option (id, field_id, label, value, order_index, created_at)
SELECT 
    gen_random_uuid(),
    ff.id,
    option_data.label,
    option_data.value,
    option_data.order_index,
    NOW()
FROM form_field ff
CROSS JOIN (
    VALUES 
        ('Very Satisfied', '5', 0),
        ('Satisfied', '4', 1),
        ('Neutral', '3', 2),
        ('Dissatisfied', '2', 3),
        ('Very Dissatisfied', '1', 4)
) AS option_data(label, value, order_index)
WHERE ff.field_type = 'select'
    AND ff.label = 'Satisfaction Level';
```

### Seed Data for Development

```python
# management/commands/seed_data.py
from django.core.management.base import BaseCommand
from apps.forms.models import Form, FormField, FieldOption
from apps.users.models import User

class Command(BaseCommand):
    help = 'Seed database with test data'
    
    def handle(self, *args, **options):
        # Create test users
        user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create test form
        form = Form.objects.create(
            user=user,
            title='Employee Onboarding',
            unique_slug='employee-onboarding-test',
            visibility='public'
        )
        
        # Add fields
        name_field = FormField.objects.create(
            form=form,
            field_type='text',
            label='Full Name',
            is_required=True,
            order_index=0
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
```

---

## 20. Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Slow form submission queries
**Symptoms**: High latency on POST /api/v1/public/forms/{slug}/submit/
**Diagnosis**:
```sql
-- Check for missing indexes on submission_answer
EXPLAIN ANALYZE 
SELECT * FROM submission_answer 
WHERE submission_id = 'some-uuid';
```
**Solution**: Ensure indexes exist on frequently queried columns

#### Issue: Duplicate slug generation
**Symptoms**: Unique constraint violation on form.unique_slug
**Diagnosis**: Check slug generation logic
**Solution**: 
```python
def generate_unique_slug(base_slug):
    slug = base_slug
    counter = 1
    while Form.objects.filter(unique_slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
```

#### Issue: Out of memory during large export
**Symptoms**: API timeout on /api/v1/forms/{slug}/submissions/export/
**Diagnosis**: Loading all submissions into memory
**Solution**: Use streaming response
```python
from django.http import StreamingHttpResponse

def export_submissions(request, slug):
    def generate():
        submissions = FormSubmission.objects.filter(
            form__unique_slug=slug
        ).iterator(chunk_size=1000)
        # Stream CSV rows
        for submission in submissions:
            yield format_as_csv_row(submission)
    
    return StreamingHttpResponse(
        generate(),
        content_type='text/csv'
    )
```

#### Issue: Deadlocks during concurrent updates
**Symptoms**: Database deadlock errors
**Diagnosis**: Multiple transactions updating same rows
**Solution**: Use row-level locking
```python
from django.db import transaction

with transaction.atomic():
    form = Form.objects.select_for_update().get(slug=slug)
    form.is_active = False
    form.save()
```

---

## 21. Schema Evolution Examples

### Adding a New Field Type

**Step 1**: Update ENUM (if using PostgreSQL ENUM)
```sql
ALTER TYPE field_type_enum ADD VALUE 'phone';
ALTER TYPE field_type_enum ADD VALUE 'url';
```

**Step 2**: Update Django model
```python
class FormField(models.Model):
    FIELD_TYPES = (
        # ... existing types
        ('phone', 'Phone Number'),
        ('url', 'URL'),
    )
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
```

**Step 3**: Create migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding Soft Delete

**Step 1**: Add deleted_at column
```sql
ALTER TABLE form ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE process ADD COLUMN deleted_at TIMESTAMP NULL;
```

**Step 2**: Update queries to filter out deleted records
```python
class FormQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

class Form(models.Model):
    objects = FormQuerySet.as_manager()
    
    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()
```

### Adding Multi-language Support

**Step 1**: Create translation tables
```sql
CREATE TABLE form_translation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES form(id) ON DELETE CASCADE,
    language_code VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(form_id, language_code)
);
```

**Step 2**: Update application logic to use translations

---

## 22. Compliance & Auditing

### Audit Log Table

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "user"(id),
    action VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE, VIEW
    entity_type VARCHAR(50) NOT NULL,  -- form, process, submission
    entity_id UUID NOT NULL,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);
```

### GDPR Compliance Queries

**Export user data**:
```sql
-- Export all user data for GDPR request
SELECT json_build_object(
    'profile', (SELECT row_to_json(u) FROM "user" u WHERE u.id = :user_id),
    'forms', (SELECT json_agg(f) FROM form f WHERE f.user_id = :user_id),
    'submissions', (SELECT json_agg(fs) FROM form_submission fs WHERE fs.user_id = :user_id)
);
```

**Anonymize user data**:
```sql
-- Anonymize user after account deletion request
UPDATE "user"
SET 
    email = CONCAT('deleted_', id, '@anonymized.local'),
    first_name = 'Deleted',
    last_name = 'User',
    phone_number = NULL,
    is_active = FALSE
WHERE id = :user_id;

-- Anonymize submissions
UPDATE form_submission
SET user_id = NULL,
    metadata = jsonb_set(metadata, '{ip_address}', '"0.0.0.0"')
WHERE user_id = :user_id;
```

---

This comprehensive database schema documentation covers all aspects of the dynamic forms system, from table structures to performance optimization, monitoring, and compliance. It serves as a complete reference for developers working on the project.